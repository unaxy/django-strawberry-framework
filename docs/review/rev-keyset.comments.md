# Review · Comments: `django_strawberry_framework/keyset.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=d6f1f0a4c4d291b03cf14e680ab3649aeda10851

## Trace

Read the whole live target (`django_strawberry_framework/keyset.py`, 709
lines: 33 docstrings, 8 comment entries per the `review_inspect.py`
census) and all three own test modules whole —
`tests/test_keyset.py` (975 lines: 12 docstrings, 55 comments),
`tests/test_keyset_connection.py` (503 lines: 5 docstrings, 30
comments), and `examples/fakeshop/test_query/test_keyset_api.py` (1168
lines: 41 docstrings, 45 comments; named for keyset and the live
acceptance surface the package docstrings point at). No sibling axis
records existed at dispatch (only `rev-keyset.md`, `Status:
reviewing`); required reading was AGENTS.md, START.md, REVIEW.md,
worker-1.md, the plan, and `rev-keyset.md`. The target and all three
test modules are byte-identical to ITEM_BASELINE (`git diff
ITEM_BASELINE -- <the four paths>` is empty); the dirt versus HEAD is
pre-existing concurrent work captured in the baseline, and every grade
below is against the live text at the fingerprints in this section.

Orientation: `review_inspect.py` overview + stripped source under
`docs/review/temp-tests/keyset/comments/inspect/` plus `keyset.json`,
`test_keyset.json`, `test_keyset_connection.json`,
`test_keyset_api.json`. `build_tree_md.py --list-docstrings` passes on
all four graded files (0 breaking each).
`check_citations.py --paths <file> --substrings --json` reports 3
citations, 0 violations in the target
(`plans.py::order_entry_name_and_direction`,
`types/base.py::_validate_cursor_field`,
`optimizer/lateral_fetch.py::_keyset_seek_quals_match`, all resolving)
and 1 citation, 0 violations in `tests/test_keyset.py`
(`keyset.py::to_base64`, resolving to the module's re-exported import);
the other two test modules carry 0 citations. Provenance sweep
(REVIEW.md pattern via `grep -E`, since `rg` is not installed) on the
four graded files hits only `round-trip`/`round-trips` (codec
vocabulary), one `motivating fix for offset-cursor drift` (domain
description, not change provenance), and the temporal clauses
discharged in Findings/Rejected. No `we`/`you`/`I`, no `Tests
that`/`Ensures`, no `.py:NN`, no public symbol without a docstring in
any of the four files.

Contract trace, each claim checked against its body and one real
caller: the `keyset_contract_error` five-sites/two-modules census
(keyset.py:511 + connection.py:946,953,959,1073); the one-codec census
(mint sites connection.py:557,1157 and decode sites
connection.py:1083,1086 + nested_planner.py:903,911 — every production
mint/decode flows through this module); the offset vice-versa
(upstream `SliceMetadata.from_arguments` raises `TypeError` on a
foreign prefix, strawberry 0.324.0 `relay/utils.py`); the
permission-aware pipeline order (`_resolve_keyset_connection` step 2:
queryset already visibility-scoped); the `CursorColumn.value_source`
annotation-alias construction (`_keyset_order_state` related-path
branch); the nullable-rejection shared stem; the
`split_order_ref`/`validate_cursor_field_references`/
`declared_cursor_state_for_definition` caller censuses (single syntax
owner, declaration + finalization callers, definition-keyed callers in
connection.py:1471 and nested_planner.py:1156 via
`resolve_relation_target`); the verifier's transitive sharing of
`keyset_seek_greater` via `seek.plan()`; the
`@lru_cache(maxsize=4)`-to-`@cache` history behind "three fallbacks"
(commit 48f9f65d); upstream's bare OR-chain without a leading bound
(`build_tuple_compare`) and `orderedcursor` prefix
(strawberry-graphql-django `relay/cursor_connection.py`); SQLite/PG
NULL ordering; the BACKLOG `stable_cursor_field` entry and the KANBAN
card owning its tense; 40 other-module prose units extracted to
`other-prose.txt`, every genuine one graded in
Findings/Rejected/Routed. No keyset symbol is exported through an
`__all__` or documented in `docs/README.md`/`docs/GLOSSARY.md` (only
the `Meta.cursor_field` key is), so every prose finding here caps at
Medium.

Cells: no workspace run was needed — every instrument above is static
(source reads, AST census, citation resolution, upstream comparison).
Sharded and pg are inapplicable by construction to this Comments pass
(no database-reaching probe; all Proofs are static `grep -c` plus
grade judgments; Worker-2's prose edits owe `--code-digest` identity,
not cell runs). Cells unverified: none.

Fingerprints (`git hash-object` 8-char; upstream sha256 12-char):
target `279ad7b0`; `tests/test_keyset.py` `e5655de7`;
`tests/test_keyset_connection.py` `70db0483`;
`test_keyset_api.py` `88a432b0`; `connection.py` `1fca6266`;
`utils/connections.py` `efcf749a`; `optimizer/nested_planner.py`
`d32d1b7b`; `optimizer/lateral_fetch.py` `db1ea315`;
`optimizer/plans.py` `33140a76`; `optimizer/nested_fetch.py`
`1678609e`; `optimizer/single_parent_fetch.py` `e995270a`;
`types/base.py` `dc67f084`; `types/definition.py` `1c59a3fe`;
`types/finalizer.py` `b9d8acb2`; `exceptions.py` `93401220`;
`extensions/error_policy.py` `a1defd39`;
`tests/test_relay_connection.py` `fe2b2d24`;
`tests/types/test_base.py` `bb56c89b`;
`tests/optimizer/test_lateral_fetch.py` `c5aab598`;
`tests/optimizer/test_plans.py` `1e09d6d8`;
`tests/optimizer/test_single_parent_fetch.py` `1f48c6ec`;
`tests/test_connection.py` `8e08b23f`;
`tests/test_lateral_pg_parity.py` `da15d712`;
`tests/utils/test_connections.py` `65d54027`;
`tests/test_bench_common.py` `a8475340`;
`tests/test_build_tree_md.py` `71bf3ea7`;
`test_library_api.py` `2cd1b6dd`;
`test_connection_pagination_api.py` `d6a4f720`;
`test_products_api.py` `fe78cf9d`;
`test_single_parent_fastpath_api.py` `492fac73`; `BACKLOG.md`
`9e00b605`; `KANBAN.md` `39bb608e`; `docs/GLOSSARY.md` `3413edc3`;
`docs/README.md` `30978c34`; upstream `strawberry/relay/utils.py`
`67554e938db4` (0.324.0); upstream
`strawberry_django/relay/cursor_connection.py` `8ed3ce557e0d`. A
finding's Freshness lists only files beyond these: none.

## Findings

### High

None.

### Medium

- Observation: `KeysetSeek`'s docstring says the carrier exists "so
  every consumer renders the SAME predicate through ``q()``". Two of
  the four consumers never call `q()`: the lateral SQL renderer binds
  `seek.plan(values)` into `keyset_seek_sql`
  (`optimizer/lateral_fetch.py::_keyset_seek_sql`), and the
  fetch-time structural verifier reads `seek.plan()`'s direction bits
  (`_keyset_seek_quals_match`). The SAME-predicate half is true (one
  shared plan); the "through ``q()``" half is false for the SQL
  dialect.
- Evidence: the consumer census above (`q()` consumers:
  `optimizer/plans.py:1086,1093`, `connection.py:1084,1087`;
  `plan()` consumers: `lateral_fetch.py:448,780`).
- Impact: a reader extending the seek believes `q()` is the single
  render path and misses the SQL twin the plan exists to serve.
- Severity: Medium (stale docstring on an internal symbol).
- Recommendation: name both render paths; see text-after.
- Must not change: n/a.
- Proof: `grep -c "SAME predicate through"
  django_strawberry_framework/keyset.py` prints `0` (1 today); the
  rewritten docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/keyset.py::KeysetSeek`.
- Grade: stale (overclaimed render path).
- Text-before:
  `The value the plan-time walker threads to the fetch strategies (``NestedConnectionRequest.keyset_seek`` -> ``apply_window_pagination`` / ``build_lateral_sql``) and the resolve-time slicer builds for the root / per-parent paths - one carrier so every consumer renders the SAME predicate through ``q()``.`
- Text-after:
  `The value the plan-time walker threads to the fetch strategies (``NestedConnectionRequest.keyset_seek`` -> ``apply_window_pagination`` / ``build_lateral_sql``) and the resolve-time slicer builds for the root / per-parent paths - one carrier so every consumer renders the SAME predicate: ORM consumers through ``q()``, the lateral SQL renderer through ``plan()`` + ``keyset_seek_sql``.`

- Observation: `encode_keyset_cursor`'s docstring says the cursor is
  "base64-wrapped under ``KEYSET_CURSOR_PREFIX`` so bounds
  derivation can discriminate the cursor vocabulary without
  decrypting the payload first". No bounds derivation does that:
  `derive_keyset_window_bounds` is pure slice arithmetic that ignores
  `after` entirely (`noqa: ARG001 - signature parity ... the seek,
  not the bounds, consumes it`), the keyset/offset fork is chosen by
  the declared `keyset_state` rather than by inspecting any cursor,
  and the only prefix-before-decrypt check in the tree is decode
  itself (`from_base64` prefix comparison ahead of
  `_decrypt_cursor_payload`). The wrap's true reasons are the two
  decoders' prefix rejections, not bounds derivation.
- Evidence: `utils/connections.py::derive_keyset_window_bounds` body;
  the `KEYSET_CURSOR_PREFIX` census (no reader outside keyset.py);
  `decode_keyset_cursor`'s check-then-decrypt order.
- Impact: wrong stated reason for the prefix wrap (worse than none:
  a reader looking for the discriminating bounds derivation finds a
  function that explicitly ignores the cursor).
- Severity: Medium (stale comment on internal code).
- Recommendation: state the decoders' prefix rejections; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c "bounds derivation can discriminate"
  django_strawberry_framework/keyset.py` prints `0` (1 today); the
  rewritten sentence earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/keyset.py::encode_keyset_cursor`.
- Grade: stale (non-existent consumer as the stated reason).
- Text-before:
  `(module docstring), then base64-wrapped under ``KEYSET_CURSOR_PREFIX`` so bounds derivation can discriminate the cursor vocabulary without decrypting the payload first.`
- Text-after:
  `(module docstring), then base64-wrapped under ``KEYSET_CURSOR_PREFIX`` so each vocabulary's decoder rejects a foreign cursor on its prefix: ``decode_keyset_cursor`` refuses a non-keyset prefix before attempting authenticated-decryption, and the offset path's ``SliceMetadata`` refuses a keyset prefix the same way.`

- Observation: `KeysetSeekPlan`'s docstring says "The canonical
  portable shape both dialects render is the redundant leading
  inclusive bound on column 0 plus the OR-expansion". The SQL
  dialect renders that shape only for mixed directions: uniform
  directions emit the bare native row-value comparison
  (`(a, b) > (%s, %s)`, single column `col > %s`) with no leading
  bound. The docstring's own next sentences carve out the uniform
  exception, so the opening universal contradicts its own paragraph.
- Evidence: `keyset_seek_sql`'s `if plan.uniform` branch versus the
  always-bound-plus-expansion `keyset_seek_q`.
- Impact: a reader is told both dialects render one shape, then told
  one of them renders another; the universal misstates the SQL
  renderer's output on every uniform page.
- Severity: Medium (stale docstring on an internal symbol).
- Recommendation: scope the canonical shape per dialect; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c "both dialects render is the"
  django_strawberry_framework/keyset.py` prints `0` (1 today); the
  rewritten paragraph earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/keyset.py::KeysetSeekPlan`.
- Grade: stale (false universal, contradicted by its own paragraph).
- Text-before:
  `The canonical portable shape both dialects render is the redundant leading inclusive bound on column 0 plus the OR-expansion of strict-comparison arms (one arm per column).`
- Text-after:
  `The canonical portable shape is the redundant leading inclusive bound on column 0 plus the OR-expansion of strict-comparison arms (one arm per column); the ORM dialect always renders it, while the SQL dialect renders it only for mixed directions (uniform directions emit the native row-value comparison below).`

- Observation: the module docstring's motivating example declares
  `cursor_field = ("-created_at", "id")` and then illustrates the
  seek as "a tuple-comparison seek (``WHERE (created_at, id) > (%s,
  %s)``)". That order is mixed-direction, so it never emits the
  row-value form — mixed directions always render the
  redundant-leading-bound OR-expansion (uniform `greater` bits are
  unreachable under `("-created_at", "id")` in either flip), and a
  single-operator row-value comparison cannot express mixed
  directions at all. The parenthetical shows SQL the example order
  can never produce.
- Evidence: `keyset_seek_sql`'s `uniform` gate;
  `build_keyset_seek_plan([True, False], ...)` is mixed in both
  flips; `keyset_seek_q` always renders bound-plus-expansion.
- Impact: the contract's headline illustration teaches the wrong SQL
  shape for its own example order.
- Severity: Medium (stale module prose on the motivating example).
- Recommendation: show the expansion the example emits and scope the
  row-value form to uniform directions; see text-after.
- Must not change: n/a.
- Proof: `grep -c "WHERE (created_at, id)"
  django_strawberry_framework/keyset.py` prints `0` (1 today); the
  rewritten sentence earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/keyset.py` module docstring.
- Grade: stale (illustration unreachable under its own example).
- Text-before:
  `cursor carries the row's ordering-column values (plus the unique terminal tiebreak), so ``after:`` becomes a tuple-comparison seek (``WHERE (created_at, id) > (%s, %s)``) instead of a row-number offset`
- Text-after:
  `cursor carries the row's ordering-column values (plus the unique terminal tiebreak), so ``after:`` becomes a tuple-comparison seek (``WHERE`` on the ordering columns - a redundant leading bound plus an OR-expansion across the tuple, collapsing to ``(created_at, id) > (%s, %s)`` only when every column seeks the same direction) instead of a row-number offset`

### Low

- Observation: `keyset_contract_error`'s docstring justifies the
  helper in the past tense: "The stem was re-typed at five sites
  across two modules, so a reword of the shared half was a five-site
  edit with nothing checking it". The five-site census still holds
  (verified in Trace), but "was re-typed / was a five-site edit"
  narrates the pre-helper state instead of the live sharing the
  helper owns.
- Evidence: the five call sites, all still sharing this stem.
- Impact: bounded; history where the ownership invariant belongs.
- Severity: Low.
- Recommendation: present-tense sharing; see text-after.
- Must not change: n/a.
- Proof: `grep -c "was re-typed at five"
  django_strawberry_framework/keyset.py` prints `0` (1 today); the
  rewritten sentence earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/keyset.py::keyset_contract_error`.
- Grade: process provenance (past-tense change narration).
- Text-before:
  `The stem was re-typed at five sites across two modules, so a reword of the shared half was a five-site edit with nothing checking it;`
- Text-after:
  `Five sites across two modules share this stem: without this helper a reword of the shared half would be a five-site edit with nothing checking it;`

- Observation:
  `test_nested_keyset_unselected_cursor_column_is_not_lazy_loaded_per_edge`'s
  docstring says "The already-implemented
  ``_extend_only_projection`` (which killed the strawberry-django
  ``annotate_ordering_fields`` port) folds the cursor columns back
  into the projection". "already-implemented" is temporal and the
  parenthetical narrates a killed port (upstream
  `annotate_ordering_fields` exists; no port of it exists in this
  tree — the only mention is this sentence). The live content is
  the folding behavior, which is true.
- Evidence: the `annotate_ordering_fields` census (one hit: this
  sentence) versus upstream
  `strawberry_django/relay/cursor_connection.py`.
- Impact: bounded; killed-port history where the projection rule
  belongs.
- Severity: Low.
- Recommendation: present-tense behavior, drop the port history;
  see text-after.
- Must not change: n/a.
- Proof: `grep -c "killed the strawberry-django"
  examples/fakeshop/test_query/test_keyset_api.py` prints `0` (1
  today); the rewritten paragraph earns grade true.
- Freshness: none beyond Trace.
- Symbol:
  `examples/fakeshop/test_query/test_keyset_api.py::test_nested_keyset_unselected_cursor_column_is_not_lazy_loaded_per_edge`.
- Grade: process provenance (temporal + killed-history aside).
- Text-before:
  `value cursor would lazy-load ``number`` once PER edge (an N+1). The already-implemented ``_extend_only_projection`` (which killed the strawberry-django ``annotate_ordering_fields`` port) folds the cursor columns back into the projection, so the whole nested window stays a single batched prefetch with zero per-edge lazy loads. Pinned here as live behavior.` (source wraps `already-` across lines 708-709).
- Text-after:
  `value cursor would lazy-load ``number`` once PER edge (an N+1). ``_extend_only_projection`` folds the cursor columns back into the projection, so the whole nested window stays a single batched prefetch with zero per-edge lazy loads. Pinned here as live behavior.`

- Observation:
  `test_nested_keyset_marker_distinguishes_pre_cursor_only_parents`
  carries a reasoning-trace comment above code that does none of
  what it walks through: "Cursor past astro#2 (deep page): botany's
  numbers 3..1 all precede it? No - ... Take the cursor at astro#1
  ... Botany keeps a page; give botany a cursor past ALL its rows
  instead by cursoring at the global tail." The test takes neither
  the astro#2 nor the astro#1 cursor; it mints the global tail
  cursor (bot#1). The "No -" self-correction is deliberation
  residue; only the last sentence describes the code.
- Evidence: read verbatim (lines 652-658) against the `tail_cursor`
  body below it.
- Impact: bounded; rejected-options walk where the tail-cursor
  account belongs.
- Severity: Low.
- Recommendation: keep only the tail-cursor account; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c "all precede it? No"
  examples/fakeshop/test_query/test_keyset_api.py` prints `0` (1
  today); the rewritten comment earns grade true.
- Freshness: none beyond Trace.
- Symbol:
  `examples/fakeshop/test_query/test_keyset_api.py::test_nested_keyset_marker_distinguishes_pre_cursor_only_parents`.
- Grade: process provenance (reasoning trace with dead options).
- Text-before:
  `Cursor past astro#2 (deep page): botany's numbers 3..1 all precede it? No - under (-number, id), "past the cursor" means SMALLER numbers. Take the cursor at astro#1 (the last astronomy row): the only rows past it are bot#1 (number 1, larger pk). Botany keeps a page; give botany a cursor past ALL its rows instead by cursoring at the global tail.`
- Text-after:
  `Cursor at the global tail (bot#1, the final row): every astronomy row precedes it, so the page is empty while the abs-first marker row carries the true pre-seek count.`

- Observation:
  `tests/types/test_base.py::test_meta_cursor_field_in_allowed_meta_keys`'s
  docstring reads "``Meta.cursor_field`` is a net-new ALLOWED key
  (the ``stable_cursor_field`` card). Net-new ALLOWED, NOT a
  DEFERRED_META_KEYS promotion - the feature ships in the same
  change that adds the key (the ``Meta.connection`` precedent)."
  The assertions are true, but "(the ``stable_cursor_field``
  card)" is card attribution (board residue) and "ships in the
  same change" narrates how the key came to be. This module rides
  with the `types/base.py` item, so this Low will almost surely
  defer here and stand as the record for that pass.
- Evidence: read verbatim (lines 2357-2361); assertions verified
  true.
- Impact: bounded; card/change provenance on a true contract pin.
- Severity: Low.
- Recommendation: state the usable-at-creation contract without
  the card or the change; see text-after.
- Must not change: n/a.
- Proof: `grep -c "stable_cursor_field.*card"
  tests/types/test_base.py` prints `0` (1 today); the rewritten
  docstring earns grade true.
- Freshness: none beyond Trace.
- Symbol:
  `tests/types/test_base.py::test_meta_cursor_field_in_allowed_meta_keys`.
- Grade: process provenance (card attribution + change narration).
- Text-before:
  ```text
  ``Meta.cursor_field`` is a net-new ALLOWED key (the ``stable_cursor_field`` card).

  Net-new ALLOWED, NOT a DEFERRED_META_KEYS promotion - the feature ships in the same change that adds the key (the ``Meta.connection`` precedent).
  ```
- Text-after:
  ```text
  ``Meta.cursor_field`` is a direct ALLOWED key, never a DEFERRED_META_KEYS promotion.

  Usable at class creation (the ``Meta.connection`` precedent); ``DEFERRED_META_KEYS`` carries no cursor entry.
  ```

## Rejected

- R1 — Non-imperative first lines. `KeysetSeek.q` (`The ...`),
  `KeysetSeek.plan` (`The ...`), `order_fingerprint` (`The ...`),
  `validate_cursor_field_columns` (`Finalization-time ...`),
  `_invalid_cursor_error` (`The ...`), `keyset_seek_q` (`The ...`)
  join the file's descriptive convention for concept-carrying
  helpers. Precedent (connection.py Comments R1, exceptions.py
  Comments R1) accepts descriptive mood and rewrites nothing until
  a package-wide mood gate lands; rewriting six sites here would
  make this file inconsistent with that standing rejection.
  Trigger: a package-wide mood gate lands.
- R2 — "BACKLOG contract" pointers (module docstring "The BACKLOG
  ``stable_cursor_field`` contract", `validate_cursor_field_columns`
  "the BACKLOG contract requires the tiebreak DECLARED"). The
  established package-wide naming convention for this contract (6
  sites across keyset.py, types/base.py, types/definition.py,
  nested_planner.py), and the backlog entry's future-tense question
  is already owned by its KANBAN card, which explicitly leaves the
  spec-or-glossary decision open. Repointing here would prejudge
  it. Trigger: the maintainer answers that card.
- R3 — `keyset_seek_greater` "Shared by ...
  plus the lateral fetch-time structural verifier". The verifier
  never re-derives directions: it reads `plan.greater` /
  `plan.lead_greater` off `seek.plan()`, which renders through
  `build_keyset_seek_plan` → `keyset_seek_greater`. Shared rule,
  transitively shared code; the "can never seek opposite sides"
  guarantee holds. No trigger beyond a verifier rewrite that
  re-derives directions.
- R4 — "mutually rejecting" vocabularies. Verified both
  directions raise rather than confuse: keyset decode rejects a
  foreign prefix before decrypting, and an offset connection
  routes a keyset cursor into upstream `SliceMetadata`, which
  raises `TypeError` on prefix mismatch (strawberry 0.324.0).
  Trigger: an upstream or offset-path change that stops checking
  prefixes.
- R5 — `_cursor_aessiv` "more than three fallbacks". Encodes the
  pre-change `@lru_cache(maxsize=4)` capacity (active key + three
  fallbacks) that commit 48f9f65d's `@cache` removed; the number
  is the old eviction threshold, not an arbitrary limit. True.
  Trigger: none (historical capacity, fixed).
- R6 — `keyset_seek_q` "(the use-the-index-luke lesson upstream's
  comparator omits)". Verified against
  strawberry-graphql-django's `build_tuple_compare`, which folds
  `cmp | (eq & current)` with no redundant leading bound. The
  unnamed "upstream" is the package's documented cribbing
  direction (START.md). True. Trigger: upstream adds a leading
  bound.
- R7 — `test_library_api.py` "(keyset cursors are BACKLOG item 39
  sub-feature 3)". True identity: the KANBAN card uses exactly
  this "shipped as item 39 sub-feature 3" language. (The
  "(Revision 2 P1)" sharing that first line is review residue but
  is not about keyset symbols, so it is out of this mandate;
  noted in Handoff, not graded.) Trigger: the board renames the
  item.
- R8 — `types/base.py` ALLOWED_KEYS comment ("net-new ALLOWED
  keys ... ships in the same card ... never
  reserved-but-nonfunctional"). Considered as a route candidate
  and rejected: "net-new" is glossed in place as the
  added-with-feature category (versus DEFERRED promotions), a
  historical fact per key that does not rot, and "were never
  reserved-but-nonfunctional" is the load-bearing explanation for
  `DEFERRED_META_KEYS` staying unchanged. True; the types/base
  pass may still reword it, but nothing here is false.

## Routed leads

- Routed: `django_strawberry_framework/types/definition.py`
  `cursor_field` comment — `it orders by these columns, mints
  value-encoded SIGNED cursors (``keyset.py``), and rejects offset
  cursors`. Cursors are AES-SIV authenticated-encrypted, and the
  keyset module docstring explicitly rejects the merely-signed
  shape ("A merely signed/base64 cursor ... would disclose column
  data"); "signed" misstates the confidentiality contract.
  Born-stale in 51421e54 (the same commit that introduced
  `authenticated-encrypted`). Owner: the `types/definition.py`
  item, which is out of scope this run — Worker-0 to carry into
  `## Decisions`.

Handoff: I graded every docstring and comment in the target (33
docstrings, 8 comment entries) and all three own test modules
whole (58 docstrings, 130 comment lines), plus 40 other-module
prose units about keyset symbols (`other-prose.txt`): 4 Mediums
(F1 `q()` overclaim, F2 phantom bounds-derivation consumer, F3
false both-dialects universal, F4 unreachable tuple-comparison
illustration) and 4 Lows (L1 past-tense stem sharing, L2 killed
port, L3 reasoning trace, L4 card/change provenance in
`tests/types/test_base.py`, which will likely defer here), 8
rejections with triggers, and 1 new Routed lead
(`types/definition.py` "signed cursors" → `## Decisions`, that
item being out of scope). Everything else grades true,
including all 4 path::Symbol citations (0 violations), the
vice-versa rejection pair, the one-codec census, the five-site
stem census, the AES-SIV cache rationale, and the upstream
comparator/orderedcursor claims. Corroborated standing routes,
not duplicated: `utils/connections.py::split_window_rows`
"future keyset-cursor backend" (verbatim live; the page-relative
backend resolves through `_resolve_from_window` + `split_window_rows`
at connection.py:454 today) and nested_planner's "legacy
shared-to_attr" (line 1360 as routed, plus an adjacent twin at
line 1165, "`None` keeps the legacy shared `to_attr`", for the
same fix). Observed but out of mandate (not about keyset
symbols, no owning open item): "(Revision 2 P1)" in
`test_library_api.py::test_stale_after_cursor_no_error`. No
workspace runs (all instruments static); scratch under
`docs/review/temp-tests/keyset/comments/` (`inspect/`,
`keyset.json`, `test_keyset.json`,
`test_keyset_connection.json`, `test_keyset_api.json`,
`citations.json`, `other-prose.txt`); live text equals
ITEM_BASELINE on all four graded files. On verify: each Proof
is a static `grep -c` printing 0 with the rewritten text
grading true; every prose-only file owes `--code-digest`
identity.

## Verification (Comments)

Step 1 (the tree still carries the change):
`git diff d6f1f0a4c4d291b03cf14e680ab3649aeda10851 --
django_strawberry_framework/keyset.py` sha256
`96670bf91b70e3f7e77d91ece2413b74f20c4ffaa463e8c56b34cb67b0b80043`
equals `docs/review/temp-tests/keyset/diff/pass-1.diff` sha256
`96670bf91b70e3f7e77d91ece2413b74f20c4ffaa463e8c56b34cb67b0b80043`
(`diff` reports `HASH_EQUAL`) — pass, graded.

Proof runs (verbatim, shared tree — all static `grep -c`):

- M1 `grep -c "SAME predicate through"
  django_strawberry_framework/keyset.py` → `0` (was 1). Pass.
- M2 `grep -c "bounds derivation can discriminate"
  django_strawberry_framework/keyset.py` → `0` (was 1). Pass.
- M3 `grep -c "both dialects render is the"
  django_strawberry_framework/keyset.py` → `0` (was 1). Pass.
- M4 `grep -c "WHERE (created_at, id)"
  django_strawberry_framework/keyset.py` → `0` (was 1). Pass.
- L1 `grep -c "was re-typed at five"
  django_strawberry_framework/keyset.py` → `0` (was 1). Pass.
- L2 (deferred) `grep -c "killed the strawberry-django"
  examples/fakeshop/test_query/test_keyset_api.py` → `1` — still
  present, confirmed and stated so. Pass.
- L3 (deferred) `grep -c "all precede it? No"
  examples/fakeshop/test_query/test_keyset_api.py` → `1` — still
  present, confirmed and stated so. Pass.
- L4 (deferred) `grep -c "stable_cursor_field.*card"
  tests/types/test_base.py` → `1` — still present, confirmed and
  stated so. Pass.

No `## Cross-axis (for Comments)` section exists in either sibling
record (confirmed by `grep`: the only `Cross-axis` hits note their
absence), so no further Proof is owed. 8/8 hold.

Grades (each landed docstring whole, against body + one real caller;
each matches the record's text-after modulo 99-col rewrapping, no
rewording):

- M1 `KeysetSeek` docstring — **true**. The both-render-paths
  sentence is accurate: ORM consumers render through `q()`
  (`plans.py`, `connection.py` slicer), and the lateral renderer
  binds `seek.plan(values)` into `keyset_seek_sql`
  (`lateral_fetch.py:448,450`). Rest of the docstring (threading,
  flip semantics) unchanged and still accurate.
- M2 `encode_keyset_cursor` docstring — **true**. Decode refuses a
  foreign prefix before decrypting (`from_base64`, prefix compare,
  then `_decrypt_cursor_payload`), and upstream
  `SliceMetadata.from_arguments` raises `TypeError` on prefix
  mismatch (strawberry 0.324.0 `relay/utils.py`, re-read). First
  line stays imperative; payload-shape and NULL paragraphs
  unchanged and accurate.
- M3 `KeysetSeekPlan` docstring — **true**. `keyset_seek_sql`'s
  `uniform` branch emits the native row-value comparison while the
  mixed branch emits the bound-plus-expansion the ORM always
  renders (body re-read); the per-dialect scoping matches, and the
  following `uniform` sentence stays consistent with it.
- M4 module docstring sentence — **true**. The mixed-direction
  example order now illustrates the expansion it actually emits,
  with the row-value form correctly scoped to uniform directions
  ("only when every column seeks the same direction").
- L1 `keyset_contract_error` docstring — **true**. Present-tense
  sharing; the five-site/two-module census re-derived intact (1
  in-target `:516` + 4 in `connection.py`
  `:946,:953,:959,:1073`). First line stays imperative.

Ride-rule judgment: correctly applied. L1 rides `keyset.py`, which
the four Mediums change — implemented. L2/L3 (`test_keyset_api.py`)
and L4 (`tests/types/test_base.py`) sit in files no higher finding
in this item touches — deferred, and both files are byte-identical
to ITEM_BASELINE (empty `git diff <ITEM_BASELINE>`, fingerprints
`88a432b0`, `bb56c89b` reproduced). No other axis changed code
(both sibling records no-findings), so no cross-axis file-sharing
argues otherwise.

Instruments (shared tree, target file):

- `build_tree_md.py --list-docstrings
  django_strawberry_framework/keyset.py` → `1 modules, 0 breaking
  the first-line rule`. Pass.
- `check_citations.py --paths
  django_strawberry_framework/keyset.py --substrings --json` → 3
  citations, 0 violations (same three resolving cites as review).
  Pass.
- `review_inspect.py --code-digest
  d6f1f0a4c4d291b03cf14e680ab3649aeda10851:django_strawberry_framework/keyset.py
  django_strawberry_framework/keyset.py` → exit 0, both
  `sha256:bb01f2e8fe76bba0d0884be6ec485830283e6853df51348e7507551e6549ee05`,
  matching Worker-2's reported digest. Direct baseline comparison:
  no other axis changed code, so no reconstruction is owed. Pass.
- Diff hygiene: every `+` line swept for the provenance vocabulary,
  line-number citations, and `we`/`you` — clean. Module first line
  byte-identical baseline vs live, so no TREE.md render is owed.

Sibling verifiers' sections: Performance verify 1 and Mechanics
verify 1 both report `verified` with no new finding and no gap
routed to Comments (Mechanics explicitly notes the deferred Lows
move no mechanics surface). Nothing routed here; nothing to
absorb.

Attacks on the landed prose (all pass, no new finding):

1. M1's "every consumer": the fetch-time structural verifier also
  consumes `seek.plan()` (`lateral_fetch.py:780`) but is not named.
  It verifies the Q-tree shape against the shared plan rather than
  rendering a predicate, so the sentence's render-path enumeration
  (ORM via `q()`, lateral SQL via `plan()` + `keyset_seek_sql`)
  is complete and the SAME-predicate guarantee it conveys is, if
  anything, strengthened by the verifier's existence.
2. M2's "before attempting authenticated-decryption": decode order
  re-read — `from_base64`, prefix compare, then decrypt. A
  well-formed foreign-prefix cursor is refused before any decrypt
  attempt. Holds.
3. M3's "the native row-value comparison below": the single-column
  uniform case emits the bare `col > %s`, the 1-tuple degenerate
  of the row-value form, and "below" delegates to
  `keyset_seek_sql`'s docstring + body which document the shape
  including that arm. Consistent with the pre-existing `uniform`
  sentence beside it. Holds.
4. M4's parenthetical: the example order is mixed, so the sentence
  now teaches the expansion first and scopes the row-value form
  with "only when" — no reading attributes the row-value form to
  the example itself. Holds.
5. L1's "would be a five-site edit": hypothetical present, correct
  for the live sharing (census above). Holds.

Disputes: none — Implementation records zero `disputed` findings;
nothing to judge.

Cells: sharded and pg inapplicable by construction (static Proofs
plus `--code-digest` identity on a prose-only diff; the target
opens no database). Cells unverified: none.

Verdict: all 5 implemented Proofs print 0 with landed docstrings
grading true whole; all 3 deferred Proofs still print 1 with the
ride rule correctly applied; code identity holds; hygiene clean.
`Status: verified`.

Scratch: `docs/review/temp-tests/keyset/verify-comments-1/`
(created; holds no probe — none owed for static proofs). No
workspace runs, no run ids. Fingerprints at verify time: target
`d1a6dec2` (was `279ad7b0` at ITEM_BASELINE, matches Worker-2's),
`test_keyset_api.py` `88a432b0`, `tests/types/test_base.py`
`bb56c89b` (both equal ITEM_BASELINE), this record `d2e942ac`
(pre-section), `rev-keyset.performance.md` `9f24072f`,
`rev-keyset.mechanics.md` `193527d2` (both moved since Worker-2's
read by their verifiers' appended sections, as expected),
`rev-keyset.md` `bcbaf44c`.

Handoff: Comments verify 1 is a clean pass — Step 1 hash-equal,
8/8 Proofs hold (5 implemented at 0, 3 deferred still at 1),
all five landed docstrings grade true whole against re-read
bodies and callers, the three deferrals satisfy the ride rule
with both deferred files byte-identical to the baseline,
`--code-digest` identity reproduced, `--list-docstrings` and
`check_citations` green, no provenance/line-refs/we, module
first line unchanged, five prose attacks passing, no disputes,
no gaps from or to sibling axes. Nothing is left open for a
further Comments pass; a re-pass would only be owed if a later
pass touched prose.
