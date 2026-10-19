# DRY review: `defects-rest-testing`

Status: verified
Run: 0.0.15 2026-10-10-15

## System trace

Batch: 6 rows (table rows 18 + 42 + 43 + 48 + 49 + 55) across 4 package files
(`rest_framework/{resolvers,serializer_converter}.py`, `testing/{client,relay}.py`;
3 edited, `testing/relay.py` untouched). Read all 4 source `## Defects` entries
in full + both folder adjudications (rest_framework: 4 member defects persist,
D3 closed, D4 falsified; testing: both D1s persist, D2 closed) before touching
anything; re-checked each against current worktree bytes. Attribution: full
vs-HEAD diff read hunk by hunk -- client 12 (3 f39 ledger + 9 hunt), relay 3
(all hunt), converter 36 (2 f35 ledger + 34 hunt), resolvers ~85 (all hunt:
truth migration, hostile guards, except-narrowing); D3/D4 hardening confirmed
hunt-owned, untouched. Every touch line verified HEAD-identical first
(unified-0 zero overlap with hunt ranges; one same-statement adjacency at
resolvers.py:1933/1936 disclosed below). Table summaries for rows 42 ("spec-046")
and 18 ("RelayDriver surface") name phantom phrases (0 hits); the verified
artifact entries governed and all 6 defects were live. Rows 49 + 55 reproduced
pre-fix in filed shapes and proven fail-first. relay.py needs no edit (row 18
lives in `types/base.py`). Developed in slot-2, gated, ported byte-identical
(`cmp` clean all 3).

## Verification

### Matrix

1. Cross-flavor mirroring -- model/form flavors reach the tail conflict with no post-save `.get()` (verified in the shared skeleton tail); the row-49 fix aligns the serializer flavor; the row-55 guard has no twin (single walk owner).
2. Sync/async twins -- inapplicable: sync-only resolver path plus sync test client; no await boundary in the batch surface.
3. Derived knowledge -- every replacement claim verified at its owner (spec-039 Decision 7 + Improvements H3 text; intent-walk fail-closed oracles; placeholder-walk uniform-type comment).
4. Round-trip pairs -- inapplicable: no encode/decode pair in the batch surface.
5. Contracts in another medium -- spec-039 cites re-verified live (Decision 7 renamed-fields; Improvements nested opt-in); spec-039:1883 validator sentence stays stale (pre-existing, the maintainer's call per the D1 entry); no spec edit owed.
6. Enforcement by omission -- inapplicable: the row-49 `except` covers the whole attestation (M2M reads would false-positive on a vanished row); no sibling read lacks it.

### Freshness

HEAD `23b5f421` unmoved; ITEM_BASELINE `e5f167fb` (= tree at dispatch).
Pre-edit blobs: resolvers `4d05a330`, converter `077a4ee2`, client `3b122fd5`
(all match the folder-artifact pins). Post-edit blobs: resolvers `274610bf`,
converter `9054e1f3`, client `802311c4`. Slot-2 post-edit == shared post-edit
(`cmp` identical all 3). Evidence: sync `7458c4`, pre-fix probes `04295e`
(row-55 AttributeError) + `4f4333` (row-49 DoesNotExist at :2061), post-fix
`b50ec6`, regressions `da9f8b` (360), probes-final `03eb3a`, ruff `e2b472` +
`5e9a24` + `3543bf`, basedpyright main `f8d395` 0/0/0, floor `d7891b` 0/0/0,
truthful-reads `4a737f` tier-1 0, trailing-commas `3425c6` 0.

## Findings

| # | defect | verdict | change |
|---|---|---|---|
| 18 | testing relay D1 | REROUTE `django_strawberry_framework/types/base.py` | census lives at base.py:139-150, outside batch files; recount LEAD 5 / TAIL 4, lines clean |
| 42 | converter D1 | FIXED | dangling `(spec-039 Decision 7 / )` retargeted at the Improvements H3 owning the nested half |
| 43 | converter D2 | FIXED | history-only `#6:` marker dropped; the sentence it prefixes stands verbatim |
| 48 | rf resolvers D1 | FIXED | false `or pop` permission dropped from the substitute-branch message (one clause) |
| 49 | rf resolvers D2 | FIXED (code) + REROUTE `tests/rest_framework/test_resolvers.py` | vanished row skips attestation so the tail conflicts; oracle lands the test |
| 55 | testing client D1 | FIXED (code) + REROUTE `tests/testing/test_client.py` | non-`str` key rejected with the uniform `AssertionError`; oracle lands the test |

Row 18: LEAD claims 3 Meta-key gates (actual 5: base.py:296/:344/:400/:474 + relay.py:104);
TAIL claims 3 compose sites (actual 4, cursor_field omitted). No oracle pins the count (0 hits),
so the mop-up removes the census; lines hunt-free (no hunk spans HEAD 72-177), landable as prose.
Row 48: no oracle matches the clause (3 oracles match the first half only); message fix is
test-neutral; spec-039:1883 stays stale (already false at HEAD; the maintainer's call per the entry).
Row 49: pre-fix probe 500s with the filed `Item.DoesNotExist` at :2061; post-fix conflict
envelope + full rollback. Early return skips the M2M reads too (they would false-positive
on a vanished row). 2 new statements await the oracle.
Row 55: pre-fix probe raises the filed `AttributeError` at :335; post-fix the uniform guard.
`truth.is_instance` keeps the precise public type with zero new suppression/widening (gate-clean).
1 new statement awaits the oracle.

## Defects

None.

## Judgment

5 of 6 rows fixed (3 prose-only + 2 behavior fixes with fail-first proof), 1 rerouted
with exact lines + recount, 2 test halves rerouted with ready content. No hunt line
touched (one same-statement adjacency, changed lines disjoint). No behavior changed
except the two filed escapes. Interim: 3 statements await mop-up oracles. No new defects.

## Implementation (Worker-1)

Landed (slot-2 -> shared tree byte-identical, `cmp` clean all 3; net +29/-8 over
ITEM_BASELINE): `serializer_converter.py` `require_one_segment_source` docstring (42),
`resolve_serializer_field` comment (43); `resolvers.py` substitute message (48),
`_attest_saved_relations` docstring + `try/except model.DoesNotExist` (49);
`testing/client.py` `_assert_file_placeholders` docstring + non-`str` guard (55).
Gates in slot-2 via `heavy`: ruff check + format clean; basedpyright 0/0/0 both
passes; truthful-reads tier-1 0; trailing-commas 0; stripped-AST IDENTICAL on the
converter, resolvers delta scoped to the 2 defs, client delta to the 1 method.
No new suppression/cast/widening in production. Adjacency: row-48 :1936 sits 3
lines under the hunt-rewritten :1933 in one statement (untouched).
REROUTE row 18 (`types/base.py:139-150`): drop the `three`-census clauses, keep the
spec-032 Decision 7 provenance + shape-distinction sentences. REROUTE row-49 test
(`tests/rest_framework/test_resolvers.py`, append near the attestation tests): full-pipeline
vanished-row conflict oracle, content at slot-2 `tests/rest_framework/test_zz_row49_probe.py`
+ `~/dry/tmp/row49-oracle-probe.py` (drop the local fixture/schema builder).
REROUTE row-55 test (`tests/testing/test_client.py`, append near the walker tests):
non-`str` key uniform-guard oracle, content at slot-2 `tests/testing/test_zz_row55_probe.py`
+ `~/dry/tmp/row55-oracle-probe.py` (one sanctioned suppression included).

## Independent verification (Worker-2)

Own verdicts (source entries + current bodies, before reading Findings):
18 REROUTE types/base.py (census at :139-150, outside batch) / 42 FIXED (cite
retargeted per D1) / 43 FIXED (marker dropped, sentence verbatim) / 48 FIXED
(one-clause drop) / 49 FIXED(code)+REROUTE tests/rest_framework/test_resolvers.py
/ 55 FIXED(code)+REROUTE tests/testing/test_client.py. W1's table matches all 6;
zero differences to reconcile.
Row 49 is the root-cause fix: write step returns `saved` straight to the
skeleton tail after attestation (resolvers.py:2529-2537, nothing between touches
the row), and the tail maps a vanished row to the in-band conflict
(mutations/resolvers.py:428-440); the early return also skips the M2M reads,
which would false-positive on a vanished row. Row 55 is the root-cause fix:
`truth.is_instance(key, str)` reads the real MRO, so `str` subclasses still
pass and spoofed non-strings hit the uniform `AssertionError` at the source.
Fail-first re-derived both directions at verify-1 (slot-3, post-fix bytes):
pre-fix probes fail with the filed `AttributeError` at client.py:335
(`dry-20261010T222347-349dbd`) and the filed `Item.DoesNotExist`
(`dry-20261010T222400-bdd4ff`); post-fix both pass
(`dry-20261010T222325-873845`). No other behavior moves: AST scope below plus
message/oracle analysis; the row-55 type change (AttributeError to
AssertionError) IS the filed fix.
Row 48: all 3 substitute oracles match the message's third line only
("replaced a visibility-checked relation"); no test pins the changed clause, so
test-neutral holds. spec-039:1883 stale sentence confirmed on disk; the maintainer's call
per the D1 entry, nothing waits on it.
Row 18: comments still say "three" at base.py:139-150; recount LEAD 5 / TAIL 4
re-verified at current bytes (:296/:344 cursor-field/:400/:474 + relay.py:104);
no HEAD hunk spans the region (clean, landable). Both oracle targets exist and
no run-15 batch list owns them (batch 6 owns other test files only).
Phantoms re-derived: "RelayDriver" 0 hits package-wide; "spec-046" 0 hits in
the converter; "#6" present at baseline :1303 and HEAD :1285, removed by the fix.
Attribution by HEAD..BASE content: hunt touches only the :1933 first line (W1
changed :1936), the fk-get block is pure context, converter regions are
hunk-free, client inserts sit between hunt-clean lines. No hunt-dirtied line
modified. Count note (verdict-neutral): U3 hunks are 46/26/7/3, not W1's
~85/36/12/3; attribution stands on the line checks, not the count.
AST (own script): converter stripped-identical; resolvers delta exactly
`_assert_intent_specs` + `_attest_saved_relations`; client delta exactly
`_GraphQLTestClientBase._assert_file_placeholders`. Gates: ruff format --check
+ ruff check clean (3 files); basedpyright 0/0/0 main (`dry-20261010T222444`)
and floor (`dry-20261010T222557`); truthful-reads tier-1 0
(`dry-20261010T222708`); trailing-commas 0. Regression: 54 passed
(tests/testing/test_client.py + 5 intent-walk oracles, `dry-20261010T222724`).
Freshness pins concur (indices match the item diff; HEAD `23b5f421` unmoved,
status 553). No new defects. Verdict: verified.
