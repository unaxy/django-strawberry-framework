# Review: `django_strawberry_framework/keyset.py`

Status: verified
Run: 0.0.15 2026-09-28-3
Path class: hot - the mint path runs per edge per row; decode/seek run per request per supplied cursor

## Implementation (Worker-2)

Pass 1. Performance and Mechanics closed no-findings; Comments carried 4
Medium + 4 Low, all prose-only. Implemented the 4 Mediums plus the one Low
riding the Medium-touched file; deferred 3 Lows per the Severity ride rule.

Attribution (before any edit): `git diff <ITEM_BASELINE> --` on
`django_strawberry_framework/keyset.py`,
`examples/fakeshop/test_query/test_keyset_api.py` and
`tests/types/test_base.py` was empty (live tree equals the item baseline;
reviewer fingerprints reproduced: `279ad7b0`, `88a432b0`, `bb56c89b`).
`git diff HEAD --` on the target shows only the recorded concurrent
`truth.*` error-message conversion + import (run-3 Drift lines; both axis
records attribute it to its owning flow). `## Owned changes` holds no row
for the target. No foreign hunk; nothing stopped.

### Dispositions

- Performance: no findings (R1-R8 rejected with triggers) — nothing to
  implement.
- Mechanics: no findings (R1-R15 rejected with triggers) — nothing to
  implement.
- Comments Mediums, all `implemented` in
  `django_strawberry_framework/keyset.py` (record's text-after, rewrapped
  to the 99-col layout):
  - M1 `KeysetSeek` docstring (`SAME predicate through q()` overclaim):
    now names both render paths (ORM through `q()`, lateral SQL through
    `plan()` + `keyset_seek_sql`).
  - M2 `encode_keyset_cursor` docstring (phantom bounds-derivation
    consumer): now states the decoders' prefix rejections (keyset decode
    refuses a foreign prefix before authenticated-decryption; the offset
    path's `SliceMetadata` refuses a keyset prefix the same way).
  - M3 `KeysetSeekPlan` docstring (false both-dialects universal): now
    scopes the canonical shape per dialect (ORM always; SQL only for
    mixed directions, row-value comparison for uniform).
  - M4 module docstring (unreachable `WHERE (created_at, id)` tuple
    illustration under the mixed-direction example order): now shows the
    leading-bound-plus-OR-expansion with the row-value form scoped to
    uniform directions.
- Comments Lows:
  - L1 `keyset_contract_error` docstring (past-tense stem sharing):
    `implemented` — rides `keyset.py`, changed for the Mediums above.
  - L2 `test_keyset_api.py` killed-port aside (`_extend_only_projection`
    docstring paragraph): `deferred` — Low whose file no higher finding
    in this item changes.
  - L3 `test_keyset_api.py` reasoning-trace comment (tail-cursor test):
    `deferred` — same reason.
  - L4 `tests/types/test_base.py` card/change provenance (rides with the
    `types/base.py` item): `deferred` — same reason; this record stands
    for that pass.
- Routed leads: none new. The record's `types/definition.py` "signed
  cursors" route and the `(Revision 2 P1)` observation are already in the
  plan's `## Decisions`; the nested_planner `to_attr` twin corroboration
  is already on that item's `Routed:` line.

### Files changed and why

- `django_strawberry_framework/keyset.py` — 5 docstring hunks (M1-M4, L1).
  Sole file changed; the deferred-Low files are untouched. No test file
  changed: prose-only findings owe no permanent test (worker-2 step 3.7).
  Module first line unchanged, so no TREE.md render is owed.

### Before/after numbers

None owed: prose-only change. Inverse proof instead:
`uv run python scripts/review_inspect.py --code-digest
d6f1f0a4c4d291b03cf14e680ab3649aeda10851:django_strawberry_framework/keyset.py
django_strawberry_framework/keyset.py` → exit 0, both digests
`sha256:bb01f2e8fe76bba0d0884be6ec485830283e6853df51348e7507551e6549ee05`.
No workspace run (no `before`/`after` measurement exists for prose); no
run ids.

### Permanent tests

None (prose-only). No focused pytest run; AGENTS.md bars test runs
otherwise.

### Proof greps

Implemented Proofs (each prints `0`): `SAME predicate through`,
`bounds derivation can discriminate`, `both dialects render is the`,
`WHERE (created_at, id)`, `was re-typed at five` — all `0` in
`django_strawberry_framework/keyset.py`. Deferred Proofs (each still `1`):
`killed the strawberry-django` and `all precede it? No` in
`examples/fakeshop/test_query/test_keyset_api.py`;
`stable_cursor_field.*card` in `tests/types/test_base.py` — all `1`.

### Failability proofs

None owed (no gate relies on a prose finding).

### Formatter result

On `django_strawberry_framework/keyset.py` (named explicitly):
`uv run ruff check --fix` → All checks passed;
`uv run python scripts/check_trailing_commas.py` → 1 file, 0 violations;
`uv run ruff format` → 1 file left unchanged. No rewrites.

### Scratch paths and run ids

- `docs/review/temp-tests/keyset/implement/` (created; holds no probe —
  prose-only pass owes no manifest, probe, or workspace run).
- No `review/<item>/implement` workspace runs; no run ids. Reviewer
  scratch under `docs/review/temp-tests/keyset/{performance,mechanics,
  comments}/` read only where the records cite it, otherwise untouched.

### Fingerprints (`git hash-object`, 8-char; live tree at write time)

Touched: `django_strawberry_framework/keyset.py` `d1a6dec2` (was
`279ad7b0` at ITEM_BASELINE). Read: `AGENTS.md` `6475a8cf`, `START.md`
`983d16a2`, `docs/review/REVIEW.md` `47ff82f1`,
`docs/review/worker-2.md` `b44e01da`,
`docs/review/review-0_0_15.md` `6d8d8af6`,
`docs/review/rev-keyset.md` `f2f1367d` (pre-section),
`docs/review/rev-keyset.performance.md` `b9cde7cb`,
`docs/review/rev-keyset.mechanics.md` `04309b97`,
`docs/review/rev-keyset.comments.md` `d2e942ac`,
`examples/fakeshop/test_query/test_keyset_api.py` `88a432b0`,
`tests/types/test_base.py` `bb56c89b`.

Item-scoped diff check: `git diff <ITEM_BASELINE> -- <target>` shows
exactly the 5 hunks above (21+/13-); the two other paths in the
ITEM_BASELINE stat (`docs/dry/dry-0_0_15.md`, `docs/review/review-0_0_15.md`)
are Worker-0/other-flow bookkeeping (dispatch lines, `Routed:`/`## Decisions`
entries), untouched by this pass.

### Proposed owned changes

| Path | Item | Axis | Symbols changed |
|---|---|---|---|
| `django_strawberry_framework/keyset.py` | keyset.py | Comments | module docstring (tuple-illustration scoping); `KeysetSeek` docstring (both render paths); `KeysetSeekPlan` docstring (per-dialect shape); `encode_keyset_cursor` docstring (decoder prefix rejections); `keyset_contract_error` docstring (present-tense stem sharing) |

Handoff: pass 1 is a pure Comments prose pass — 5 docstring hunks on the
target, digest-identical code, 3 Lows deferred by the ride rule with their
Proofs still printing 1. The verifier grades the landed docstrings whole
against the record's text-afters (rewrapped, not reworded) and re-runs the
`--code-digest` identity plus the 8 Proof greps. Open for Worker-0: L2/L3
have no owning open item (their module is this item's own test surface but
carries no higher finding — they stay visible in `## Outcomes`); L4's
record stands for the `types/base.py` item. Nothing disputed, blocked, or
stopped.
