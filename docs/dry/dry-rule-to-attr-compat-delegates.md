# DRY review: `to-attr-compat-delegates`

Status: verified
Run: 0.0.15 2026-10-11-21

## System trace

Target: two one-line forwards in [nested_planner.py][nested-planner]
(`_relation_connection_to_attr`, `_relation_connection_to_attr_for_key`), each a
same-module forward to the documented owner `relation_connection_to_attr`.
`3054d2cc` unified two real bodies into the owner and kept the old private names
as forwards; the in-module construction site moved to the owner in that commit.
Reader census re-derived over package + tests + examples + scripts + specs:
`connection.py` (import + 2 resolve-side calls) was the last executable reader
once the sibling alias item landed; zero readers in tests/examples/scripts, zero
dynamic access, zero spec cites of the delegate names. `spec-033` names the
owner only. Coupling: this deletion ports after `walker-planner-dead-aliases`,
which landed in the live tree mid-item; the copy was re-synced and every proof
re-ran on the post-alias tree.

## Verification

### Matrix

Each axis for the family as a whole. (1) Cross-flavor: no mirror; one grammar,
one producer module. (2) Sync/async: none; a pure string function has no twin.
(3) Derived-twice: the family itself; deletion leaves one producer. (4)
Inverse halves: the grammar is one-way (construct + `getattr` probe); no
second constructor or parser exists. (5) Other media: spec-033 cites the owner
only (no spec edit owed); one dated board sentence names the delegate imports
(see Defects). (6) Omission: nothing to guard; the deleted spellings leave no
member behind.

### Challenges

Grammar change (third arm, new separator, escape-rule change): exactly 1
definition carries logic (the owner) before and after; the forwards are
mechanical, so this lands under principle 11, not the change-obligation clause.
Arity-split contract disproved: both forwards are pure (no validation,
defaulting, or error mapping), their signatures are strict subsets of the
owner's, and both call sites map 1:1 onto owner arms. Compatibility disproved:
"compat" was the pre-unification call-site spelling per `3054d2cc`; the names
are private, all in-repo spellings move in this change, and no consumer
contract names them.

| Site | Role |
|---|---|
| `nested_planner.py::relation_connection_to_attr` | definition (owner, kept) |
| `nested_planner.py::_relation_connection_to_attr` | forward (deleted) |
| `nested_planner.py::_relation_connection_to_attr_for_key` | forward (deleted) |
| `connection.py` import + 2 calls | consumers (migrated to owner) |
| `nested_planner.py:1515` construction site | consumer (already on owner) |
| divergent-alias + fast-path oracles | independent oracles (unchanged) |
| spec-033 owner cites | projection (unchanged) |

## Findings

**Contract + variation.** Package-reserved `to_attr` grammar,
`_dst_<field>_connection` default and `_dst_<field>$<key>_connection` per key;
varies only on response-key presence. **Owner + lifetime.**
`nested_planner.py::relation_connection_to_attr` by responsibility (its module
both constructs the window attr and probes it); pure derivation, not cached.
**Migration.** Both forwards deleted; `connection.py` imports and calls the
owner directly. **Shrinkage.** Net package -11 (planner -10, connection
import -1, call sites rename-only); no new helper, wrapper, or constant.
**Distinct behavior.** None; both arms produce byte-identical attrs.
**Behavioral proof** (all `execution-verified`): `tests/test_relay_connection.py`
+ `tests/test_keyset_connection.py` 90 passed (`dry-20261012T012851-a7a233`);
live `test_keyset_api.py` + `test_library_api.py` 514 passed
(`dry-20261012T013241-769f91`); failability `dry-20261012T012908-1eda15`:
per-key probe minus its key fails exactly the 2 divergent-alias oracles, shared
attr plus a bogus key fails 17 fast-path oracles, both baselines 67 passed, and
each mutant file returned to pre-mutation bytes (SHA-256 matched).
**Negative control.** None; mis-construction is the threat and both arms are
covered by wrong-result oracles. **Coupling.** Ports after the landed
`walker-planner-dead-aliases`; verified on the post-alias tree. **Freshness.**
`ITEM_BASELINE=849dcd6a399bc53f7f18dcf91062fd5a14089f43`; ported blobs
`connection.py 29252be7`, `nested_planner.py 9f99edfe`, post-alias `walker.py
5508e486`; oracles `test_relay_connection.py 6f8e5c33`,
`test_keyset_connection.py 0bca5629`, `test_keyset_api.py 5bd9347a`,
`test_library_api.py b9aa189d`; census patterns `_relation_connection_to_attr`
and `relation_connection_to_attr` over package + tests + examples + scripts +
specs + board docs.

## Defects

- `KANBAN.md:307` (dated 2026-08-27) says `connection.py` imports the delegate
names; true until this item ports, stale after. Board-DB prose, outside this
fence; route to Worker-0 for a maintainer wording touch.

## Judgment

Two forwards with no compatibility left to keep: every reader is migrated, the
owner is documented, and the oracles fail on exactly the wrong results each
migrated call guards. Delete.

## What shrinks

Rule: the window `to_attr` grammar. Change: delete the two pre-unification
forward spellings; resolve-side consumers call the owner by name. Owner:
`nested_planner.py::relation_connection_to_attr` (unchanged). Net: -11 package
lines, zero machinery, zero spec edits, zero test edits. Exact diff (live tree
to ported state; copy holds it at slot-6):

```diff
--- a/django_strawberry_framework/optimizer/nested_planner.py
+++ b/django_strawberry_framework/optimizer/nested_planner.py
@@ -806,16 +806,6 @@
     escaped_key = response_key.replace("_", "$")
     return f"_dst_{relation_field_name}${escaped_key}_connection"
 
 
-def _relation_connection_to_attr(relation_field_name: str) -> str:
-    """Compatibility delegate to ``relation_connection_to_attr``."""
-    return relation_connection_to_attr(relation_field_name)
-
-
-def _relation_connection_to_attr_for_key(relation_field_name: str, response_key: str) -> str:
-    """Compatibility delegate to ``relation_connection_to_attr``."""
-    return relation_connection_to_attr(relation_field_name, response_key)
-
-
 def _connection_node_selections(
--- a/django_strawberry_framework/connection.py
+++ b/django_strawberry_framework/connection.py
@@ -83,8 +83,7 @@
 from .optimizer.nested_planner import (
     _extend_only_projection,
-    _relation_connection_to_attr,
-    _relation_connection_to_attr_for_key,
+    relation_connection_to_attr,
 )
@@ -2302,7 +2301,7 @@
-    to_attr = _relation_connection_to_attr(relation_field_name)
+    to_attr = relation_connection_to_attr(relation_field_name)
@@ -2312,7 +2311,7 @@
-        per_key_attr = _relation_connection_to_attr_for_key(
+        per_key_attr = relation_connection_to_attr(
```

## Implementation (Worker-1)

Edits in slot-6 only; live source untouched. `nested_planner.py`: both forwards
deleted. `connection.py`: import rebound to the owner, both resolve-side calls
renamed. `tests/test_keyset_connection.py` reads zero delegate spellings, so it
stays untouched per the fence. Gates on the ported tree: ruff check + format
(`dry-20261012T012842-6f0ee8`, `dry-20261012T012843-f08272`), basedpyright
(`dry-20261012T012956-878675`) and floor (`dry-20261012T013109-673e64`) both
0/0/0, truthful-reads 0 errors (`dry-20261012T013224-bc2803`), trailing-commas
0 violations (`dry-20261012T013226-6b5aae`), citations 3347 resolve
(`dry-20261012T013227-29d2b4`).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[nested-planner]: ../django_strawberry_framework/optimizer/nested_planner.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker-2)

Own trace (recorded before opening `## Findings`; two instruments,
`muse.search` + `grep -rn`, over package + tests + examples + scripts +
specs/board): delegate spellings occur on exactly 6 `.py` lines, all in
`connection.py` (import :86-87, calls :2305/:2315) and `nested_planner.py`
(defs :809/:814); zero in tests/examples/scripts, zero dynamic or
string-literal readers (`getattr` reads computed attr values, never the
names). Bare owner: def :794 + plan-side call :1515 + the 2 forward
bodies. Live `walker.py` holds 0 mentions; the A live diff deletes
exactly the 2 alias lines (+ comment) present at HEAD, so each delegate
has exactly 1 reader pre-port. `tests/test_keyset_connection.py`: 0
mentions. `spec-033` names the owner only (3 hits). Pre-read verdict:
PROCEED under principle 11 (pure forwards, no remaining compat role).

Reconciliation: no material difference. `3054d2cc` verified in git (message
+ diff: two bodies unified into the owner, old names kept as forwards,
in-module site moved). Strict-subset + 1:1 mapping verified by body and
call-site reading (short -> `None` arm, long -> key arm, no validation
in either). Axis 4 one-way re-derived: 0 parse sites package-wide.
Matrix judged axis by axis, all hold. Counts, roles, and shrinkage
(-11: planner -10, import -2/+1, 2 rename-only calls) confirmed against
the live-vs-slot-6 diff; `tests/` trees identical. Pins re-hashed: ported
`29252be7`/`9f99edfe`, walker `5508e486`, oracles `6f8e5c33`/`0bca5629`/
`5bd9347a`/`b9aa189d`, HEAD `c37a08a0`; live still pre-B (no B-shaped
hunk in its HEAD diff). `3054d2cc` in prose is contract evidence for the
compat disproof, not process narration; the code diff carries none.
`path:NN` cites are allowed in `dry-*.md` per AGENTS.md. D1
(`KANBAN.md:307`, textually confirmed; only the delegate names go stale,
`_extend_only_projection` stays) is board prose outside the fence and
correctly routed, non-blocking. Pending-absent justified: every proof
below is execution-verified. Triggers n/a (no rejections).

Proofs re-run (pool held 6/6, so `verify-1` got no slot; ran in slot-6,
same post-B bytes, digest `927d1012...` unchanged): 90-pair 90 passed
(`dry-20261012T020055-312ef8`, exit 0); failability replicated 2/65 +
17/50 over 67 baselines with SHA-256 restore True both
(`dry-20261012T020112-18632f`, exit 0; post-run blob still `29252be7`;
this independent re-run also discharges M1's <=3-row floor); ruff
format-check + check on both touched paths pass
(`dry-20261012T020201-da5d38`, `dry-20261012T020202-d928e2`). Live 514
judged from W1's log (514 passed in 402.98s, same digest, post-sync),
not re-run on the shared box. Watchlist: link-def `../` is one level
shallow (`../../` is correct here) but gate-irrelevant — both
`check_trailing_commas.py` (`docs/dry/dry-*.md` in `EXCLUDE_SCRATCH_DIRS`)
and `check_citations.py` (per-cycle artifacts out of corpus) exclude this
file — so noted, not routed. Same for the `build-033:383` delegate
sentence (frozen DONE history). `What shrinks` hunk headers and changed
lines match the real diff; context trimmed for display. No (Worker-2)
defects. Verdict: verified.
