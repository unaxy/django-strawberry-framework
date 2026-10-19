# Review · Comments: `django_strawberry_framework/scalars.py`

Status: findings-recorded
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=be73a504707bc57990681fc526ad5607c1e681d1

## Trace

Read the whole live target (`django_strawberry_framework/scalars.py`, 179
lines: module docstring, 3 function docstrings, 8 `#` comment blocks) and the
whole own test module (`tests/test_scalars.py`, 410 lines: module docstring,
28 test/helper docstrings, 7 section banners, no inline comments). Required
reading in order: AGENTS.md, START.md, REVIEW.md, worker-1.md, the plan
(`docs/review/review-0_0_15.md`, run 0.0.15 2026-09-28-3, incl. its
`## Owned changes`, which holds no row for this target and no Routed lead on
this item), `docs/review/rev-scalars.md` (skeleton, `Status: reviewing`),
then both sibling axis records whole with every Handoff and Cross-axis
section (`rev-scalars.performance.md` and `rev-scalars.mechanics.md`, both
already `Status: findings-recorded` when read). The target and its test
module are dirty vs HEAD (the truthful-reads migration, `+34/-62` on the
target) but byte-identical to ITEM_BASELINE (`git diff be73a504 -- <both>`
empty); every grade below is against the live text at the fingerprints in
this section.

Orientation: `review_inspect.py` overview + stripped source under
`docs/review/temp-tests/scalars/comments/inspect/` plus
`docs/review/temp-tests/scalars/comments/scalars.json`.
`build_tree_md.py --list-docstrings` passes on both graded-whole files
(1 module each, 0 breaking). `check_citations.py --paths <file>
--substrings --json` reports 0 citations, 0 violations in both. Provenance
sweep (REVIEW.md pattern, regex mode) hits only `spec-037` x2 + `spec-025`
(target: M-findings L1 plus the kept Decision 4 pointer) and `spec-037
Decision 5` x2 (tests: kept). `we` x1 (L3); no `you`/`I`, no `Tests
that`/`Ensures`, no `.py:NN`, no TODO, no dead-name reference. No TREE.md
row moves: no finding touches a module first line.

Contract trace, each risky claim against its body and one real caller or
contract source: the Upload/BigInt registration contrast (installed
strawberry-graphql 0.324.0 `DEFAULT_SCALAR_REGISTRY` carries
`Upload: UploadDefinition`; `Upload = NewType("Upload", bytes)`; plus the
workspace probe below); the `int.__str__`/`tp_repr` slot claim
(`int.__str__` is object's slot wrapper, verified on the bench
interpreter); `truth.text` exact-`str` copy (`str.__str__` branch for
`str` inputs); spec-025 Decisions 2/3/4 subjects (match the cited tests),
spec-025 Decision 5 vs spec-037 Decision 5 (different subjects, same
numeral: the L2 ambiguity), spec-037 Decision 5 body (exact home for the
L1 pointers); spec-025 `### Error shapes` (exists, but shared with
spec-022/023/024: the L2 fifth site) and the three quoted `(spec #...)`
labels (each unique to spec-025, verified verbatim); spec-017 Decision 1
+ Non-goals (pins the `Strict...` first lines, the `Decimal integer
strings` spelling, and the `technically arbitrary-precision` framing:
R1/R2/R3); `StrawberryConfig` `auto_camel_case: InitVar` +
`__post_init__` application and `relay_max_results: int = 100`
(installed `config.py`); `ScalarWrapper` internal (exists, exported
nowhere); the live bool/float literal row
(`test_filter_specimens_by_bigint_exact_rejects_non_integer_literal`),
the live int-literal pin
(`test_scalar_specimen_bigint_input_int_literal_argument_over_http`),
and the referenced live test names (both resolve). Other-test prose:
every docstring/comment naming a target symbol in 12 further test
modules (converters BigInt section + MRO-precedence pin, init
re-export pins, mutations BigInt-input + narrow-for-plain-build
comments, live scalars/upload suites incl. the zero-mention filter
suite, forms/mutations/rest_framework Upload-mapping prose, the
transport/setup-probe and visibility plain-schema precedents for M2).
Package prose: every docstring/comment naming a target symbol in 11
further package modules (converters MRO analogy + merge code read,
filters x3, selections `auto_camel_case` knob, inspect merge code read,
resource_policy/debug usage examples, orders/forms/conf/write_values
mentions); all grade true, no Routed lead.

Workspace probe
`docs/review/temp-tests/scalars/comments/probe_bigint_requires_map.py`,
run `review-20260929T114145-a87143` (address
`review/scalars.py/comments`, cell default, copy slot-4 fresh, package
digest `sha256:5c16fc5c26601a47414759f8ac8cbe8e9d797d25d69709512ac1156e3aa8605c`,
exit 0): Upload field builds under a plain `StrawberryConfig`, BigInt
field builds with `strawberry_config()`, BigInt field under a plain
config raises `TypeError: ... Unexpected type
'django_strawberry_framework.scalars.BigInt'` — the spec-025 Decision 5
failure mode, still exact. (One earlier run at this address,
`review-20260929T114139-26ac75`, exit 2 on a relative scratch path that
resolves inside the copy; rerun by absolute path, uncited.)
Cells: default run for the probe, which opens no database. Sharded and
pg are `inapplicable by construction`: the graded prose reaches no
database, alias, or dialect decision (verifier judges).

Sibling correlation (read, not written): Mechanics C1 (Medium,
`## Cross-axis (for Comments)` in `rev-scalars.mechanics.md`) owns the
module docstring's `for direct-call sites` sentence — independently
corroborated here (same live literal pin, same empty production-caller
population) and NOT duplicated below; it rides with Comments and shares
its paragraph with M1 (Handoff). Mechanics R7/R8 and Performance R2/R5
corroborate R3/R2 and the subclass-placement rationale respectively;
Performance F1/F2 will restructure both strict bodies ahead of Comments
(Handoff).

Looks-for discharge (REVIEW.md "Comments"): whole-target + whole-module
grading — this record; other-test prose — all true (above); grades —
below; module first lines — both pass; function mood — R1 (+R5);
public symbol w/o docstring — none (`BigInt`/`Upload`/`UploadDefinition`
are a NewType/re-exports, `strawberry_config` documented); signature
restatement — none; `we` — L3; `Tests that`/`Ensures` — none;
line-number/dead-name refs — none; contradicted stated reasons —
M1/M2/M3 (+C1 cited); unrecorded separations — none (the
Upload-out/BigInt-in split and the parse/serialize asymmetry are each
recorded at the owner, module docstring + factory/test pins).

Fingerprints (`git hash-object`, live) of every file inspected:

- `django_strawberry_framework/scalars.py` `5da8c14052321d214d3e9dfff2bde3d59c90d92c`
- `tests/test_scalars.py` `156b57e13222c7586de017c2c2575c9f995f25f3`
- `django_strawberry_framework/types/converters.py` `f6cadb0856c725d96ce316abb4418b4c9d55bf9d`
- `django_strawberry_framework/utils/truth.py` `d5c96bc8d191d3fce0a20140d8e91063bb466ec9`
- `django_strawberry_framework/management/commands/inspect_django_type.py` `bb63204cca61bc22e6b9bc548db77a7955740002`
- `django_strawberry_framework/filters/inputs.py` `a932dbf85d89791280774b0600a40b5fb43b89e4`
- `django_strawberry_framework/filters/sets.py` `e47c6758e540e0bd9caa8cb90103263b26e905e1`
- `django_strawberry_framework/filters/base.py` `3b1dcbced1069e0faf1abeb33661e94a296f94ba`
- `django_strawberry_framework/optimizer/selections.py` `b189fa15639910e3f59a0e40203154b59f0c7589`
- `django_strawberry_framework/extensions/resource_policy.py` `0134d83a9aa2db580b7b8180ded27a3d31b115c7`
- `django_strawberry_framework/extensions/debug.py` `054e04df5915ed12c49ef63e4710feebca7388aa`
- `django_strawberry_framework/orders/inputs.py` `2d258da74ee36f5d851ffa6550462b0fd65bd460`
- `django_strawberry_framework/forms/inputs.py` `259afbb2d5c7eeadb2ec3e996b26567328dd7295`
- `django_strawberry_framework/conf.py` `3820c575bfd4e3c384244d1bed460b75d3bb7681`
- `django_strawberry_framework/utils/write_values.py` `13548c76605ec264cf95e7d10dc6a8bc813b360d`
- `tests/types/test_converters.py` `ddf24f5997a5185dec079598d7506b6c7d3cf6a3`
- `tests/base/test_init.py` `239648ed635fa67baa10bf5bd428cd127098088b`
- `tests/mutations/test_resolvers.py` `eeab4fbe67bec4ae8835f0c33344002046f3c3f9`
- `tests/forms/test_inputs.py` `6c4617aa821c1c69d3570781ec75f9d32551dc9c`
- `tests/mutations/test_inputs.py` `118f431c1ec81c740ebf0ebd79ca920235af64a3`
- `tests/forms/test_converter.py` `4609b09acd3938d3fd1a15d22122daa30c6abcc3`
- `tests/forms/test_resolvers.py` `6cab42c2ff6779e1a64e98bdc055d24ac6389378`
- `tests/rest_framework/test_inputs.py` `fa60df50a0e536778019a32f0239ec65ad04b30d`
- `tests/rest_framework/test_converter.py` `bb585a38519330e2de546250cfe9aecfa52c2b0a`
- `tests/rest_framework/test_resolvers.py` `0c64d6d4a2c3ba1351652adcd6c19cb1e5f3ed91`
- `tests/testing/test_client.py` `517cf1e680f158b62611f76d1c3d798e4f3f55eb`
- `tests/test_views.py` `3f9c81153f4fa742479d1b8d7792a18e294e6253`
- `examples/fakeshop/test_query/test_scalars_api.py` `edc50088330abef73c3b33dcd8b7f04c5e9e4467`
- `examples/fakeshop/test_query/test_uploads_api.py` `dcbcbf61f730796450b58bd542a525cd8e648275`
- `examples/fakeshop/test_query/test_scalars_filter_api.py` `d2417723cc3a342436b651862f86e17b796ea0f4`
- `examples/fakeshop/test_query/test_products_visibility_api.py` `318bc95ebb66e9e0c76f04c4ce042ee2ef133aec`
- `examples/fakeshop/test_query/test_multi_db.py` `893956aa9eb6cd52446bf6388f506c5663313a14`
- `examples/fakeshop/test_query/test_transport_api.py` `6d65274f9e7b5589d60777d7e0484b3ad10df394`
- `examples/fakeshop/config/schema.py` `303ea2da9df1f8611c02926fd28c59e5ccf9ecac`
- `examples/fakeshop/strategy_schemas.py` `a66200fb22f9441269bd4b44b9c3162408a73893`
- `examples/fakeshop/apps/scalars/schema.py` `6bd2375ee3647fff3c7cfb9e5fc1365416848c36`
- `examples/fakeshop/apps/scalars/models.py` `6f65052e83c0aab1af268784e45bd50bf3a37905`
- `examples/fakeshop/apps/scalars/filters.py` `7b3b5a741e94fe7bf7a3ca91dbcf182d53ef5214`
- `docs/SPECS/spec-017-deferred_scalars-0_0_6.md` `b04cddabc1f1e076b5592bb7c80b55055dd1b3cc`
- `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` `5a7362efa891622b1e9e2e8e816b4a1b8f3d4d73`
- `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` `cc708186f9d120445be2d7b02787d471dabb7f16`
- `docs/review/rev-scalars.md` `fcc1a33008b19e6eea81e45b26270f0b1a1d12be`
- `docs/review/rev-scalars.performance.md` `76b43ee65d7e848f4122e90af4594a40e775af4a`
- `docs/review/rev-scalars.mechanics.md` `2c816f8e7621ebdf3f0866634a19ac26c3a27b07`
- `docs/review/review-0_0_15.md` `291ce1397b98f9710d5b53a05587a3101f64ab05`

Installed-tree reads (no git blob): strawberry-graphql 0.324.0
`file_uploads/scalars.py` (`Upload` NewType), `schema/types/scalar.py`
(`DEFAULT_SCALAR_REGISTRY`), `schema/config.py` (`InitVar`,
`relay_max_results`, `__post_init__`), `types/scalar.py`
(`ScalarWrapper`); CPython 3.14 int slot wrappers.

## Findings

### High

None.

### Medium

#### M1: module docstring serializes "via Python `str(int_value)`" the body deliberately never calls

- Observation: the `BigInt` paragraph says the scalar is "serialized as
  a decimal string via Python ``str(int_value)``". The body goes out of
  its way never to call `str()`: `_serialize_bigint` normalizes via
  `int.__repr__`, and its own comment explains why — ``str(value)``
  dispatches to a subclass's override (`int.__str__` inherits
  `object.__str__`, which delegates to `tp_repr`). With `str()`, the
  pinned `_HostileInt` (`__str__` returning `"forged"`) would emit
  `"forged"`, not `"7"`. The module docstring and the body comment give
  opposite guidance about the same call.
- Evidence: docstring line 12 vs body lines 111-117 at blob `5da8c140`;
  `test_bigint_int_subclasses_are_normalized_before_serialization`
  (hostile `__str__` pinned to `"7"`); Mechanics R8 confirms the two
  mechanisms differ exactly under hostile overrides (no body change
  owed — this finding is prose-only).
- Impact: a maintainer trusting the module gloss ("it is just `str()`")
  misunderstands the load-bearing hardening, or "simplifies"
  `int.__repr__` back to `str()` and breaks the subclass pin. False
  stated mechanism on a public scalar's module docstring; the wire
  contract beside it (decimal string out) is true, so not High.
- Severity: Medium (stale mechanism gloss; contradicts the body's own
  comment).
- Recommendation: name the real call; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'str(int_value)' django_strawberry_framework/scalars.py`
  prints `0` (1 today); the reworded sentence grades true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/scalars.py` module docstring.
- Grade: stale.
- Text-before:
  `It is technically arbitrary-precision - serialized as a decimal string via Python ``str(int_value)`` so values past GraphQL's signed 32-bit ``Int`` boundary survive transit without truncation.`
- Text-after:
  `It is technically arbitrary-precision - serialized as a decimal string (``int.__repr__`` of the accepted ``int``) so values past GraphQL's signed 32-bit ``Int`` boundary survive transit without truncation.`

#### M2: own-test module docstring claims fakeshop always passes `strawberry_config()`

- Observation: the "why no live request can express it" bullet for the
  plain-config Upload pin ends "(fakeshop always passes
  ``strawberry_config()``)". The live tier mounts plain-config schemas
  over real HTTP today: `test_products_visibility_api.py` serves
  `strawberry.Schema(query=Query)` via `override_settings(ROOT_URLCONF)`
  + `post_graphql(url="/graphql/")`, `test_transport_api.py` mounts a
  config-less `_SETUP_PROBE_SCHEMA`, and a dozen further live modules
  build schemas without `config=`. The census is false, and with it the
  placement rationale — a plain-config Upload pin is expressible live
  by the visibility pattern.
- Evidence: module docstring lines 21-23 vs the `strawberry.Schema(` /
  `DjangoSchema(` census over `examples/fakeshop` (20+ config-less
  constructions, three read whole); only the composed project schemas
  (`config/schema.py`, `strategy_schemas.py`) always pass the factory.
- Impact: a reader auditing live-first placement learns a rule ("no
  plain-config request exists") that the cited tier refutes, and the
  bullet's real placement reason stays unstated. Stale census + wrong
  stated reason on internal prose.
- Severity: Medium (stale census on internal prose; wrong stated reason
  for the placement claim).
- Recommendation: replace the false census with the true placement
  reason — the pin asserts on schema-build output (SDL text), identical
  in-process and over HTTP; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'fakeshop always passes' tests/test_scalars.py` prints `0` (1 today); the rewritten bullet grades true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_scalars.py` module docstring.
- Grade: stale.
- Text-before:
  `- ``Upload`` as Strawberry's built-in re-export, absent from the package scalar map, resolving under a plain ``StrawberryConfig`` with no package map (fakeshop always passes ``strawberry_config()``).`
- Text-after:
  `- ``Upload`` as Strawberry's built-in re-export, absent from the package scalar map, resolving under a plain ``StrawberryConfig`` with no package map (a schema-build pin: it asserts on SDL text, identical in-process and over HTTP).`

#### M3: `None`-rejection docstring reaches its path through a route it says never runs

- Observation: `test_bigint_rejects_none` claims "this code path is
  reachable only through (a) non-nullable inputs where Strawberry
  catches ``None`` before ``_parse_bigint`` runs and (b) direct
  unit-test calls". Route (a) describes non-reachability — if
  Strawberry catches `None` before the parser runs, the path is not
  reached through (a). The sentence lists as a reachability route the
  exact case where the parser does not run, so no reader can extract
  the true rule (wire-unreachable both ways; direct calls only).
- Evidence: docstring read against the parser's final `raise` arm and
  the null-strip pins (`test_converters.py` nullable-argument test, the
  live suite's strip comment); route (a)'s mechanism (pre-parser
  interception for non-nullable inputs) is right, the sentence
  structure contradicts it.
- Impact: the defense-in-depth rationale the docstring exists to give
  ("don't remove the `None` check as unreachable") rests on a
  self-contradictory reachability story.
- Severity: Medium (stale reachability claim on internal prose).
- Recommendation: keep the mechanism, fix the structure — unreachable
  via wire either way, reachable only direct; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'Strawberry catches' tests/test_scalars.py` prints `0`
  (1 today); the rewritten docstring grades true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_scalars.py::test_bigint_rejects_none`.
- Grade: stale.
- Text-before:
  `"""Strawberry strips ``null`` before calling ``parse_value`` for nullable inputs, so this code path is reachable only through (a) non-nullable inputs where Strawberry catches ``None`` before ``_parse_bigint`` runs and (b) direct unit-test calls. Tested for defense in depth so a future reader doesn't try to remove the parser's ``None`` check as "unreachable". """`
- Text-after:
  `"""Strawberry strips ``null`` before calling ``parse_value`` for nullable inputs and rejects ``None`` before ``_parse_bigint`` runs for non-nullable ones, so this code path is reachable only through direct unit-test calls. Tested for defense in depth so a future reader doesn't try to remove the parser's ``None`` check as "unreachable". """`

### Low

#### L1: two bare `spec-037` tags in the target name no Decision

- Observation: the module docstring says "per spec-037" and the
  re-export comment says "(spec-037)" — bare spec tags, which the axis
  grades process provenance. The exact home is spec-037 Decision 5
  ("Re-export `Upload` rather than register it"), already named by the
  own test module's banner and pin for this same subject.
- Evidence: Decision 5 body read (re-export + no map entry + the BigInt
  contrast, matching both sites word for word in subject).
- Impact: bounded clarity; the number is right, the pointer unanchored.
- Severity: Low (provenance; correct spec, missing Decision).
- Recommendation: point both at Decision 5; see text-after.
- Must not change: n/a.
- Proof: `grep -c -e 'spec-037)' -e '(spec-037)' django_strawberry_framework/scalars.py` prints `0` (2 today); both rewritten pointers grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/scalars.py` module docstring +
  the `__all__` re-export comment.
- Grade: process provenance.
- Text-before:
  `Strawberry's built-in ``strawberry.file_uploads.scalars`` per spec-037).` /
  `# as the package's public upload scalar (spec-037).`
- Text-after:
  `Strawberry's built-in ``strawberry.file_uploads.scalars`` per spec-037 Decision 5).` /
  `# as the package's public upload scalar (spec-037 Decision 5).`

#### L2: five bare Decision/section numerals in the own test module

- Observation: the test module cites `(Decision 2)`, `(Decision 3)`,
  `(Decision 4)`, `(Error shapes)` (all spec-025 subjects) and
  `(Decision 5)` (a spec-037 subject), while naming `spec-025` zero
  times and `spec-037` twice. No anchor sits on the reader's path for
  the first four (the permissions-L1 shape), and the fifth is
  genuinely ambiguous: spec-025 Decision 5 ("Migration posture: hard
  break in alpha") shares the numeral with spec-037 Decision 5
  ("Re-export `Upload` rather than register it"), as do spec-037
  Decisions 2/3/4 with the bare 2/3/4. All five numerals/section are
  correct (subjects verified against both specs); only the anchors are
  missing.
- Evidence: `grep -c spec-025` over the file prints `0`; both specs'
  Decision lists read; `### Error shapes` heads spec-022/023/024/025
  alike.
- Impact: bounded clarity; a maintainer cannot resolve which spec any
  numeral means without searching, and the Decision 5 site has a
  plausible wrong answer in the file's own other spec.
- Severity: Low (ambiguous pointer, correct numbers).
- Recommendation: anchor all five to their spec; see text-after.
- Must not change: n/a.
- Proof: `grep -c -e '(Decision [0-9]' -e '(Error shapes)' tests/test_scalars.py` prints `0` (5 today, one per line); all five rewritten parentheticals grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_scalars.py::test_strawberry_config_returns_strawberry_config_instance`,
  `::test_strawberry_config_default_scalar_map_includes_bigint`,
  `::test_strawberry_config_collision_with_package_scalar_raises_value_error`,
  `::test_strawberry_config_rejects_scalar_map_kwarg`,
  `::test_strawberry_config_scalar_map_excludes_upload`.
- Grade: ambiguous pointer (bare spec-Decision numerals + section
  name).
- Text-before:
  `(Decision 2)` / `(Decision 3)` / `(Decision 4)` / `(Error shapes)` /
  `(Decision 5)`
- Text-after:
  `(spec-025 Decision 2)` / `(spec-025 Decision 3)` / `(spec-025
  Decision 4)` / `(spec-025 Error shapes)` / `(spec-037 Decision 5)` —
  same sites, same order.

#### L3: serializer body comment speaks as "we"

- Observation: the `int.__repr__` rationale comment says "so we
  normalize via ``int.__repr__``". Authorial `we`, banned by the axis
  rule alongside `you`/`I`; the only such hit in either graded-whole
  file. The mechanism it states is true (verified against the slot
  wrappers and the hostile-subclass pin); only the voice goes.
- Evidence: comment read against `int.__str__`/`int.__repr__` slot
  wrappers and `test_bigint_int_subclasses_are_normalized_before_serialization`.
- Impact: bounded clarity; one voice break in an otherwise voiceless
  file.
- Severity: Low.
- Recommendation: re-voice to the serializer; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'so we normalize' django_strawberry_framework/scalars.py` prints `0` (1 today); the reworded comment grades true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/scalars.py::_serialize_bigint`.
- Grade: authorial voice (`we`).
- Text-before:
  `# ``tp_repr`` (the subclass's ``__repr__``), so we normalize via`
- Text-after:
  `# ``tp_repr`` (the subclass's ``__repr__``), so the serializer normalizes via`

## Rejected

- R1 — Descriptive first lines ("Strict BigInt parser.",
  "Strict BigInt serializer.", and the `_UploadQuery.echo_name` test-stub
  opener): spec-017 Decision 1 pins the first two verbatim, so rewording
  fights the contract source; the target's mood majority is descriptive
  (2 vs the one imperative `strawberry_config`), and the test module
  holds a single helper opener with no convention to enforce. Follows
  the resource_policy-R8 precedent. Trigger: a maintainer mood decision
  applied package-wide.
- R2 — "Decimal integer strings" (parser Accepts): spec-017's pinned
  spelling; the anchored regex on the same line makes "strings"
  unambiguous, and `Decimal`-object rejection is pinned by
  `test_bigint_serialize_rejects_non_int_types` and stated in the
  serializer docstring. Trigger: spec-017's spelling revised.
- R3 — "Technically arbitrary-precision" vs the 4300-digit interpreter
  cap: spec-017's canonical framing (Non-goals + line 568), naming the
  scalar's own unboundedness, not the interpreter's global int/str
  guard; Performance R5 and Mechanics R7 corroborate (symmetric
  boundary, no feasible input reaches it). Trigger: a contract
  promising >4300-digit round-trips.
- R4 — Kept pointers, all verified word-for-word: target "(per spec-025
  Decision 4)" (collision `ValueError`, exact subject); tests
  "(spec-037 Decision 5)" x2 (banner + pin, exact subject); the three
  `(spec #"...")` quoted labels (each unique to spec-025, verified
  verbatim — attribution plus locator, the permissions-R4 shape).
  Trigger: a spec renumber or heading reword.
- R5 — "Today:" module census marker: present-tense set description
  naming no process, and TREE.md renders only the first line.
  Trigger: none.
- R6 — "(the ORM never hands `bool` / `float` / `str` / `Decimal` to
  `_serialize_bigint`)": true within fakeshop flows (no model hands
  those types; the custom-`from_db_value` pathological case spec-017
  contemplates fails loud by design), and the placement rationale it
  carries holds. Trigger: a fakeshop model handing a non-int to the
  serializer.
- R7 — `tests/base/test_init.py` 0.0.14 card narrative: already homed
  on the Project integration item (plan Routed, from `list_field.py`
  Comments). Not re-raised.
- R8 — `tests/mutations/test_inputs.py:970` bare "(spec-037)" banner:
  observed, about that item's file-mapping subject rather than this
  target's symbols; that item grades its own test module whole. Not
  routed (test prose, not package prose).

## Routed leads

None. Every package module's prose about the target's symbols grades
true (see Trace); the two already-homed twins sit under R7/R8, not
here.

## Cross-axis

None. No performance or mechanics finding arose from this pass: the
prose audit surfaced pointers and rationale only, and every mechanism
they describe was verified in place rather than found wanting. (The
`direct-call sites` sentence is owned by Mechanics C1, cited in Trace,
not duplicated here.)

Handoff: Comments review is closed with 3 Mediums (M1 the `str()`
mechanism gloss contradicting the body's own comment, M2 the false
fakeshop-always census behind the Upload placement bullet, M3 the
self-contradictory `None`-reachability sentence) and 3 Lows (L1 two
bare spec-037 tags, L2 five bare Decision/section numerals with a live
Decision-5 ambiguity across two specs, L3 one authorial `we`), plus 8
rejections. Everything else grades true, including the registration
contrast (probe `review-20260929T114145-a87143` reproduces the spec-025
Decision 5 failure verbatim), the CPython slot rationale, the
`truth.text` copy claim, every installed-Strawberry pin (`Upload`
NewType-bytes, default-registry membership, `InitVar`,
`relay_max_results`, `ScalarWrapper` internal), and all cross-module
prose (11 package + 12 test modules, zero Routed leads). Open threads
for Worker-0/Worker-2: M1 and Mechanics C1 share one paragraph
(sentences 2 and 4 of the `BigInt` block) — apply both wordings without
clobbering; Performance F1/F2 restructure both strict bodies ahead of
Comments, so L3's comment may shift context and any new fast-path prose
belongs to the Comments verifier; C1's Proof runs with this axis at
verify time.

## Verify comments

Verify pass 1, Comments axis (incl. Mechanics C1, whose Proof runs with
this axis). Fully static: shared-tree greps, reads, and
`check_citations.py` only; no workspace copy bound, no test run.
Live `git diff ITEM_BASELINE -- <both touched files>` is byte-identical
to `docs/review/temp-tests/scalars/diff/pass-1.diff` (62 insertions, 34
deletions), so every grade below is against pass 1 exactly. Module first
lines unchanged on both files (no TREE.md row moves). Fingerprints
(live): `django_strawberry_framework/scalars.py`
`9e945168903a309f2e0541ad96043b59e47b6b3f`;
`tests/test_scalars.py`
`ab5943d65298b5b7782136a87c6cea4bf2f5cd99` (pass-diff index prefixes
`9e945168` / `ab5943d6` agree). Scratch:
`docs/review/temp-tests/scalars/verify-comments-1/`
(`proofs.txt`, `grade.txt`, `sweeps.txt`, `drift.txt`).

### C1 (Mechanics cross-axis): `direct-call sites` reason — pass

- Proof: `grep -c "direct-call sites"
  django_strawberry_framework/scalars.py` prints `0` (exit 1, no
  matches). Landed sentence (scalars.py:16-17): "the parser additionally
  accepts ``int`` for GraphQL bare-int literals and direct Python
  callers" — names bare-int literals first, verbatim the recommended
  wording.
- Grade true: the literal population is the live-pinned path
  (`test_scalar_specimen_bigint_input_int_literal_argument_over_http`
  resolves at test_scalars_api.py:938); "direct Python callers" states a
  capability, not the empty production-caller census the old sentence
  implied. The C1 code-digest clause (exit 0 vs ITEM_BASELINE) is
  inapplicable on this diff by construction: F1/F2 moved code in the
  same file, so the digest must differ; behavior identity is the
  Performance verifier's probe, not this axis.
- M1+C1 paragraph coherence: both wordings landed in the one `BigInt`
  paragraph without clobbering — sentence 2 the M1 mechanism gloss,
  sentence 4 the C1 reason, the symmetry sentence between them intact;
  the paragraph reads as one coherent contract statement.

### M1: `str(int_value)` mechanism gloss — pass

- Proof: `grep -c 'str(int_value)'
  django_strawberry_framework/scalars.py` prints `0` (exit 1).
- Grade true: landed "(``int.__repr__`` of the accepted ``int``)"
  (scalars.py:12) names the call both serialize legs actually use
  (fast path scalars.py:114-115, subclass leg scalars.py:124); module
  docstring and body comment now agree.

### M2: fakeshop-always census — pass

- Proof: `grep -c 'fakeshop always passes' tests/test_scalars.py`
  prints `0` (exit 1).
- Grade true: landed "(a schema-build pin: it asserts on SDL text,
  identical in-process and over HTTP)" (test_scalars.py:23-24) states
  the real placement reason — the pin asserts on `str(schema)` SDL
  text, which is transport-independent. No census claim remains.

### M3: `None`-reachability sentence — pass

- Proof: `grep -c 'Strawberry catches' tests/test_scalars.py` prints
  `0` (exit 1).
- Grade true: landed "Strawberry strips ``null`` ... for nullable
  inputs and rejects ``None`` before ``_parse_bigint`` runs for
  non-nullable ones, so this code path is reachable only through direct
  unit-test calls" (test_scalars.py:157-159) keeps the mechanism, fixes
  the structure — both wire routes now read as non-reachability, direct
  calls as the sole route. Matches text-after.

### L1: bare `spec-037` tags — pass

- Proof: `grep -c -e 'spec-037)' -e '(spec-037)'
  django_strawberry_framework/scalars.py` prints `0` (exit 1). Both
  sites anchored: module docstring "per spec-037 Decision 5"
  (scalars.py:4-5, wrapped across the line break by the formatter —
  joined-text grep confirms one occurrence) and re-export comment
  "(spec-037 Decision 5)" (scalars.py:33).
- Grade true: Decision 5 ("Re-export `Upload` rather than register
  it") is the verified home for both subjects. Observation only: the
  wrapped anchor is split across two physical lines, so a single-line
  `spec-037 Decision 5` grep finds only the comment site; no action
  (text-after did not prescribe layout).

### L2: bare Decision/section numerals — pass

- Proof: `grep -c -e '(Decision [0-9]' -e '(Error shapes)'
  tests/test_scalars.py` prints `0` (exit 1). All five landed in order:
  `(spec-025 Decision 2)` (test_scalars.py:237), `(spec-025 Decision
  3)` (:243), `(spec-025 Decision 4)` (:304), `(spec-025 Error shapes)`
  (:365), `(spec-037 Decision 5)` (:404). The Decision-5 ambiguity is
  resolved at the site; remaining `spec-037 Decision 5` hits (:387,
  :426) are the pre-existing kept pointers (R4).
- Grade true: every numeral/section matches its text-after anchor and
  verified subject.

### L3: authorial `we` — pass

- Proof: `grep -c 'so we normalize'
  django_strawberry_framework/scalars.py` prints `0` (exit 1).
- Grade true in its shifted context: the comment now sits below the F1
  fast path but still directly annotates the subclass leg it reasons
  about (scalars.py:119-124), and "so the serializer normalizes via"
  (:121) is voiceless with the mechanism untouched. The rationale
  (subclass-override dispatch) still applies exactly to that leg; the
  fast path above handles only exact `int`, where no override exists.

### F1/F2 disturbance: `_parse`/`_serialize` docstrings vs new bodies — pass

- Both docstrings re-graded against the restructured bodies: the
  accept/reject tables are unchanged claims and the fast paths return
  the same expressions as the legs they bypass (`int.__int__` /
  `int.__repr__`; exact-`str` shares the regex tail). No graded
  docstring sentence contradicts the new structure.
- Considered: the parser's bool comment "(before the int check, since
  bool is an int subclass)" (scalars.py:75) now follows the exact-int
  fast path. Still true: the named check is the subclass-aware
  `truth.is_instance(value, int)` leg below it, and the exact-type
  check cannot accept `bool` (`type(True) is bool`), so the ordering
  rationale is undisturbed. The str-leg "Copied to an exact ``str``"
  comment still annotates only the subclass `elif` leg. True.

### `_HostileStr` leg comment + module-bullet tweak — pass

- Leg comment (test_scalars.py:90-92): "copies through the base slot"
  matches the `elif` leg's `truth.text(value)` (`str.__str__` base
  slot); "the forged ``__str__`` never decides the accepted value"
  matches the pin (`_parse_bigint(_HostileStr("7")) == 7`, exact
  `int`); "the serializer rejects ``str`` subclasses like every other
  ``str``" matches the `TypeError` pin and the body (a `str` subclass
  reaches the same final raise as an exact `str`). True.
- Bullet tweak (test_scalars.py:10-11): "``int`` / ``str`` subclasses
  normalized to the canonical wire value" — the new leg normalizes the
  hostile `str` to canonical `7` on the parse side the parenthetical
  scopes ("no GraphQL argument can carry a Python subclass"); the
  serialize-side rejection is covered by the adjacent bullet. True.

### Gates and sweeps — pass

- `check_citations.py --paths <file> --substrings --json` on both
  touched files: 0 citations, 0 violations, 0 warnings each.
- Provenance sweep (REVIEW.md pattern) over both files: only kept
  `spec-025`/`spec-037 Decision` pointers (L1/L2/R4 sites); added-lines
  sweep over the ITEM_BASELINE diff: no hits (exit 1).
- Voice sweep (`we`/`you`/`Tests that`/`Ensures`/standalone `I`): no
  hits (exit 1). Line-reference sweep (`\.py:[0-9]+`): no hits
  (exit 1).

Status: verified (7/7 findings pass: C1, M1, M2, M3, L1, L2, L3; F1/F2
disturbance none; new-leg prose true; gates green; no open threads, no
new defects).

Handoff: Comments verify is closed. Nothing was bound, run, or edited
beyond this section: the verdict rests on shared-tree greps and reads
against a diff proven byte-identical to pass-1.diff. Two observations
carried, neither a defect: (a) the L1 module-docstring anchor wraps
across lines 4-5, so single-line greps for the full anchor find only
the comment site; (b) the C1 code-digest clause cannot hold on a diff
that also moves code — behavior identity belongs to the Performance
probe rerun. Rejections R1-R8 were not re-proven (out of verify scope;
no finding touched their sites).

