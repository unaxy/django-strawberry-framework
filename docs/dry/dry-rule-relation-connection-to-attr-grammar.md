# DRY review: `relation-connection-to-attr-grammar`

Status: verified, pending execution
Run: 0.0.15 2026-10-01-9

## System trace

The rule is the package-reserved window `to_attr` grammar: the attribute
name a nested relation-connection window lands under on each parent.
Two schemes, one producer:
`_dst_<field>_connection` for a relation whose selections agree on their
arguments (`response_key=None`), and
`_dst_<field>$<key>_connection` per response key for divergent aliases,
with every `_` in the key escaped to `$`. The producer is
[relation_connection_to_attr][nested-planner]
(`optimizer/nested_planner.py:776`, two f-string arms at :786/:788).
The escape exists because Django splits `prefetch_to` on `LOOKUP_SEP`,
so a `to_attr` must never contain `__`; `$` is illegal in both input
vocabularies (Django field names are identifier-vocabulary, GraphQL
response keys match `[_A-Za-z][_0-9A-Za-z]*`), which keeps the grammar
injective. Reads use the exact computed name via `getattr`; nothing
parses a `to_attr` back apart.

Contract sources: [spec-033][spec-033] Decision 4/5 (two schemes, owner,
`$` rationale), the `_dst_` namespace entry in [START.md][start]
("Verified and rejected"), and the window paragraph in
[GLOSSARY.md][glossary]. History (orientation only):
`3054d2cc` merged two single-arm private bodies into the current public
function, so the two-body divergence this family guards against is a
shape that literally existed before.

Site inventory (roles per [DRY.md][dry] vocabulary):

- Definition (1):
  `optimizer/nested_planner.py::relation_connection_to_attr` (:776).
- Compatibility delegates composing by name (2, same module, zero
  grammar tokens): `_relation_connection_to_attr` (:791),
  `_relation_connection_to_attr_for_key` (:796).
- Re-export aliases composing by name (2, zero tokens, zero readers —
  verified by import grep, converging with verified File
  `optimizer/walker.py` row A9..A17): `optimizer/walker.py:110-111`.
- Consumers composing by name or by parameter:
  the planner request loop (`nested_planner.py:1475`,
  `to_attr=relation_connection_to_attr(relation_field_name, resp_key)`);
  the resolve probe (`connection.py:2320` shared arm via the delegate,
  `:2330` per-key arm from `info.path.key`, per-key first with shared
  fallback); the `NestedConnectionRequest.to_attr` record slot
  (`nested_fetch.py:260`) and its attach floor (`:356`,
  `to_attr=request.to_attr`, which the windowed, lateral (`wrap`), and
  single-parent (queryset wrap) strategies all ride); the strictness
  thread (`connection.py:2383`, `to_attr=probe_attr` into
  `types/resolvers.py::_check_n1(kind="connection_to_attr")`, which
  probes the passed string via `getattr` at `resolvers.py:372`).
- Oracles (spell both schemes literally; never import the owner):
  `tests/optimizer/test_walker.py` (shared + divergent-set pins),
  `tests/test_relay_connection.py` (planted attrs, probe-order pins),
  `tests/optimizer/test_plans.py`, `tests/optimizer/test_nested_fetch.py`,
  `tests/optimizer/test_lateral_fetch.py`,
  `tests/optimizer/_builders.py:41` (oracle-side builder f-string),
  `tests/test_lateral_pg_parity.py`, `tests/test_keyset.py`,
  live `examples/fakeshop/test_query/test_library_api.py`.
- Projections: the owner docstring ("Single authoritative owner"),
  the connection fast-path/strictness docstrings, the `_check_n1`
  Decision 8 paragraph, the finalizer `name`-vs-accessor comment, the
  `nested_fetch.py` module docstring, spec-033 prose, the glossary
  paragraph.

Freshness (WT `git hash-object`; HEAD `git rev-parse HEAD:`; BASE
`404927326cc5b0877849ac600aba2475162cffc8`; HEAD `5c3496e0` throughout):

| File | WT | HEAD | BASE |
|---|---|---|---|
| `optimizer/nested_planner.py` | `b6ff0a0e…1ebb` | `8c3a45f5…adb` | == WT |
| `connection.py` | `48de0243…e91a` | `99969652…13b` | == WT |
| `types/resolvers.py` | `a8c6a46e…3949` | `09d40f34…cdf` | == WT |
| `types/finalizer.py` | `0807fea7…c23d` | `662826eb…c3c` | == WT |
| `optimizer/walker.py` | `4fd8077f…f01b` | `13e1be20…e0aa` | == WT |
| `optimizer/nested_fetch.py` | `c36826bb…177` | `bedaa76e…21a` | == WT |
| `tests/test_relay_connection.py` | `aa2528b2…b1c8` (post-gate) | `29a2be59…bee8` | `e6b4b556…5240` (pre-gate) |

WT inputs read at WT only: spec-033 `33b845a3…93ae`,
`tests/optimizer/test_walker.py` `ca5c32d7…cf8`,
`tests/optimizer/test_plans.py` `df714065…490`,
`tests/optimizer/test_nested_fetch.py` `0b65aa96…a5cb`,
`tests/optimizer/test_lateral_fetch.py` `c5aab598…74de`,
`tests/optimizer/_builders.py` `567defa9…6b6b`,
`tests/test_keyset_connection.py` `70db0483…2bb76`,
`test_query/test_library_api.py` `099e25b9…01d76`,
`optimizer/plans.py` `2e962ae2…51249`,
`optimizer/lateral_fetch.py` `a48cb0a4…35848`,
`optimizer/single_parent_fetch.py` `3a4bb89b…93f482`,
`filters/sets.py` `697ffd40…c70834`,
`filters/base.py` `9502e12c…27e9b`,
`orders/sets.py` `8ce11495…7f043`,
`optimizer/predicates.py` `d9e2f789…0e70df`,
`types/definition.py` `ef9e871a…9fb2e`,
`docs/GLOSSARY.md` `95cd34f3…62ff20`.
WT matches BASE on all six indexed files: every WT-vs-HEAD hunk there
predates this item. Full 40-char ids in `## Implementation (Worker-1)`.

## Verification

### Matrix

1. **Cross-flavor policy mirroring** — discharged by census. The
   package holds nine other `_dst_`-prefixed shapes (window row/count
   constants, cursor-value aliases, predicate/order alias prefixes,
   provenance and pk markers, lateral/single-parent/window-signature
   stash names, the keyset-state class attr, the synthesized-marker
   literal). Each is a fixed literal or a differently-keyed
   interpolation with its own readers; none constructs the window
   attach name. Differences + triggers under `## Findings`.
2. **Sync/async twins** — inapplicable with reason. The grammar is a
   pure string function with no await boundary; both production callers
   (request loop, synthesized resolver build) are sync, and the nested
   relation-connection pipeline is sync-only by documented contract
   (`connection.py` resolver docstring), so no twin can drift.
3. **Derived rather than repeated knowledge** — discharged. The
   `<field>_connection` GraphQL field-name grammar
   (`types/finalizer.py:720`) is the one look-alike: same relation
   input, `_connection` suffix, no `_dst_` prefix, no escape. Rejected
   as R1 (separate vocabulary, readers, reasons to change). The
   field-name-vs-accessor keying is standing rejection R-C of verified
   Family `relation-instance-accessor` (trigger-checked, unfired).
4. **Inverse / round-trip pairs** — discharged: encode-only, correctly
   one-way. Zero parse sites package-wide: no `$` split, no `_dst_`
   strip, no `_connection` trim of a window attr (text census over
   `removeprefix`/`removesuffix`/`split`/`startswith("._dst")`).
   Both schemes are read back only by recomputing the exact name and
   probing with `getattr` (`connection.py:2335-2338`,
   `types/resolvers.py:372`), matching the START.md `_dst_` entry.
5. **Contracts restated in another medium** — discharged by role.
   Production holds 1 definition; oracles spell both schemes literally
   (required: an oracle reading the owner could not contradict it);
   prose projections (docstrings, spec-033, glossary) describe. The
   `tests/optimizer/_builders.py:41` f-string is oracle-side: no
   production reader, so it moves with a contract change but is never
   counted as a definition.
6. **Enforcement by omission** — discharged by enumeration. All three
   fetch strategies attach through the one floor
   (`nested_fetch.py::attach_windowed_prefetch:356`,
   `to_attr=request.to_attr`): windowed bare, lateral via `wrap`,
   single-parent via queryset wrap. No strategy builds its own attr;
   no omission.

### Enumeration

Instruments (all run at current WT bytes): an AST census over all 119
package `.py` files for string *constructions* (f-string, `+`/`%`,
`.format()`) whose static text contains both `_dst_` and
`_connection`; text censuses for `relation_connection_to_attr`,
`_dst_`, `to_attr=`, `$`, `_connection`, and walker-import readers.
Counts: constructions **2**, both in
`optimizer/nested_planner.py::relation_connection_to_attr` (:786,
:788); `_`→`$` escape implementations **1** (`:787`); inverse/parse
sites **0**; `to_attr=` production sites 6 (owner call, request floor,
probe thread, two consumer-prefetch pass-throughs in `walker.py`,
one docstring example); walker-alias readers **0**; test importers of
the owner **0**. Every member lands in F1 (definition, delegates,
aliases, consumers, oracles, projections) or in a rejection/exclusion
below; nothing unassigned.

### Challenges

- CH1 (spelling scheme: rename the `_dst_` prefix or the
  `_connection` suffix) — definitions forced: **1** (the owner's two
  arms, one edit). Delegates, aliases, request slot, probe, and
  strictness thread move zero (they call or carry, never spell).
  Oracles + projections that also move: listed, not counted.
- CH2 (escape rule: change `_`→`$` to another encoding or extend it
  to the field segment) — definitions forced: **1** (`:787`).
  Same zero-move followers as CH1.
- CH3 (scheme arity: add a third arm or change the `None`-arm
  default) — definitions forced: **1** (owner gains the arm; a
  delegate signature follows only if the scheme needs a compat name).
  New-scheme oracles pin the new spelling (listed).

Considered boundary (not a challenge outcome): the field segment
passes through unescaped while response keys are escaped, because
field names are identifier-vocabulary and keys are response-key
vocabulary. A `__`-bearing field name would break `prefetch_to`
descent, but no Django-feasible consumer shape reaches the planner
with one (lookups split on `__` first), so this is a documented
property, not a defect. Trigger: `__`-bearing field names that reach
the planner.

Experiments: (a) stdlib AST census probe over the package tree —
119 files, 0 unparseable, exactly the 2 owner arms
(`execution-verified`, `/tmp/relattr_probe.py`, replayable);
(b) stdlib negative-control driver AST-extracting the shipped gate
helper and running it over the real tree (2 owner hits) plus a
`/tmp` copy carrying the exact hand-copy mutant (trips with the
third hit at `connection.py::_build_relation_connection_resolver`)
(`execution-verified`, `/tmp/relattr_control.py`);
(c) focused gate run, shared venv —
`tests/test_relay_connection.py::test_window_to_attr_grammar_has_exactly_one_producer`,
1 passed (`execution-verified`); (d) focused behavior rows, shared
venv — per-key-preferred + annotations-missing fallback, 2 passed
(`execution-verified`). Workspace `prove` unavailable (pool 4/4
bound; slots 1-3 other items, slot-4 own `before` unselectable per
brief KNOWN), so the in-tree mutant proof is `execution-deferred`
under `## Pending execution`.

## Findings

### F1 `relation-connection-to-attr-grammar` — CONFIRM single-owned, gate-only

- Contract + variation: the window attach name from
  `(relation_field_name, response_key | None)`: shared vs per-key
  scheme, `_dst_` prefix, `$` separator, `_`→`$` key escape,
  `_connection` suffix. Varies over schemes, escape, and arity (CH1-3).
- Sites + roles: 1 definition (owner, 2 arms); 2 delegates + 2
  aliases composing by name (zero grammar tokens); 5 consumer sites
  (request loop call, 2 probe calls, request record slot, strictness
  parameter); oracles in 8 test files + 1 live module spelling
  literally; projections in 6 docstrings + spec + glossary. No second
  definition: package-wide construction census yields exactly the 2
  owner arms.
- Challenges: CH1/CH2/CH3 each count **1** (see `### Challenges`).
- Owner + lifetime: `optimizer/nested_planner.py::`
  `relation_connection_to_attr` (principle 7: the producer module both
  sides already import one way — `connection.py` imports the planner;
  the planner never imports `connection.py` or `types/*` — and
  `types/resolvers.py` needs no import at all, receiving the string as
  a parameter). The build-033 residue proposing a move to
  `utils/connections.py` was re-derived and declined: the dependency
  runs one way with no cycle, and a move relieves no change obligation
  (1 body either way). Lifetime (principle 4): pure derivation, not
  cached; cached plans hold produced *values* under the plan cache's
  lifetime, never the rule.
- Migration: no production moves (nothing to consolidate). The
  deliverable is the structural census gate below (gate-only shape:
  owner single + no prior gate). Migrating `connection.py` off the
  private delegates to the public owner, or deleting the unread
  walker aliases, would move zero grammar tokens and relieve no change
  obligation — explicitly not a finding. The alias set stays per
  verified File `optimizer/walker.py` row A9..A17 (converged).
- Distinct behavior: R1 + standing R2/R3/R4 + the scope table below,
  each at its recorded home.
- Behavioral proof: census `execution-verified` (stdlib probe, 119
  files); gate green `execution-verified` (shared venv, 1 passed);
  control detector trips `execution-verified` (shipped-bytes driver);
  behavior rows green `execution-verified` (shared venv, 2 passed);
  in-tree mutant proof `execution-deferred` (pending entry P1).
- Structural gate:
  `tests/test_relay_connection.py::`
  `test_window_to_attr_grammar_has_exactly_one_producer` — AST census
  over the package asserting exactly the 2 owner arms as
  `file::qualname` hits, with an `unparseable == []` guard (shape
  mirrors adopted
  `tests/base/test_init.py::test_package_defines_exactly_one_getlogger_call`).
  Population: interpolated `_dst_…_connection` constructions
  (f-string/`+`/`%`/`.format`); fixed literals and prose are out by
  construction. Negative control: the resolve-side hand copy
  (`connection.py:2320` arm pasted verbatim) — trips the detector
  (shown), passes every behavior oracle (copy is byte-identical
  output; behavior-half proof deferred with P1).
- Coupling: none. No other family shares the owner lines.
- Freshness: fingerprints under `## System trace`; item-scoped diff
  holds only the gate hunks (`## Implementation (Worker-1)`).
- Principle 2 read: one grammar produces the attach name; the request
  loop and the resolve probe both read it. Principle 11: delegates
  have live readers, aliases belong to a ruled-on set — nothing dead.

### R1 synthesized GraphQL field-name grammar — REJECTED

`types/finalizer.py:720` (`f"{name}_connection"`): the public GraphQL
sibling name, no `_dst_` prefix, no escape, read by the schema and the
`relation_connections` record (`types/definition.py`, read — never
rebuilt — by the walker and `inspect_django_type.py`). Difference:
public schema vocabulary vs package-reserved prefetch namespace;
different readers, different reasons to change (GraphQL naming vs
prefetch mechanics). Trigger: either name derives from the other.
Home (present, verified): the finalizer `name`-vs-accessor comment
(`finalizer.py:769-775`, both names' roles) plus the walker keying
docstring (`walker.py:676`, "NOT the generated `<field>_connection`").

### Standing converges (trigger-checked, unfired)

- R2 synthesized marker (`finalizer.py:489`,
  `_dst_synthesized_relation_connection`): fixed class-level
  re-entrancy literal vs interpolated instance-level attach names.
  Standing File `optimizer/nested_planner.py` R10; namespaces still
  distinct, census confirms the marker is a plain constant outside the
  construction population.
- R3 instance accessor (`utils/relations.py::instance_accessor`):
  instance reading vs prefetch attach namespace; the request still
  takes `lookup` from the accessor (`nested_planner.py:1476`) and
  `to_attr` from the field name (`:1475`). Standing verified Family
  `relation-instance-accessor` R-C; trigger (windows keyed on the
  accessor) unfired.
- R4 window row/count annotation names (`optimizer/plans.py`
  `WINDOW_*`): fixed per-row annotation vocabulary read off rows vs
  per-parent attach slots. Standing `nested-fetch-strategy-seam`
  boundary via File `optimizer/nested_planner.py` F4; still fixed
  constants, zero constructions.

### Scope exclusions (each: contract difference + trigger)

| Name | Difference | Trigger |
|---|---|---|
| `_dst_cursor_value_{index}` (`connection.py:994`) | Keyset-codec annotation alias for `F()` values, position-indexed, read by cursor mint/decode — never a prefetch slot | Cursor aliases derive from the window grammar |
| `_dst_predicate_{n}` (`optimizer/predicates.py`) | Generated predicate alias prefix + counter in annotation namespace | Predicate aliases derive from the window grammar |
| `_dst_order_{i}_…` (`orders/sets.py:768`) | Order-alias prefix in annotation namespace | Order aliases derive from the window grammar |
| `_dst_generation_provenance` (`filters/sets.py`) | Fixed input-generation marker literal | Marker becomes interpolated per-field |
| `_dst_globalid_relation_pk` (`filters/base.py`) | Fixed pk-marker literal | Marker becomes interpolated per-field |
| `_dst_lateral_spec` / `_dst_window_signature` / `_dst_single_parent_spec` | Fixed queryset-stash attr names on queryset objects, not parent attrs | Stash names interpolate field/key |
| `_dst_keyset_state` (`connection.py`) | Fixed class-level cursor-state attr | State keyed per field/key |

## Defects

None.

D-W2-1 (Worker-2, observation-grade, non-blocking): the gate helper
`tests/test_relay_connection.py::_window_to_attr_constructions` reads only
one `BinOp` level, so a 3-part `"a" + x + "b"`-style chain holding both
`_dst_` and `_connection` across nesting levels is missed (proven with
shipped bytes via `/tmp/w2_scanner_probe.py`; constant-indirection evasion
is likewise out of reach, as for any dataflow-free AST census). No such
shape exists in the tree and the plausible bypass is caught, so this does
not disturb the verdict. Owner if ever hardened: the gate helper itself
(make `_static_text` recurse into `BinOp` operands).

## Pending execution

- `proof: uv run python scripts/workspace.py prove dry/relattr-f28/consolidate /tmp/relattr-f28-manifest.json`
  — discharges F1's in-tree negative control (entry 1: gate must fail
  under the resolve-side hand copy; entry 2 `[]`: the two behavior
  rows must stay green). Deferred for cause, not for scope: the
  workspace pool was 4/4 bound at proof time (slots 1-3 other items,
  slot-4 own `before` unselectable per brief KNOWN), and shared-tree
  mutation is forbidden. The control logic itself is
  `execution-verified` via the shipped-bytes stdlib driver. Manifest
  (recreate byte-identically if `/tmp` did not survive):

```json
{
  "scratch_root": "/tmp/relattr-f28-failability",
  "proofs": [
    {
      "label": "window to_attr census hand-copy control (resolve side)",
      "target": "django_strawberry_framework/connection.py",
      "anchor": "    to_attr = _relation_connection_to_attr(relation_field_name)",
      "replacement": "    to_attr = f\"_dst_{relation_field_name}_connection\"",
      "mutation": "resolve-side shared-arm construction hand-copied from the owner (identical string)",
      "scope": [
        "tests/test_relay_connection.py::test_window_to_attr_grammar_has_exactly_one_producer",
        "-n0",
        "--no-cov"
      ],
      "expect_failing": [
        "tests/test_relay_connection.py::test_window_to_attr_grammar_has_exactly_one_producer"
      ]
    },
    {
      "label": "window to_attr behavior control under the hand copy",
      "target": "django_strawberry_framework/connection.py",
      "anchor": "    to_attr = _relation_connection_to_attr(relation_field_name)",
      "replacement": "    to_attr = f\"_dst_{relation_field_name}_connection\"",
      "mutation": "same hand copy; behavior rows must stay green",
      "scope": [
        "tests/test_relay_connection.py::test_divergent_alias_per_key_window_preferred_over_shared",
        "tests/test_relay_connection.py::test_fallback_when_annotations_missing",
        "-n0",
        "--no-cov"
      ],
      "expect_failing": []
    }
  ]
}
```

Cells: default — the gate + behavior rows ran green in the shared
venv; the P1 mutant proof above is the one deferred default-cell
command. Sharded/pg — `inapplicable by construction`: the rule is a
pure string derivation and the gate is a source-tree AST scan; neither
reaches a database, alias, or dialect decision (Worker-2 judges).

## Judgment

CONFIRM single-owned, gate-only: the window `to_attr` grammar is
produced in exactly one function (2 arms, 3 challenges each count 1),
consumed everywhere by name or by parameter, with zero second
spellings, zero escape twins, and zero parse sites. The landing is the
structural census gate plus its oracles-tier home — no production
moves, no defects, one deferred in-tree proof.

## Implementation (Worker-1)

Tracked changes: `tests/test_relay_connection.py` only, 4 hunks
(docstring census clause; `import ast` + `from pathlib import Path`;
`import django_strawberry_framework`; `_window_to_attr_constructions`
helper + `test_window_to_attr_grammar_has_exactly_one_producer`).
Production files: zero edits — all six indexed files are WT==BASE.
Item-scoped diff vs `40492732…` is exactly these hunks; the plan-file
hunk in the same diff is Worker-0's dispatch record.

Pre-existing dirt adjudication (by diff content): the test file
carries one concurrent hunk in BASE (`:798-838`, 41 lines,
`test_windowed_fast_path_constructs_no_fallback_queryset` — a behavior
test, no `## Owned changes` row, mid-file). My hunks (imports +
docstring at top, gate appended at EOF) are disjoint from it; it was
read, never edited, reverted, or tidied.

Gates and probes: `ruff check --fix` + `ruff format` clean on the
touched file; `check_trailing_commas.py` clean (0 violations,
ASCII-only); `mypy` clean (119 files); `basedpyright` clean (0/0/0);
`check_any.py` clean (130 uses at 90 sites); no new `cast`/`Any`/
suppression; added lines banned-word scanned clean. Execution in the
shared venv per brief KNOWN (slots 1-3 damaged, slot-4 unselectable;
workspace pool 4/4 bound at proof time): gate 1 passed, behavior rows
2 passed; stdlib drivers `/tmp/relattr_probe.py` (census green) and
`/tmp/relattr_control.py` (control trips) green.

Proposed `## Owned changes` rows for Worker-0 transcription:

- `tests/test_relay_connection.py` — Family `relation-connection-to-attr-grammar` (f28) — gate-only: `_window_to_attr_constructions` + `test_window_to_attr_grammar_has_exactly_one_producer` + module-docstring census clause + 3 imports.

Full fingerprints (40-char): nested_planner WT
`b6ff0a0e998291c5acdf204fd363fd015bb1e1bb` HEAD
`8c3a45f55533cbaf9697013e5d87f599aae65adb` BASE == WT; connection WT
`48de0243613555312478aaeb7b1a2f198923e91a` HEAD
`999696529e18160aff1e465951ebe7e88dd4613b` BASE == WT; resolvers WT
`a8c6a46e0381d52db486cab6a6d24e48fedd3949` HEAD
`09d40f34ddeca4fa7f191fd05b2c8a6bec1f5cdf` BASE == WT; finalizer WT
`0807fea7a87426ba6af4c00356e29276b3a4c23d` HEAD
`662826eb0ab9365ccafb8985014b725f5c9bc3c3` BASE == WT; walker WT
`4fd8077fca391111ceb343a693c0a0c52571f01b` HEAD
`13e1be20e63b8848562e62446b11c64d5893e0aa` BASE == WT; nested_fetch WT
`c36826bb6954642590185ac83deba10cc1423177` HEAD
`bedaa76ebf24d010c4535dddbd1f8e5aa26f621a` BASE == WT; test home WT
`aa2528b234f0187049398856e152474b6960b1c8` HEAD
`29a2be595493a06311c020ec258af1eb1dd6bee8` BASE
`e6b4b5560d27a7373b5e45c8985d338358fe5240`.

## Independent verification (Worker-2)

Recorded BEFORE reading `## Findings` (expectation-first; only the section
headers and the tail fingerprint block were seen before this write).

### Own trace: sites and roles

The rule: the windowed-prefetch `to_attr` grammar — `_dst_<field>_connection`
(shared window) and `_dst_<field>$<key>_connection` (per-response-key window,
`_` in the key escaped to `$`).

- DEFINITION (sole): `django_strawberry_framework/optimizer/nested_planner.py`
  `::relation_connection_to_attr` — 2 f-string arms (default arm and
  keyed arm) plus the single `response_key.replace("_", "$")` escape. The
  docstring already claims single ownership.
- Compatibility delegates (consumers-by-name, zero string construction):
  `nested_planner.py::_relation_connection_to_attr` and
  `::_relation_connection_to_attr_for_key` — both pure forwards.
- Module-alias rebinds (not constructions): `optimizer/walker.py` rebinds both
  private delegates off `_nested_planner` (import-shim style, two assignment
  lines); `connection.py` imports both private delegates by name.
- Consumers by call: `nested_planner.py::plan_connection_relation` region
  (`to_attr=relation_connection_to_attr(relation_field_name, resp_key)` —
  internal by-name call); `connection.py` resolve-side probe (shared attr via
  `_relation_connection_to_attr(relation_field_name)`, per-key attr via
  `_relation_connection_to_attr_for_key(...)` with `info.path.key`).
- Consumers by parameter: `types/resolvers.py::_check_n1`
  (`kind="connection_to_attr"`, `to_attr` threaded in, `getattr` probe only);
  `optimizer/nested_fetch.py::NestedConnectionRequest.to_attr` field carried
  into `Prefetch(..., to_attr=request.to_attr)`.
- Projections (prose only): `types/resolvers.py` docstring,
  `types/finalizer.py` comment, `connection.py` docstrings,
  `optimizer/nested_fetch.py` module docstring all spell the grammar in
  backticks; `types/definition.py` prose cites `books_connection`.
- Excluded by own body (different contract, not second producers):
  `connection.py` `f"_dst_cursor_value_{index}"` (cursor-value annotations, no
  `_connection` token); `orders/sets.py` `f"_dst_order_{index}_..."` (order
  aliases, no `_connection` token); `optimizer/predicates.py`
  `_dst_predicate_` counter (different namespace); `optimizer/plans.py`
  `WINDOW_*` constants (fixed annotation names, plain constants);
  `types/finalizer.py::_SYNTHESIZED_RELATION_CONNECTION_MARKER` (fixed
  literal, not parameterized); `types/finalizer.py` `f"{name}_connection"`
  (GraphQL connection FIELD name, no `_dst_` token — adjacent grammar, own
  owner candidate).
- Parse-back / escape-twin sweep: `$` occurs package-wide only in the owner
  (+ its docstring/prose echoes), GraphQL-variable prose, regexes, the
  `filters/inputs.py` `$`→`iregex` map, and a JS template. No
  `split("$")`, no `removeprefix("_dst_")`, no second `.replace("_", "$")`.
  Zero parse sites, zero escape twins.

### Own challenges (each: change posited + definitions forced)

- C1: rename the `_dst_` prefix (e.g. `_dx_`): only the 2 arms move → count 1.
- C2: rename the `_connection` suffix: only the 2 arms move → count 1.
- C3: change the key escape (`_`→`$` to another mangling): only the escape
  line + keyed arm move → count 1.

Consumers move zero lines under all three (name calls / parameters / prose).

### Owner I would choose

`optimizer/nested_planner.py::relation_connection_to_attr` — already the sole
producer; the two private delegates are compat shims composing it by name.
No consolidation to land: gate-only.

### Scanner-population stress (shipped helper bytes, stdlib probe)

Executed the shipped `_window_to_attr_constructions` (AST-extracted verbatim
from `tests/test_relay_connection.py`, `/tmp/w2_scanner_probe.py`) against 8
shapes: owner f-string HIT; `.format()` HIT; `%` HIT; 2-part `+` with f-string
HIT; `f"{name}_connection"` correctly OUT; plain constants correctly OUT;
3-part `"a" + x + "b"` chain MISSED (nested `BinOp` not recursed — the helper
reads only one `BinOp` level, so neither the outer nor the inner node holds
both tokens); constant-indirection (`f"{P}{x}_connection`) MISSED (no
dataflow). The 3-part miss contradicts the helper docstring's "`+` ...
combination" population claim narrowly; the constant-indirection miss is
beyond any reasonable AST census. Neither shape exists in the tree (exhaustive
`_dst_`/`$`/escape sweeps above), and the plausible bypass — a hand copy of
the owner's f-string body — IS caught. Judged a non-blocking limitation (see
`## Defects` D-W2-1, observation-grade); the gate pins the single producer
against the plausible bypass, which is the DRY.md gate-only standard.

### Gate run (own evidence, shared venv)

`tests/test_relay_connection.py::test_window_to_attr_grammar_has_exactly_one_producer`
passes at current bytes (1 passed). Qualname-stack handling verified by read:
push on FunctionDef/AsyncFunctionDef/ClassDef, visit, pop — balanced; module
level yields `path::` with empty qualname (no hit can hide there since a hit
still records). `hits == [...]` exact-equality assertion pins both cardinality
(2) and identity (one qualname).

### Reconciliation with `## Findings` (read AFTER the trace above)

Agreements (re-derived, not inherited): sole owner
`relation_connection_to_attr` with 2 arms; all challenges count 1; delegates
+ walker aliases compose by name with zero grammar tokens; consumers by
call/parameter (request loop, 2 probe calls, record slot + attach floor,
strictness thread); zero second spellings / escape twins / parse sites;
R1 field-name rejection; R2/R3/R4 converges; all 7 scope rows (each matches
an exclusion in my own sweep); matrix axes 1/3/4/5/6 discharged, axis 2
inapplicable with reason (pure string function, sync-only pipeline —
accepted); enumeration count 2; oracles spell literally with zero test
importers of the owner (confirmed by own grep); gate home
`tests/test_relay_connection.py` is the right oracles-tier home (package
census, unreachable from any GraphQL query); history note `3054d2cc`
exists and touches the planner's `to_attr` unification (orientation only).

Differences, each reconciled:

- Challenge framing: mine posit prefix / suffix / escape; W1's posit
  spelling / escape / arity. Same count-1 verdict on every axis; W1 CH3
  (arity) is an axis I did not posit but its count-1 is evident (a new
  arm lands only in the owner). No material difference — accept.
- Walker-alias readers: W1 claims zero; my trace did not assert. Own
  grep over `tests/`, `examples/`, package: zero readers outside
  `walker.py` itself (only the comment + the two binds). Converges,
  strengthened — accept.
- Oracle census (8 files + 1 live module): spot-verified
  `tests/optimizer/test_walker.py` literal pins (shared + `$` per-key),
  `tests/optimizer/_builders.py:41` oracle-side f-string (no production
  reader — it lives in `tests/`, outside the gate's package scan), and
  the zero-owner-import grep. Accept.
- Axis-6 floor: spot-verified the lateral `wrap` and single-parent
  `rebind` ride `nested_fetch.py:356`, and neither strategy module
  spells a `to_attr` (prose mentions only). Accept.
- R3 trigger: re-checked — the request still takes `lookup` from the
  accessor (`:1476`) and `to_attr` from the field name (`:1475`).
  Unfired — accept. R2/R4 triggers likewise unfired (marker still a
  plain constant, `WINDOW_*` still fixed constants) — accept.
- `__`-bearing-field boundary note: W1 documents it as a property with
  a trigger, not a defect. Consistent with Django lookup semantics;
  trigger recorded — accept.
- Scanner 3-part-`+`-chain miss (my probe, above): the one place my
  trace is stricter than W1's. The helper docstring claims "`+` ...
  combination" coverage but nested `BinOp` is not recursed. No such
  shape exists in the tree, the plausible bypass (hand-copied f-string)
  is caught, and the deferred P1 control exercises exactly that shape.
  Judged a non-blocking limitation — recorded as D-W2-1
  (observation-grade), not a revision driver.

Adjudications on fresh evidence:

- Item diff: EXACTLY the plan edit (single Worker-0 hunk) + the 4
  test-file hunks + this new artifact (`??`); full stat 2 files,
  +167/-2. Production 6/6 WT==BASE (own `hash-object` vs BASE
  `rev-parse`), HEAD pins match dispatch pins on all 7 paths (own
  `rev-parse HEAD:`). Status count 476 = 475 + artifact (own `wc`).
- Dirt: BASE→HEAD removes the 41-line
  `test_windowed_fast_path_constructs_no_fallback_queryset` at `:798`
  (own diff read — W1's `:798-838` boundaries re-derived and confirmed);
  W1's hunks (top imports/docstring + EOF gate) have zero line overlap.
  Disjoint, read-never-touched — accept W1's attribution.
- Deferred P1: cause genuine — pool dry 4/4 bound under my own
  `workspace.py status` (slots 1-3 other items, slot-4 own `before`),
  so no `verify`-address copy is obtainable; brief KNOWN (slot-4
  unselectable, slots 1-3 venvs damaged) independently consistent.
  Manifest reproducible: anchor present exactly once at current bytes
  (own `grep -c` = 1); `/tmp` manifest content byte-identical to the
  artifact block (fences aside); `/tmp` drivers survived. Expected
  outcomes right: entry 1 trips (third hit at
  `connection.py::_build_relation_connection_resolver`), entry 2 stays
  green (byte-identical output). Deferral SUSTAINED — I could not
  execute it either.
- `execution-verified` control claim: REPRODUCED under my hand —
  re-ran `/tmp/relattr_control.py` (real tree 2 owner hits; mutant
  tree 3 hits incl. the resolve-side third hit) and ran my own
  shipped-bytes probe (`/tmp/w2_scanner_probe.py`, 8 shapes).
  Supported.
- Cells: default ran green under my hand (gate 1 passed + 2 behavior
  rows passed, shared venv, stated); sharded/pg `inapplicable by
  construction` ACCEPTED — pure string derivation + source-tree AST
  scan reach no database/alias/dialect, same ruling shape as f18/f21.
- Index rows: NONE owed — R1 home present, converges standing,
  exclusions are exclusions. Endorsed.
- Owned-changes row: ENDORSED VERBATIM — path, family, gate-only
  contents (helper + gate + docstring clause + 3 imports) all accurate.
- Gates (own runs): `ruff format --check` + `ruff check` clean;
  `check_trailing_commas.py --check` 0 violations; `mypy` 119 files
  clean; `basedpyright` 0/0/0; `check_any.py` 130/90; no new
  cast/Any/suppression; banned words clean on word boundaries
  (`planner` substring hits are the module name, not provenance);
  ASCII-only; no `pragma: no cover`. All match W1's claims.
- Fingerprints: W1's table spot-verified comparable — all 6 indexed
  WT==BASE plus all 7 HEAD pins plus test BASE pin confirmed above.

Verdict: `verified, pending execution` (P1 correctly remains). No
standing disagreement; no revision driver; no third pass needed.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[start]: ../../START.md

<!-- docs/ -->
[dry]: DRY.md
[glossary]: ../GLOSSARY.md

<!-- docs/SPECS/ -->
[spec-033]: ../SPECS/spec-033-connection_optimizer-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[nested-planner]: ../../django_strawberry_framework/optimizer/nested_planner.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
