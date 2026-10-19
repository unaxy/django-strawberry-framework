# DRY review: `pk-field-resolution-twin`

Status: verified
Run: 0.0.15 2026-10-11-21

## System trace

Pair: [keyset.py][keyset] `:242-250` (pk arm + `get_field`); [relations.py][relations]
`:255-271` (guard + pk arm + `get_field`). Touch lines HEAD-clean (region diff vs
`git show HEAD:` empty; foreign `:239`/`:342+`). Owner read at WT bytes, unedited.
Keyset callers take only `definition.model` (finalizer `:1005`, keyset `:319`);
`Meta.model` must be a Django model class (`types/base.py:1380-1384`), so the guard is
unreachable from keyset's callers — proven. Census (`== "pk"`): 15 hits / 11 files,
hunt count reproduced. FIELD pair = these two (this item); NAME x4 = F2 (item D);
`id_attr` x4 = F3 (wave-2 H1); rest excluded. Prior art: R13/F4 named other targets
(verdicts stand, F4 unfired); R3's trigger fires for this pair; run-19 F3 is screens.

## Verification

### Matrix

1: NAME mirrors read (F2). 2: no await, pure `_meta`. 3: census homed. 4: one-way, no
halves. 5: docstrings state the rule; zero spec cites; oracles literal. 6: two defs, no gap.

### Challenges

- C1 (alias vocabulary): both pk arms move — 2, real logic each.
- C2 (composite-pk fail-closed, cf. `has_composite_pk`): both bare `meta.pk` move — 2.
- C3 (missing-name vocabulary): both loud `FieldDoesNotExist` delegations move — 2.
- Drift horn: the guard already splits them (off-domain AttributeError vs typed refusal).
- Data horn: pk-alias feeds cursor columns; a wrong column mints a wrong page.

## Findings

### F1: keyset twin composes the segment-field owner

- Contract: `(model, name) -> field`, pk honored, loud `FieldDoesNotExist`. No traversal.
- Sites: keyset `:242-250` becomes a call; 3 sites stay consumers; relations `:255-271` owner.
- Bar: C1-C3 count 2 + drift horn + data horn. No machinery.
- Owner: `_resolve_segment_field` (narrowest; private import precedented, connection.py:75). No stored derivation.
- Migration: body becomes the composed call + one import; docstring points at the owner.
Index row for Worker-0: `pk-field-resolution-twin`, owner relations, `consolidated`.
- Shrinkage: -3/+1 body, +1 import; see `## What shrinks`.
- Distinct: caller policies stay. Off-domain: non-model AttributeError -> FieldDoesNotExist
(louder; unreachable). Reverse-through-columns identical.
- Proof: `execution-verified` in-copy: 14 green, twin+owner files 218 green, M1 2/2 +
M2 5/5 pinned (prove `dry-20261012T014226-ae0157`). Live tier unreachable for the pk arm
(no `("pk",)` type; post-finalize registration impossible; new example model barred).
- Negative control: none; bypass not the threat.
- Coupling: production fences disjoint; port-order with item D only over [test_keyset.py][test-keyset] (pure insertions + 2 tokens).
- Freshness: HEAD `c37a08a0`, baseline `1ad13c97`; keyset `a1890813`/`ec694bc8`; relations `b0cc6c33`; tests `b1624f47`; census 15.

### R1: rejected readings (triggers carried)

- F4 targets stand (trigger: related paths); NAME sites to item D (open); relay slot to H1.

## Defects

None.

## Judgment

One rule, two definitions, drift present. Compose at the wrapper. Ready to port.

## Implementation (Worker-1)

Applied + verified in the slot-1 consolidate copy; Worker-0 ports the two files (or the
diffs below, `git apply --check` proven exact). Runs, all green: suite-14
`dry-20261012T014150-b15dde`, files-218 `dry-20261012T014204-7bd91e`, prove
`dry-20261012T014226-ae0157` (M1 2/2, M2 5/5), basedpyright `...-220aa6`, floor
`...-1c941a`, truthful-reads `...-4a1fc1`, trailing-commas `...-3bf707`, citations
`...-8ba781`. Post-edit blobs: keyset `b3f1b48a`, tests `180c76e3`.

```diff
--- a/django_strawberry_framework/keyset.py
+++ b/django_strawberry_framework/keyset.py
@@ -94,5 +94,6 @@
 from .exceptions import ConfigurationError
 from .utils import truth
 from .utils.imports import require_optional_module
+from .utils.relations import _resolve_segment_field
 
 if TYPE_CHECKING:
@@ -242,12 +242,12 @@
 def _resolve_cursor_field_column(model: type[models.Model], name: str) -> ModelField:
-    """Resolve one cursor column name to its model field (``pk`` alias honored).
+    """Resolve one cursor column name through the shared segment-field rule.
 
-    A reverse-relation name resolves to its ``ForeignObjectRel``;
-    ``validate_cursor_field_columns`` is what rejects it.
+    The ``pk`` alias and the ``FieldDoesNotExist`` vocabulary are owned by
+    ``utils.relations._resolve_segment_field``; a reverse-relation name
+    resolves to its ``ForeignObjectRel``, which ``validate_cursor_field_columns``
+    rejects.
     """
-    if name == "pk":
-        return model._meta.pk
-    return model._meta.get_field(name)
+    return _resolve_segment_field(model, name)
 
 
 def cursor_columns_for(
```

```diff
--- a/tests/test_keyset.py
+++ b/tests/test_keyset.py
@@ -32,4 +32,5 @@
 import pytest
-from apps.library.models import Book, Issue, Patron, Periodical
+from apps.library.models import Book, Genre, Issue, Patron, Periodical
 from apps.scalars.models import ScalarSpecimen
+from django.core.exceptions import FieldDoesNotExist
 from django.db.models import Field, Model, Prefetch, QuerySet
@@ -123,6 +123,18 @@
     assert column.name == "pk"
     assert column.field is Issue._meta.pk
     assert column.value_source == "id"
+
+
+def test_cursor_columns_for_resolves_named_column():
+    (column,) = cursor_columns_for(Issue, ("number",))
+    assert column.name == "number"
+    assert column.field is Issue._meta.get_field("number")
+    assert column.value_source == "number"
+
+
+def test_cursor_columns_for_missing_column_raises_field_does_not_exist():
+    with pytest.raises(FieldDoesNotExist):
+        cursor_columns_for(Issue, ("nope",))
 
 
 # ---------------------------------------------------------------------------
@@ -169,6 +169,11 @@
 def test_validate_cursor_field_rejects_relation_column():
     with pytest.raises(ConfigurationError, match="local concrete column"):
         validate_cursor_field_columns("IssueType", Issue, ("periodical", "id"))
+
+
+def test_validate_cursor_field_rejects_reverse_column():
+    with pytest.raises(ConfigurationError, match="local concrete column"):
+        validate_cursor_field_columns("GenreType", Genre, ("books", "id"))
 
 
 def test_validate_cursor_field_rejects_nullable_column():
```

## What shrinks

Net package change over ITEM_BASELINE: +2/-3 lines in
[keyset.py][keyset] (pk-arm restatement becomes one composed call;
one import). No machinery added: no new driver, registry, flag,
helper, wrapper, or constant — the wrapper pre-exists with its 3
call sites, and the composition point is exactly one line plus its
import. [relations.py][relations] untouched (read-only fence).
[test_keyset.py][test-keyset] gains 3 behavioral pins (+18) and 2
import tokens; zero existing oracles rewritten. No spec sentence
falsified (zero cites of either body; behavior preserved on the
typed domain). What the consolidation removes: one pk-alias change
obligation (C1-C3 each move 2 definitions today, 1 after), the live
guard drift (off-domain AttributeError vs FieldDoesNotExist becomes
one typed refusal), and the trap where a future pk-rule fix lands on
one body while cursor pagination silently keeps the other. Behavior
table, twin body vs owner body today (all inputs except the last row
identical by the same `get_field` delegation or the same `meta.pk`
read): pk name -> pk field; named column -> that field; FK name ->
forward field; GFK name -> GFK object; reverse name ->
`ForeignObjectRel` (keyset's caller rejects, relations' caller
traverses — policies above the bodies, unchanged); missing name ->
`FieldDoesNotExist` both sides (incl. `related_name="+"` hidden
reverses); model without `_meta` -> AttributeError (twin) vs
`FieldDoesNotExist` (owner): the single delta, outside the
`type[models.Model]` domain, unreachable through `definition.model`
(class-creation validation), louder after. Reader counts:
`_resolve_segment_field` gains its third call site (2 in-module +
this wrapper); `_resolve_cursor_field_column` keeps its 3; every
other census hit holds its file (NAME x4 to item D, id_attr x4 to
H1, bool + whole-path + docstring exclusions stand). Equivalence: the 14-node selection + 218-file sweep are green on
the composed code; M1/M2 failability proves each pin rejects a real wrong resolution.

## Independent verification (Worker-2)

### Own trace (before opening Findings)

Census, own pattern `== "pk"` textual over package: 15 hits / 11 files (14 code +
1 prose, relay.py:304), files: keyset, relations,
orders/sets, connection, permissions, list_field x2, lateral_fetch, walker,
types/relay, relay x3, querysets. Bins: FIELD x2 (keyset:248, relations:269);
NAME x4 (`pk.name if` in orders:836, connection:892, permissions:699,
list_field:728); id_attr x4 (relay:169, types/relay:353, walker:870,
lateral:1203 attname); rest: relay:313/398 guards, list_field:775 whole-path
bool, querysets:3464 bool, 1 prose. Tests: oracle asserts only, zero defs.
Examples: 2 non-alias (`pk-desc`, row.pk value). Scripts: zero. Membership
`in (...,"pk")` (filters/base:921, plans:1096, definition:415): all bool.
Reverse (`predicates.py:236`), stamps, `values("pk")`/`pk__in`/`getattr pk`:
not alias rules. Roles: twin keyset (def -> consumer); owner relations (def);
keyset consumers x3 (cursor_columns_for:267, validate:342/369); relations
in-module x2 (classify_path:332, lenient:467); upstream finalizer:1005,
nested_planner:1230 via keyset:319, connection:1485. relay::_node_id_slot
EXCLUDED: fail-open `(id_attr, field-or-None)` pair over the GlobalID slot vs
strict single resolve (missing -> None vs raise; H1 family). Challenges (mine):
alias vocabulary -> 2; missing vocabulary -> typed error -> 2 (`_node_id_slot`
except-clause is a Django-vocabulary consumer, uncounted); `_meta`-absent
guard -> 2 + drift present (AttributeError vs FieldDoesNotExist). Pre-findings
verdict: consolidate at `_resolve_segment_field`, keyset-side compose,
relations read-only; off-domain delta disclosed + proven unreachable.

### Reconciliation

Census/bins agree exactly. C1-C3 agree (C2's `has_composite_pk` anchor sound;
other-family movers don't dilute the pair count). Data horn judged: wrong page
is not data-exposure; bar met on C1-C3 + drift without it (verdict-neutral).
Behavior table re-derived by execution (read-only shared-tree probe): pk /
named / FK / GFK / reverse-M2M / reverse-FK return identical objects both
bodies; missing + hidden-reverse (`archive_genres`) raise identical
FieldDoesNotExist type + message; non-model (None/int/str/object/plain-class,
pk + named) raises AttributeError (twin) vs FieldDoesNotExist (owner) in every
cell, exactly as tabled. Unreachability: production callers take only
`definition.model` (finalizer:1005, keyset:319; `model=validated.model`
base:852; definitions from connection:1485 + nested_planner:1230); gate
executed on 7 hostile shapes (None/int/str/instance/plain-class/plain-instance
refused ConfigurationError, real model passes, never TypeError); Django model
always carries `_meta`; direct hostile Python calls are out-of-contract and
still loud. Matrix: axis-2 (sync pure `_meta`) + axis-4 (one-way) sound;
axis-6 no third FIELD def (every other hit NAME/id_attr/bool/prose).
Oracles: 3 pins ADDED, zero existing touched (insertions + 2 import tokens).
Equivalence in my copy (staged to W1 bytes, hash-match): 14/14
`dry-20261012T021626-73c8d7`, 218/218 `dry-20261012T021634-0828c9`; my mutants
`w2-every-name-to-pk` 5/5 + `w2-every-name-to-number` 5/5, SHA-restored
`dry-20261012T021659-d74674` (union pins all 7); composed probe 6/6 identical,
non-model now FieldDoesNotExist both, validate -> ConfigurationError
`dry-20261012T021732-59bb35`. W1 runs audited (b15dde 14, 7bd91e 218, ae0157
2/2 + 5/5, restore sha 3429c324). Live tier unreachable: no `("pk",)` type
(only IssueType `("-number","id")`); post-finalize registration refused
(registry `_check_mutable` + `__init_subclass__` gate); new-fixture bar; tests/
tier CORRECT, no fixture defect owed (pinned, not gapped). Diff hunk-by-hunk
exact (keyset import + body + docstring; tests net +18; relations
byte-identical `b0cc6c33`; artifact diffs content-identical; live untouched).
No cycle: forward + reverse import proofs `dry-20261012T021530-988068`,
`dry-20261012T021546-492681` + leaf closure; convention exact
(connection.py:75 `_is_supported_cursor_field`) + 4 precedents. Freshness
re-hashed (live `a1890813`/`b0cc6c33`/`b1624f47`, post `b3f1b48a`/`180c76e3`,
HEAD unmoved); import-block foreign hunk adjacent but diff base is live, port
exact (verdict-neutral). Pending-absent CORRECT. Coupling dissolved (D
zero-edit, no port). Prose/shape: no provenance in docstring; Run + caps hold
(147 pre-What-shrinks, trace 11, judgment 3, 10 link groups); ruff
format + check clean in-copy `dry-20261012T021742-7fb51a`,
`dry-20261012T021743-c5705c`. R3 PINNED: `dry-file-utils__relations.md` R3
("pk-alias handling per contract", trigger "one owned pk-alias rule") fires
narrowly for the FIELD pair; NAME/bool split stands. R13 + F4 STAND (F4
trigger unfired: `split_order_ref` still rejects `__`). Docstring zero-cites
verified by grep. Worker-0 note: index row `utils-relations-pk-alias` now
partially converges for the FIELD pair; homing owed at closeout. No defects.

Verdict: verified. Port: `keyset.py` + `test_keyset.py`, slot-1 bytes to live.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[keyset]: ../../django_strawberry_framework/keyset.py
[relations]: ../../django_strawberry_framework/utils/relations.py

<!-- tests/ -->
[test-keyset]: ../../tests/test_keyset.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
