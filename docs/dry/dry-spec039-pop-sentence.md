# DRY review: `spec039-pop-sentence`

Status: verified
Run: 0.0.15 2026-10-11-16

## System trace

Spec-truth edit in `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` only.
Found the archived sentence by content at lines 1893-1895 (the 1883 pin is
stale; never used): "A validator may reject or pop a relation (popping reverts
to omitted semantics); it may never substitute or inject one." Read the
enforcing code first: the intent walk in
`django_strawberry_framework/rest_framework/resolvers.py` fails closed on any
pop of a supplied relation (the direct-pop guard plus the fully-consumed
backstop, both unconditional), and the SUBSTITUTE branch carries the
run-15-fixed message. The parenthetical is false at HEAD, so the one sentence
is restated fail-closed, present tense, with no history-note. Live tree
untouched; the edit lives in the copy.

## Verification

### Matrix

1. Cross-flavor mirroring -- inapplicable: one archived sentence, no public surface.
2. Sync/async twins -- inapplicable: no await boundary in the edited sentence.
3. Derived knowledge -- inapplicable: the sentence states a contract; no fact re-derived.
4. Round-trip pairs -- inapplicable: no encode/decode pair in the edited sentence.
5. Contracts in another medium -- this item: spec prose (projection) vs the
   guards (definition) plus the two oracles below. The prose was false; now it matches.
6. Enforcement by omission -- inapplicable: no family membership changes; prose fix only.

### Freshness

Target spec blob `ff9e2e9f` before, `78c12847` after (HEAD `c37a08a0`);
item baseline `e78b3fd8`; live spec `git diff` empty before the copy edit, so
the file was clean at baseline. Searched population = the one target file in
full (every remaining `pop` / `reject` / `omitted` hit re-read for the same
false claim; none found) plus the enforcing module and both oracle bodies.
Contract sources = the dispatch brief, the guards, the two oracles. Excluded
modules: none named -- the brief scopes the item to the one spec file.

## Findings

F1 -- restate the false pop sentence as fail-closed (one sentence, single
owner `docs/SPECS/spec-039-serializer_mutations-0_0_13.md`).

Contract + variation -- what a validator may do to a supplied relation:
reject it (a `ValidationError` reaching the envelope) but never pop,
substitute, or inject one. Varies only if the guards' contract changes.

Sites + roles -- two definitions (the direct-pop guard and the
fully-consumed backstop, both in
`django_strawberry_framework/rest_framework/resolvers.py`); two oracles (the
tests below); one projection (the spec sentence, now fixed). The genuinely
omitted case (client never supplied the relation) keeps omitted semantics in
both code and spec -- untouched.

Challenges -- spec-truth edit, not a package consolidation: no definition
count is claimed. Its bar is START.md (specs sum to the current code) plus the
oracles and the file's gates below; no added machinery (one sentence).

Owner + lifetime -- the spec file owns its own sentences. No stored
derivation; no lifetime fields owed.

Migration -- sentence replaced in place, 2 lines -> 1 line; headings,
anchors, terms, and the link-definitions block byte-identical.

Shrinkage -- net -1 line over the live file; deleted: the false
"(popping reverts to omitted semantics)" parenthetical and its "or pop"
permission. Machinery attestation: no new helper, wrapper, or constant; one
prose sentence.

Behavioral proof -- the two named oracles in
`tests/rest_framework/test_resolvers.py`, bodies read (not re-run, per the
brief), both pin fail-closed:
`test_object_validator_popping_a_supplied_relation_is_rejected`
(a `validate()` popping `genres` raises `ConfigurationError` matching
"removed from validated_data by a validator", and the stored M2M set is
asserted unchanged -- popping is refused, never omitted-semantics);
`test_nested_relation_nulled_after_validation_is_rejected`
(a parent validator nulling a nested value raises `ConfigurationError`
matching "removed from validated_data before the write" -- the backstop
refuses what the inline guard cannot see). File gates, both run in the copy:
`check_trailing_commas.py --check` on the spec exit 0, violations 0 (run
dry-20261011T063522-ef71e8); `check_citations.py` exit 0, 3351/3351 resolve
(run dry-20261011T063526-6e25c9). Both runs report the copy modified on
exactly one path (the spec).

Negative control -- none: bypass is not the threat for a spec-prose edit.

Re-read -- diff is exactly the sentence (copy vs live: lines 1894-1895 ->
one line); present tense; the new line carries zero history tokens
("previously" / "amended" absent; git holds history); new line 84 chars,
ASCII-only; every other `pop` hit in the spec re-read (hook-data
`pop(..., None)`, `sys.modules` pop, `create()` write-only pops) -- each a
different, still-true pop; link-definitions block untouched (diff-clean).

## Defects

None found.

## Judgment

The sentence was false at HEAD and now states the fail-closed contract the
guards enforce and the oracles pin. Ready for independent verification; port
is one file.

## Implementation (Worker-1)

Restated the one sentence in the copy's spec (blob `ff9e2e9f` ->
`78c12847`); live tree untouched. No `.py` touched, so no ruff, pytest, or
basedpyright runs. Port: copy the file to the live tree.

## What shrinks

| edit | rule | change | owner | net | machinery attestation |
|---|---|---|---|---|---|
| 1 | validator pop contract | false "(popping reverts to omitted semantics)" restated as fail-closed | `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` intent-ledger bullet | -1 line | no new machinery; one sentence in place |

## Independent verification (Worker-2)

Recorded from my own reads (spec, diff, code, oracles, sweeps) before opening
`## Findings`; reconciled after. Address `dry/spec039-pop-sentence/verify-1`.

My trace. Live sentence (`spec-039`, line 1894): "A validator may reject a
supplied relation but never pop, substitute, or inject one." Baseline sentence
(from the item diff, old lines 1894-1895): "A validator may reject or pop a
relation (popping reverts to omitted semantics); it may never substitute or
inject one." Guards in `resolvers.py`: the inline direct-pop guard (key absent
from `validated_data` + ledger record present -> `ConfigurationError`,
"never pop it"); the `assert_fully_consumed` backstop (unconsumed record ->
"never drop it", for nested/dropped-list-item removals); the
`_assert_relation_intent` docstring (pop fails closed; a never-sent relation
produces no record and keeps omitted semantics); the genuinely-omitted
`continue` branch. Oracles in `test_resolvers.py`:
`test_object_validator_popping_a_supplied_relation_is_rejected` (line 4819:
`validate()` pops `genres` -> raises matching "removed from validated_data
by a validator", stored M2M asserted unchanged) and
`test_nested_relation_nulled_after_validation_is_rejected` (line 5359: parent
nulls a nested value -> raises matching "removed from validated_data before
the write"). My verdict: restatement correct, sentence was false — the old
parenthetical permits exactly what both guards refuse.

Reconciliation: full concur except one record slip — the artifact's Re-read
says "new line 84 chars"; two instruments (awk, python) measure 87. Both are
within 99, so verdict-neutral; 87 stands as the figure.

Confirmations. (2) Restatement is present tense, fail-closed on pop of a
supplied relation, zero history tokens; the genuinely-omitted case still
reads correctly at line 1931 (omitted partial-update M2M), untouched.
(3) Re-swept myself: `pop` 11 lines — the sentence plus hook `pop(...,
None)` rationale (1855), `sys.modules` pop (2275), `create()` write-only
pops (3362, 3444), and populate/population prose — each a different,
still-true pop; `reject` only the sentence is validator-relation-relevant;
`omit` hits (1502 input semantics, 1852 hook-data, 1931 omitted-M2M) all
true. No other sentence states the false claim. (4) Diff vs `e78b3fd8` is
the sentence only (+1/-2, one hunk); headings/anchors/terms/link block
untouched; line 87 chars; new bytes ASCII-only; zero `][` added.
(5) Fresh gates in slot-3: commas run dry-20261011T063923-02e1e0 exit 0,
violations 0; citations run dry-20261011T063927-ae1725 exit 0, 3351/3351
resolve (matches W1's figure). (6) Blob pins match (live `78c12847...`,
baseline `e78b3fd8`); oracle readings match verbatim; pending execution
empty (no section; correct — proofs are read-oracles + gates per the
brief); no coupling (single F1). No defects found; no `## Defects` entry owed.
