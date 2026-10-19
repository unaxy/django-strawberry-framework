# Review: `django_strawberry_framework/extensions/debug.py`

Status: implementing
Run: 0.0.15 2026-09-28-3
Path class: hot per operation when installed (both teardowns drain + collect; fail-closed gate once per op)

## Implementation (Worker-2 pass 1; dispositions carried by Worker-0)

Axis order Performance -> Mechanics -> Comments. Two files changed:
`django_strawberry_framework/extensions/debug.py` (3 code hunks + prose) and
`tests/extensions/test_debug.py` (3 new tests + 4 prose sites).

Attribution (before any edit): `git diff 2dae90d03c0749 -- <target + own
tests>` was empty and the target blob `054e04df` matched the reviewed
fingerprint, so every hunk below is this pass's; the concurrent dirt vs HEAD
(the `__init__` exact-bool check + `truth.describe` import) is preserved
verbatim and covered by the plan's run-3 `Drift:` lines.

### Performance F1 (Medium): implemented

`_query_log_entries_since` takes `budget` (default `_MAX_SQL_ROWS`, so the
existing slicing test calls it unmodified) and returns at most that many
entries via indexed tail over the clamped window; `_build_payload` threads
`remaining = _MAX_SQL_ROWS - len(sql_rows)` across the per-connection loop
and breaks when exhausted. An `IndexError` from concurrent mutation falls
into the existing drain-failure handler (rows so far). Known delta stands:
the refusal log line for a beyond-cap hostile row vanishes. New test
`test_build_payload_serializes_at_most_100_new_log_entries` (N in
{50, 101, 2000}; count == min(N, 100); earliest-100 order; pull-counting
deque double, iteration pulls and indexed gets each <= 100).

### Performance F2 (Medium): implemented

`_collect_exceptions` walks `result.errors` once, keeps the first 25
`original_error` bearers, serializes only those. New test
`test_collect_exceptions_serializes_only_the_first_25_errors` (E in
{10, 26, 100}; count == min(E, 25); earliest-25 order; hostile `__str__`
at position 100 leaves the admitted 25 published).

### Mechanics F1 (Medium defect): implemented

`_disclosure_permitted` short-circuits on acknowledgement, then reads
`settings.DEBUG` inside `try/except (AttributeError, ImproperlyConfigured)`
defaulting inert, keeping exact `is True`; gate comment reworded (getattr
mechanism prose gone). New test `test_unconfigured_settings_is_an_inert_refusal`
beside the Scenario 23 gate rows (`_UnconfiguredSettings` holder raising
`ImproperlyConfigured`; data intact, no `debug` key, exactly one warning,
coordinator empty).

### Mechanics C1 (Medium cross-axis): implemented

All three sync-None sites (class Lifecycle paragraph, `on_operation`
teardown comment, `_stash_payload_if_executed` docstring) now read
None-or-strawberry-pre-execution-shape (sync, version-dependent) /
`PreExecutionError` (async); async halves untouched.

### Comments F1-F15: implemented; F16-F17 deferred

All record text-afters landed except the converged F1: its sync half adopts
the C1 wording ("sync leaves result as None or a strawberry pre-execution
shape, version-dependent") because the record's None-only half is stale per
C1. Deviations: F10 shortened to one 104-char descriptive line (record
text-after was 121 chars: E501/D205); F6 gained one closing paren
rebalancing the outer paren; `_query_log_entries_since` docstring updated
for the bounded drain. F16 (live tier) and F17 (governance) deferred under
the ride rule (files no higher finding touches); both still present
(`now the extension's` x1, `forbids a` x2).

Shared-tree checks: full module `tests/extensions/test_debug.py` 75 passed;
compat nodes unmodified and passing
(`test_query_log_slicing_suffix_clamp_and_rollover`,
`test_exception_collector_guards_filter_order_and_no_dedup`,
`test_deleted_debug_setting_is_an_inert_refusal`); `ruff check --fix`,
`ruff format`, `check_trailing_commas.py` clean on both paths;
`build_tree_md.py --list-docstrings` ok; `check_citations.py` 1/1 resolves.
