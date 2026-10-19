# Review · Mechanics: `django_strawberry_framework/scalars.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=be73a504707bc57990681fc526ad5607c1e681d1

## Trace

Required reading in order: AGENTS.md, START.md,
`docs/review/REVIEW.md`, `docs/review/worker-1.md`, the plan
(`docs/review/review-0_0_15.md`, run 0.0.15 2026-09-28-3, incl.
its `## Owned changes`, which holds no row for this target and
no Routed lead on this item), `docs/review/rev-scalars.md`
(skeleton, Status: reviewing, Path class blank). Sibling axis
records `docs/review/rev-scalars.performance.md` and
`docs/review/rev-scalars.comments.md` did not exist when read
(this record is `rev-scalars.mechanics.md`, read back after
writing); no Handoff or Cross-axis sections to absorb.

Target read whole (179 lines) live at blob `5da8c140`
(dirty per the run-3 Drift lines).
`git diff ITEM_BASELINE -- django_strawberry_framework/scalars.py`
is empty: the item baseline captured the dirty tree, so live
IS the baseline. Reviewed live as dispatched.

Orientation: `review_inspect.py` overview at
`docs/review/temp-tests/scalars/mechanics/inspect/` (json
`docs/review/temp-tests/scalars/mechanics/scalars.json`): 3
symbols, 2 control-flow hotspots, 0 hot entry points, 2
import-time calls (`re.compile`,
`strawberry.scalar`). Leads only.

Edges traced by read (callers, importers, registrations,
oracles, contracts):

- Importers: `types/converters.py` imports `BigInt`
  (`BigIntegerField` / `PositiveBigIntegerField` rows of
  `SCALAR_MAP`); `forms/inputs.py`,
  `mutations/inputs.py`,
  `rest_framework/serializer_converter.py` import `Upload`
  from this module (never from Strawberry directly);
  `management/commands/inspect_django_type.py` imports the
  private `_PACKAGE_SCALAR_MAP` to derive its cold-path
  `_GRAPHQL_SCALAR_NAMES` fallback; the package root
  re-exports `BigInt`, `Upload`, `strawberry_config`.
- Production callers of the privates: none. A repo-wide
  search shows `_parse_bigint` / `_serialize_bigint` /
  `_BIGINT_SCALAR_DEFINITION` referenced only inside
  `scalars.py` (definition + wiring), in tests, and in
  prose. Strawberry alone invokes the parser/serializer,
  with wire-derived values.
- Oracles read whole: `tests/test_scalars.py` (strict
  parser/serializer pins, hostile-subclass normalization,
  factory merge/collision/kwarg pins, Upload re-export and
  default-registry pins). Live tier at grep plus spot
  level: `test_scalars_api.py` (decimal-string AND bare-int
  `BigInt!` argument pins, wire-always-string assertion,
  literal-rejection shape with its masking note),
  `test_uploads_api.py` (multipart + input-mapping pins),
  `test_scalars_filter_api.py` (shape only).
  `tests/types/test_converters.py` BigInt section and
  `tests/base/test_init.py::test_public_api_surface_is_pinned`
  (exact root `__all__`; spec-037 added `Upload` and the
  two file output objects, not `UploadDefinition`).
- Contracts: spec-017 Decision 1 (wire format, accept
  sets, `ValueError`/`TypeError` split, strictness
  symmetry); spec-025 Decisions 2/3/4 + DoD (helper
  shape, `BigInt` in map, collision `ValueError`,
  `scalar_map=` rejection, kwargs passthrough,
  `is None` test) and its rationale (public-map
  promotion rejected); spec-037 Decision 5 + Slice 2
  (re-export `Upload` and `UploadDefinition` at module
  level, root re-exports `Upload` alone, no map entry);
  GLOSSARY `BigInt` / `strawberry_config` / `Upload` /
  Structural error classification; README error policy
  (line 128: unexpected exceptions masked, deliberate
  errors keep their contract); `types/converters.py`
  `SCALAR_MAP` rows; `schema.py` config posture at grep
  level (no `strawberry_config` default: hard-break
  migration per spec-025 Decision 5, consumer passes
  `config=` explicitly).
- Standing citers (`check_citations.py --cited-by`):
  `_PACKAGE_SCALAR_MAP` has 0 citing sites;
  `django_strawberry_framework/scalars.py::strawberry_config`
  has 2, both gated and resolved in KANBAN.md. No
  recommendation moves or renames any symbol, so no
  citer updates are owed.

Looks-for discharge (finding, none+reason, or
rejection+trigger): rule at caller vs owner — none
(strictness, collision, ownership all at their owner;
consumers read the owner, R4); policy/adapter placement
— none (thin factory, no policy layer); contract
sources vs body — agree throughout (R7, R8, R10;
one prose reason wrong, C1); dead branch — none (every
branch maps to a wire, direct-call, or config path;
the `None` arm is spec-017 defense-in-depth, pinned);
mode flag — none in module; state in two places —
none (map single-owned and never mutated post-import;
R3); dependency direction — clean (stdlib +
strawberry + `utils/truth.py`, which imports stdlib
only; the `utils/__init__.py` chain carries zero
references to this module; no `TYPE_CHECKING`; no
django import); settings at import — none (bare-import
subprocess oracle green without settings);
`__all__` — agrees (R5); one rule twice — none (R1,
R2, R3); sync/async twins — none in module; sibling
guard gap — none (R9; parse/serialize asymmetry is
spec-017-pinned deliberate).

Workspace probe
`docs/review/temp-tests/scalars/mechanics/probe_bigint_boundaries.py`,
run `review-20260929T113455-a2fcd9` (address
`review/scalars.py/mechanics`, cell default, copy
slot-3 fresh, package digest
`sha256:5c16fc5c26601a47414759f8ac8cbe8e9d797d25d69709512ac1156e3aa8605c`,
exit 0): past the interpreter's 4300-digit int/str
cap both sides raise `ValueError` (symmetric); a
`NewType("OtherName", int)` key bound to a
`ScalarDefinition` named `AltScalar` builds, serves,
and renders as `scalar AltScalar` with no `OtherName`
in the SDL — the key's own name is ignored.

Cells: default run for the probe. Sharded and pg are
`inapplicable by construction`: pure-Python scalar
functions plus a config factory; no database, alias,
`using`, or dialect decision anywhere in the target
(verifier judges).

Fingerprints (`git hash-object`, live): target
`5da8c140`; `tests/test_scalars.py` `156b57e1`;
`__init__.py` `0ef72601`; `types/converters.py`
`f6cadb08`; `inspect_django_type.py` `bb63204c`;
`utils/truth.py` `d5c96bc8`; `utils/__init__.py`
`1a4c2ec8`; `schema.py` `84f2d5aa`;
`test_scalars_api.py` `edc50088`; `test_uploads_api.py`
`dcbcbf61`; `docs/GLOSSARY.md` `3413edc3`; spec-017
`b04cddab`; spec-025 `5a7362ef`; spec-037 `cc708186`;
plan `291ce139`; `rev-scalars.md` `fcc1a330`.
(A finding's Freshness then lists only files beyond
these; there are none.)

## Findings

### High

None.

### Medium

None.

### Low

None.

## Rejected

### R1: the parse/serialize bool prologues are separate contracts, not one rule twice

`django_strawberry_framework/scalars.py::_parse_bigint`
and
`django_strawberry_framework/scalars.py::_serialize_bigint`
both test bool-before-int, but the rules differ:
the parser rejects with `ValueError` (the GraphQL
`parse_value` contract) while the serializer rejects
with `TypeError`, and the normalizations differ
(`int.__int__` vs `int.__repr__`). DRY change
challenge: posit `change the parse rejection type`
— exactly one definition (spec-017 Decision 1 pins
both bodies near-verbatim, including both
prologues). Sharing a helper would couple two
spec-pinned contract bodies. Trigger: a third
strict-int site, or a shared-behavior change.

### R2: the two `dict()` calls build different dicts

In
`django_strawberry_framework/scalars.py::strawberry_config`,
`dict(extra_scalar_map)` snapshots caller-owned
input (whose errors propagate, pinned) while
`dict(_PACKAGE_SCALAR_MAP)` mints the per-call
fresh package map (isolation pinned). Different
sources, different purposes; spec-025 pins both.
Trigger: a semantic both copies must share.

### R3: the `NewType` name and the definition name are independent slots

`BigInt = NewType("BigInt", int)` and
`strawberry.scalar(name="BigInt", ...)` share a
value but not a rule: the probe binds
`NewType("OtherName", int)` to a definition named
`AltScalar` and the schema renders, serves, and
serializes under `AltScalar` with no `OtherName`
anywhere (`review-20260929T113455-a2fcd9`). The
load-bearing name is the definition's, pinned by
`test_strawberry_config_default_scalar_map_includes_bigint`;
the key name is cosmetic typing metadata.
Single-sourcing via `__name__` would add
indirection for no behavioral difference. Trigger:
a Strawberry release that reads map-key names, or
an observed drift.

### R4: the inspect command's private map import is conventional single-sourcing

`inspect_django_type.py` imports private
`_PACKAGE_SCALAR_MAP` to derive its cold-path
scalar-name fallback, with a comment stating the
single-owner rationale. Intra-package private
imports are this codebase's convention
(`filters/__init__.py` takes
`_input_type_name_for`, `filters/factories.py`
takes `_build_input_fields`, the same command
takes `_is_relay_shaped` and
`_field_output_type_for`); direction is leaf-ward
and correct; zero standing docs cite the map; and
spec-025's rationale explicitly rejected
promoting it to a public export (two parallel
composition paths). No contract promises a public
reader. Trigger: a second consumer, or a contract
demanding one.

### R5: `UploadDefinition` stopping at `scalars.py` is spec-pinned, not an `__all__` gap

`scalars.py::__all__` carries `UploadDefinition`
per spec-037 Slice 2 while the package root
re-exports `Upload` alone per spec-037 Decision 5
("the package root re-exports `Upload` alone"),
and the root `__all__` exact-pin oracle
(`test_public_api_surface_is_pinned`) plus the
GLOSSARY `Upload` anchor (root import of `Upload`
only) agree. Every name in the module `__all__`
is importable from the module. No disagreement.
Trigger: a contract requiring root
`UploadDefinition`.

### R6: hostile `extra_scalar_map` key behavior propagates by contract

`key in extra` can run a consumer key's
`__hash__`/`__eq__` (on hash collision with a
package key). The docstring states that hashing
and comparison are the keys' own behaviour and
whatever they raise propagates, and
`test_strawberry_config_mapping_failure_propagates`
pins propagation. `extra_scalar_map` is
declaration-time same-party configuration — no
wire input reaches it, no trust boundary is
crossed — and every outcome fails loud (an
exception escapes; no schema builds). Trigger: a
wire-reachable path to map keys, or a contract
demanding `ValueError` containment.

### R7: the 4300-digit cap is a symmetric interpreter boundary, not a body defect

Past CPython's int/str digit cap both sides raise
`ValueError` with the interpreter's message
(probe `review-20260929T113455-a2fcd9`); below it
round-trips hold (4000-digit pin in the same
run). No Django 64-bit column value (19 digits
max) reaches the cap; only a custom resolver
returning a 4300-digit int or a 5000-char
literal does, which no contract promises. The
body honors the GLOSSARY mechanism exactly
(`str(int_value)` raises identically past the
cap), both sides fail the same way so
input/output symmetry holds, and no code fix
exists short of process-global
`set_int_max_str_digits` mutation. The GLOSSARY
"handles any `int`" phrasing was considered for
routing and left: below the routing bar (no
feasible input reaches it; interpreter-documented).
Trigger: a contract promising >4300-digit
round-trips.

### R8: the truth-slot hardening is superset-compatible with the pinned mechanism

`int.__int__`, `int.__repr__`, and the
`truth.text` copy behave identically to the
GLOSSARY `str(int_value)` mechanism for every
well-behaved input and differ only under hostile
`int`/`str` subclass overrides, where the
mechanism would emit forged values no contract
promises. Pinned by
`test_bigint_int_subclasses_are_normalized_before_serialization`.
The serializer's bool message uses `{value!r}`
rather than a safe renderer, which is safe
because `bool` is not subclassable: the value is
exactly `True`/`False`. Trigger: a well-behaved
input where the outputs differ.

### R9: no package-side `Upload` guards is the adopted-upstream contract

`Upload` strictness is Strawberry's contract:
spec-037 Decision 5 adopts the upstream scalar
as-is (re-export, no map entry, resolves in any
schema). No contract source places `Upload`
validation in this package, so the absence of a
package guard twin is specified, not a gap.
Trigger: a contract placing `Upload` validation
in the package.

### R10: the collision check need not match the spec's illustrative block

Spec-025's pinned block spells the check as
`_PACKAGE_SCALAR_MAP.keys() & extra.keys()`;
the body tests `key in extra` per package key
and builds the message from framework-owned
definition names only (no consumer-controlled
label ever renders). The pinned contract is the
`ValueError` plus its message text (Decision 4),
which
`test_strawberry_config_collision_with_package_scalar_raises_value_error`
pins byte-for-byte. Mechanism differs;
contract holds. Trigger: message-shape drift.

## Cross-axis (for Comments)

### C1 (Medium): module docstring names "direct-call sites" as the reason the parser accepts `int`

- **Observation** —
  `django_strawberry_framework/scalars.py #"accepts int for direct-call sites"`
  says the parser "additionally accepts `int`
  for direct-call sites". That population is
  empty in production: a repo-wide search shows
  no production caller of
  `django_strawberry_framework/scalars.py::_parse_bigint`
  — Strawberry alone invokes it, with
  wire-derived values. The load-bearing `int`
  population is GraphQL bare-int literals,
  pinned live by
  `test_scalar_specimen_bigint_input_int_literal_argument_over_http`
  ("when the requested value fits in JSON's
  safe-integer range the consumer can pass it as
  a bare int literal ... the resolver must
  receive `42` as an int"). The stated reason
  misdirects (a reader goes looking for callers
  that do not exist) and omits the wire path
  that justifies the branch.
- **Evidence** — Static: the docstring lines
  14-17 at blob `5da8c140` vs the call-site
  search (production hits: the
  `parse_value=_parse_bigint` wiring only) and
  the live pin above at blob `edc50088`, which
  also pins the outbound side stays a decimal
  string for small values.
- **Impact** — A maintainer reasoning about the
  `int` branch (e.g. whether removing it breaks
  the wire contract) is pointed at a
  non-existent caller population instead of the
  live-pinned literal path. Wrong stated reason
  on a public scalar's module docstring.
- **Severity** — Medium: stale/wrong rationale
  prose on a public-surface module about a
  wire-input accept-set; behavior itself is
  correct and pinned, so not High.
- **Recommendation** — Reword to name the
  `int` literal path first (e.g. "the parser
  additionally accepts `int` for GraphQL
  bare-int literals and direct Python callers"),
  keeping the symmetry sentence. Owner: the
  `scalars.py` module docstring.
- **Must not change** — Behavior, incl. every
  `test_bigint_*`, `test_scalar_specimen_*`,
  and `test_strawberry_config_*` pin.
- **Proof** — Static, shared tree:
  `grep -c "direct-call sites" django_strawberry_framework/scalars.py`
  must print `0`, and the landed sentence must
  name bare-int literals. Grade: the reworded
  docstring paragraph grades true against the
  body and the live literal pin. Prose-only
  identity:
  `uv run python scripts/review_inspect.py --code-digest be73a504707bc57990681fc526ad5607c1e681d1:django_strawberry_framework/scalars.py django_strawberry_framework/scalars.py`
  must exit 0 with two equal digests (static,
  shared tree; the Comments verifier runs this
  Proof like one of its own).
- **Freshness** — Trace fingerprints cover
  every cited file.
- **Owner + contract source** — Owner:
  `django_strawberry_framework/scalars.py`
  module docstring. Contract sources: the live
  oracle
  `test_scalar_specimen_bigint_input_int_literal_argument_over_http`
  (names the real `int` population) and the
  Comments rule that a stated reason the body
  contradicts is worse than none.

Handoff: Beyond the record's trace I also read
the spec-025/037 rationale companions (D2-D4,
Decision-5 mechanism notes) and the concurrent
DRY scalars file at grep level for orientation
only — nothing imported; every verdict above
derives from live contracts and the probe. The
module is minimal and fully pinned: strictness
at the owner, single-sourced map, spec-shaped
factory, upstream-owned Upload half. Two threads
for later passes, neither a finding: (a) the
historical hunt record describes a superseded
containment-guard design for `strawberry_config`
(documented propagation is the live, pinned
contract — see R6); (b) the digit-cap symmetry
probe is reusable if any future scalar promises
magnitudes past 4300 digits. Open: C1 rides
with Comments; sharded/pg cells unrun per the
inapplicability claim above (verifier judges).

## Verify mechanics (pass 1)

Address `review/scalars.py/verify-mechanics-1`.
Mechanics has no on-axis findings; this pass
confirms the Performance F1/F2 fast paths
introduce no Mechanics defect, runs C1's
digest Proof in the negative sense, runs the
suites, and confirms R1-R10. Per-check
pass/fail with run ids:

1. Pass-diff integrity - pass. `git diff
   be73a50 -- <both paths>` is byte-identical
   to `docs/review/temp-tests/scalars/diff/pass-1.diff`
   (11075 bytes, DIFF-MATCH): the shared tree
   still carries exactly the change sent to
   grade. Live: `scalars.py` `9e945168`,
   `tests/test_scalars.py` `ab5943d6`;
   baseline `5da8c140` / `156b57e1` match
   the record's Trace.
2. Exact-type-first ordering sound - pass.
   Probe `review-20260929T120355-2bc247`
   (exit 0, package digest
   `sha256:b4b25dfd...`): `type(True) is
   bool` and `type(False) is bool`, so both
   fast paths fall through to the bool legs;
   bool still raises `ValueError` (parse) /
   `TypeError` (serialize) with
   byte-identical messages.
3. Baseline-vs-live equivalence - pass. Same
   run: 46 inputs x 2 seams agree on values
   AND exception type/message (92 legs),
   incl. hostile int/str subclasses, a
   4000-digit int, a 5000-char str, fullwidth
   digits, Decimal/None/object/bytes. Subclass
   legs preserved (int- and str-subclass
   inputs normalize to exact `int`; forged
   dunders never leak); raise-site census 7
   sites both sides, line-shifted only.
4. Shared regex tail equivalent - pass.
   Pattern line unchanged; the tail still
   renders the original `value` (for exact
   `str`, `value is plain_value`); invalid
   exact-str and hostile-subclass-str legs
   raise the identical `requires` message on
   both sides; the non-str `else`-raise
   precedes the regex as before.
5. No dead code - pass. Witnesses B1-B8
   (parse) + S1-S4 (serialize) each fire in
   the same run: every added/restructured
   branch is reachable.
6. No import/setting change - pass. Import
   lines byte-identical (8 lines, +1 shift
   only); 0 `django.conf` / `settings` /
   `connections` refs; the `__all__` block
   and everything from `BigInt = NewType` to
   EOF (definition, map, factory)
   byte-identical.
7. C1 digest, negative sense - pass.
   `review_inspect.py --code-digest
   be73a50:path live` prints `d9a8b8d3` vs
   `3bfa1729`, exit 1: the file DOES carry
   F1/F2 code by design. C1 static Proof
   holds: `grep -c "direct-call sites"` is
   `0`, `bare-int literals` present.
8. Prose-hunk isolation - pass.
   `recon_prose_reverted.py` (live minus
   exactly the 4 prose hunks) vs baseline
   diffs ONLY in the F1/F2 code hunks;
   recon-vs-live `--code-digest` both
   `3bfa1729`, exit 0; recon-vs-live text
   diff is module-docstring lines + 2 `#`
   comment lines only. The C1/M1/L1/L3 hunks
   touch docstring/comment lines only.
9. Suites green - pass, all exit 0 at the
   verify address, cell default, same
   package digest. Own module
   `tests/test_scalars.py`:
   `review-20260929T120403-18b6d3`, 28
   passed (matches the before-state count;
   the `_HostileStr` leg rides inside the
   existing subclass test). Live
   `examples/fakeshop/test_query/test_scalars_api.py`:
   `review-20260929T120412-d548c5`, 82
   passed. Corroborating converters BigInt
   pair: `review-20260929T120439-c59e8c`, 2
   passed.
10. Lint gates - pass. `ruff check`, `ruff
    format --check`,
    `check_trailing_commas.py --check` on
    both touched paths exit 0;
    `check_citations.py --check` whole tree
    exit 0 (1303 resolve; no symbol moved or
    renamed, so the 2 gated
    `strawberry_config` citers stand).
11. R1-R10 undisturbed - pass. R1: the
    `ValueError`/`TypeError` split and the
    `int.__int__` vs `int.__repr__`
    normalizations intact, no shared helper
    introduced. R2/R6/R10: factory
    byte-identical. R3: NewType/definition/map
    byte-identical. R4: map untouched, no new
    consumer. R5: `__all__` byte-identical.
    R7: cap symmetry preserved (4000-digit
    round-trip + 5000-char `ValueError` agree
    both sides). R8: base-slot calls preserved
    on every subclass leg; bool message still
    `{value!r}` on exact bools; hostile pins
    green. R9: Upload half untouched.
12. Cells - default verified (probe + 3 suites
    ran there); sharded + pg inapplicable by
    construction, judged: the target is pure
    functions + a config factory with no
    database/alias/dialect reach, and the
    92-leg equivalence battery (which opens no
    database) cannot vary by cell.

No disputed findings exist; none judged. No
new defects; no failing attack. Scratch:
`docs/review/temp-tests/scalars/verify-mechanics-1/`
(`baseline_scalars.py`,
`baseline_test_scalars.py`, `build_recon.py`,
`recon_prose_reverted.py`,
`probe_equivalence.py`).

Open threads: (1) C1's Proof line as written
compares live directly against ITEM_BASELINE
and now exits 1 by design, since Performance
F1/F2 landed in the same pass ahead of
Comments. The operative form is the
reconstruction check in (8) above (recon file
+ digests under scratch); the Comments
verifier runs it like one of its own. Not a
gap, no re-pass owed.

Status: verified

Handoff: Beyond the record I read the
Performance and Comments records whole with
their Handoffs, the pass-1 diff whole, and
both live files whole. The one judgment call
is the C1 Proof form (open thread 1 above):
the literal command cannot exit 0 on a file
that also carries F1/F2 code, so I proved
the prose hunks digest-neutral via
reconstruction instead. The verify-address
package digest (`b4b25dfd`) differs from the
review-time digest (`5c16fc5c`); expected,
since the tree now carries the pass-1 change.
Nothing else was left for a later pass.
