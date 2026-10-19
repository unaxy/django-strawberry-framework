# DRY review: `graphql-name-gate`

Status: verified
Run: 0.0.15 2026-10-01-11

## System trace

The rule is GraphQL type-name validity: a surface name is valid iff it
matches the spec character grammar and does not take the introspection
reserved `__` prefix. Two gates spell that conjunct independently.
Gate A is the declaration gate in [base][base]`::_validate_meta`
(`Meta.name` at class creation, :1373-1389); gate B is the derivation
gate in [definition][definition]`::DjangoTypeDefinition.graphql_type_name`
(`self.name` else the origin class name, at read time, :257-274).
Both normalize through `truth.text`, both keep per-subject messages,
and both compose the already-single-owned `_GRAPHQL_NAME_RE`
([definition][definition] :33, imported by [base][base] :74) — but the
`fullmatch`-plus-`__` conjunct itself is spelled twice:

- [base][base] :1384:
  `if not _GRAPHQL_NAME_RE.fullmatch(name) or name.startswith("__"):`
- [definition][definition] :269:
  `if not _GRAPHQL_NAME_RE.fullmatch(normalized) or normalized.startswith("__"):`

Verdict: CONFIRM-blocked. The three variation axes each force both
conjuncts to move together (counts below); the reason to change is one
(the GraphQL spec's name grammar plus its introspection reservation,
externally pinned by graphql-core's `assert_name` /
`is_valid_name_error`); every oracle spells literal names, never the
owner's regex. The owner is [definition][definition] via a pure
`is_valid_graphql_name(str) -> bool` predicate both gates compose.
The consolidation cannot land: both gate lines sit inside
hunt truth-migration hunks on paths with no `## Owned changes` row,
so the item is blocked-on-hunt with zero edits and a specified
migration.

Concurrency: both indexed files are dirty vs HEAD, all of it
concurrent work. WT/HEAD pins match dispatch exactly (`e7a62d32` /
`e0ad32aa`, `e79d7129` / `ff80ef02`); HEAD is `dd0b6691`;
ITEM_BASELINE `2f821307007cf6f76494992fdd2bf3e3ca5a5b94` exists.
`## Owned changes` carries no row for either target, and the cycle
baseline predates the hunt dirt, so every hunk below is unattributed
and the paths are untouchable. The exact blocking hunks:

- [base][base] `@@ -1369,44 +1364,41 @@` (WT :1364-1404): the whole
  `Meta.name` gate region rewritten (truth reads, `model_name` hoist,
  typo-guard reword); the :1384 conjunct line itself is byte-identical
  context embedded in the hunk, and the :74 import line sits in hunk
  `@@ -60,13 +60,15 @@`. A call-site edit lands inside hunt bytes.
- [definition][definition] `@@ -247,33 +248,28 @@` (WT :248-275):
  the whole `graphql_type_name` body rewritten (truth reads, label
  hoist, `except BaseException` deletion); the :269 conjunct line is
  byte-identical context embedded in the hunk. Predicate placement
  plus the call-site edit land inside hunt bytes.

Item-scoped diff authored by this item: empty (no tracked file
touched; this artifact is the only output).

## Verification

### Matrix

1. **Cross-flavor mirroring.** Searched every flavor for a second
   validity gate. Enum member naming is sanitize-not-reject
   ([converters][converters]`::_sanitize_member_name`, exclusion R1);
   generated input/enum type names are valid-by-construction encodings
   (`utils/inputs.py::pascalize_token`, exclusion R4) or owned
   templates (verified `generated-choice-enum-name-template` /
   `mutation_input_shape` families, untouched). No flavor gates a
   GraphQL name a second time. Discharged by exclusion, not absence.
2. **Sync/async twins.** Both gates are pure sync string checks with
   no await point, no twin, no color. Inapplicable with stated
   reason: validity is a pure function of one string.
3. **Derived knowledge.** The regex is derived once (single-owned,
   imported once). The `name`-or-class-name derivation has exactly
   one spelling ([definition][definition] :257); the whole-package
   `is not None else` census (80+ sites) shows no second
   surface-name fallback, and all 9 `graphql_type_name` consumer
   files read the property by name. The conjunct is not derived
   anywhere else: it is spelled twice. Discharged.
4. **Inverse / round-trip.** Encode = `graphql_type_name` (gated);
   decode = `registry.py::definition_for_graphql_name` (scan for
   `graphql_type_name == name`, no grammar check). The decode half
   needs no gate: an invalid name matches nothing and raises the
   miss error. Correct one-sided asymmetry, exclusion R5.
5. **Other media.** Oracles spell literal names and message
   fragments; zero test files read `_GRAPHQL_NAME_RE` (census
   below), so the oracles stay independent after consolidation.
   Prose: the [definition][definition] centralization docstring was
   verified true (no inline copies remain); graphql-core's
   `assert_name` / `is_valid_name_error` are the external oracles.
6. **Enforcement by omission.** Name-subject census: type surface
   names (gated, this family); enum members (sanitized, R1);
   generated input/enum names (encoded/template, R4); connection
   names (`f"{graphql_type_name}Connection"` — valid by
   construction, consumer); field names (collision/emptiness
   audited at finalize, grammar delegated to Strawberry's schema
   build — no contract source requires a package-side field grammar
   gate, so the absence is examined-and-clear, never a defect);
   registry decode (correctly ungated, R4-pair R5). No member lacks
   a guard its contract requires. Discharged.

### Enumeration

Family item: the population is every production spelling of the
rule's mechanism, enumerated by instrument over all 120 package
`.py` files (`find` count) via bounded `muse.search` plus an AST
walk (`/tmp/f41_census.py`, kept outside the repo):

- `_GRAPHQL_NAME_RE` tokens: exactly 4 — the :33 definition, the
  [base][base] :74 import, and the 2 gate call sites. One grammar,
  two gates.
- `.fullmatch(` calls: exactly 3 — the 2 gates plus
  `scalars.py::_parse_bigint` over `_BIGINT_STRING_PATTERN`
  (ASCII-decimal-integer grammar, exclusion R3).
- `startswith(` sites: 27 tokens; the only `__`-prefix judgments
  are the 2 gate conjuncts, the enum sanitizer arm (R1), and the
  settings introspection short-circuit (R2). The rest are single
  `_` key filters (R6), ordering `-` prefixes, Django `__`
  lookup separators, `as_sql`, SQL comments, and module paths —
  unrelated mechanisms, each read and excluded by body.
- `graphql_type_name` readers: 9 consumer files, all composing the
  property by name (filters/inputs, filters/base, finalizer,
  types/relay, registry, inspect command, testing/relay,
  connection, relay). Zero re-gates, zero re-derivations.
- Validity-helper definitions matching
  `def (is_valid|assert_valid|validate_)*name*`: zero. No third
  gate exists to converge or reject.
- Test reads of `_GRAPHQL_NAME_RE` across `tests/` + `examples/`:
  zero. Oracles are independent by construction.

### Challenges

F1 is the grammar conjunct
(`not fullmatch or startswith("__")` on a normalized non-empty
`str`). Disproof was attempted first on inputs, outputs, errors,
state, timing, hooks, and reasons to change (see F1); it failed.

- C1 (reserved-prefix arm): the spec drops or extends the `__`
  reservation. Both conjuncts must move: gate A alone dropping it
  lets `Meta.name = "__x"` pass creation then fail at the first
  `graphql_type_name` read; gate B alone dropping it accepts
  `class __Foo` (legal Python, probe-verified) while gate A still
  rejects the identical string as `Meta.name`. **Count 2.**
- C2 (third arm): GraphQL reserves a new pattern (the enum
  `true`/`false`/`null` precedent generalized). Both sites add the
  arm or declaration and derivation verdicts diverge. **Count 2.**
- C3 (conjunction shape): the rule is re-expressed (compose
  graphql-core's `assert_name`, change the call shape). Both call
  sites move; a pure pattern change to the regex itself is already
  count 1 and is not this challenge. **Count 2.**
- C4 (messages, scope control): reword gate A's `Meta.name`
  message. Gate B's `GraphQL type name for ...` message must not
  move (different subject). **Count 1** — messages stay per site,
  converging with verified per-subject-rejection-grammars.
- C5 (outer arms + normalization, scope control): change the
  non-`str`/empty verdicts or the `str`-subclass copy. The
  mechanism (`truth.is_instance`, `truth.text`) is already
  single-owned and composed by name (count 1, different family);
  the remainder is per-site verdict sequencing with different
  timing and reachability (gate A guards raw consumer input at
  creation; gate B's outer arms cover the class-name fallback and
  hand-built definitions at read). **Count 1 per site** — the
  outer trio stays per site; only the conjunct is F1.

Exclusions (each re-derived at current bytes; prior R18-class rows
were trigger-checked, never inherited):

- R1 enum sanitize: [converters][converters]`::_sanitize_member_name`
  :647-652 rewrites (`MEMBER_` prefix) instead of rejecting; total
  function over DB choice values with schema-stability and
  collision-detection obligations. Difference: rewrite vs reject,
  stability vs validity. Trigger: member naming becomes
  validation. Home: its docstring (owed, file dirty).
- R2 introspection short-circuit: [conf][conf]`::Settings.__getattr__`
  :344 raises bare `AttributeError` for dunder lookups so
  copy/inspect work; no grammar involved. Difference: Python
  protocol vs GraphQL grammar. Trigger: none plausible (dunders
  are forever). Home: its docstring (owed, file dirty).
- R3 BigInt grammar: `scalars.py` :95 `fullmatch` over
  `_BIGINT_STRING_PATTERN` (ASCII decimal integers). Difference:
  disjoint grammar, disjoint subject. Trigger: the two grammars
  merge (inconceivable — values vs names). Home: none owed (no
  shared token beyond `fullmatch`).
- R4 valid-by-construction derivations: `pascalize_token` escapes
  (total encoding), connection-name suffixing, owned input/enum
  templates. Difference: construction guarantees validity; no
  verdict exists to share. Trigger: a derivation starts accepting
  unescaped consumer text. Home: none owed.
- R5 decode lookup: `registry.py::definition_for_graphql_name`
  scans for equality; misses raise without a validity judgment.
  Difference: lookup vs gate. Trigger: decode starts validating
  grammar (its miss error already covers it). Home: its docstring
  already carries the re-opener clause; no edit owed.
- R6 single-`_` key filters: [base][base] :1397 and
  `mutations/sets.py` :165 skip private keys in Meta typo guards.
  Difference: key visibility vs name grammar. Trigger: none
  (different arity of underscore, different question). Home: none.
- R7 field-surface grammar delegation: finalizer collision +
  emptiness audit only; field grammar fails at Strawberry schema
  build. No contract source requires a package-side field gate.
  Difference: delegated layer. Trigger: a spec row requiring
  early field-grammar failure (new card, not this family). Home:
  the finalize audit docstring if such a card ever lands.
- R8 ordering `-` / Django `__` / misc `startswith`: unrelated
  mechanisms (sort direction, lookup separators, `as_sql`, SQL
  comments, module paths). Difference: no name judgment at all.
  Trigger: none. Home: none.

Experiments (all read-only vs the live tree except through the
workspace copy at `dry/gqlname-f41/consolidate`):

- P1 oracle run: the 7 gate-oracle nodes green in a fresh
  workspace copy (`dry-20261001T173814-520de9`, shared unmoved).
  Execution-verified current behavior on both gates.
- P2 census run: `/tmp/f41_census.py` (AST walk, live package
  read-only) reports exactly the 2 conjunct sites
  ([base][base] :1384, [definition][definition] :269), then 3
  with a synthetic hand copy added — the specified gate logic
  discriminates. Execution-verified population + negative-control
  direction.
- P3 legality probe: `class __Foo` keeps `__name__ == '__Foo'`
  (system python3, stdlib only, zero package imports), so gate
  B's `__` arm is reachable from real consumer declarations.
  Execution-verified.

## Findings

### F1 — type-name validity conjunct (CONFIRMED, blocked-on-hunt)

- **Contract + variation.** A GraphQL type name is valid iff it is
  a non-empty string matching `_GRAPHQL_NAME_RE` with no `__`
  prefix. Varies on the grammar (character class, reserved
  prefix, arm count) only. Messages, normalization, trio order,
  and the non-`str`/empty verdicts are per-site facets (C4/C5),
  not this finding.
- **Sites + roles.** Definitions (2): [base][base] :1384 (gate A,
  declaration) and [definition][definition] :269 (gate B,
  derivation). Consumers (listed, not counted): the 9
  `graphql_type_name` reader files plus the connection-name
  derivation. Oracles (listed, independent — zero read the
  regex): gate A —
  [test-base][test-base]`::test_meta_name_rejects_invalid_graphql_names_at_type_creation`
  (`"bad-name"`), `::test_meta_name_rejects_an_empty_string`,
  `::test_meta_name_rejects_a_non_string`;
  gate B —
  [test-defrel][test-defrel]`::test_graphql_type_name_rejects_invalid_graphql_names`
  (`"bad-name"`),
  `::test_graphql_type_name_rejects_empty_name`,
  `::test_graphql_type_name_rejects_a_non_string_name`,
  `::test_graphql_type_name_falls_back_to_the_origin_class_name`.
  External oracles: graphql-core 3.2.8
  `type/assert_name.py::assert_name` (character grammar, called
  from `type/definition.py` constructors) and
  `utilities/assert_valid_name.py::is_valid_name_error` (`__`
  reservation + `assert_name` composition) — the spec rules the
  conjunct mirrors. Projection: the
  [definition][definition] centralization docstring (verified
  true) and this artifact.
- **Challenges.** C1/C2/C3 count 2 (see `### Challenges`); C4/C5
  count 1 and bound the scope. Disproof attempt: inputs (both a
  normalized non-empty `str`), outputs (both a boolean verdict),
  errors (both `ConfigurationError`, per-subject text), hooks
  (neither), reasons to change (one: the GraphQL spec) all agree;
  only timing differs (creation vs read), which is why two
  enforcement sites exist — and a time-invariant pure verdict
  must agree across both, so timing is not a second rule.
- **Owner + lifetime.** [definition][definition], via
  `def is_valid_graphql_name(name: str) -> bool` placed adjacent
  to `_GRAPHQL_NAME_RE` with a docstring stating the grammar,
  the reservation, and the both-gates-compose contract
  (principle 10). Principle 7: the module already owns the
  grammar (the predicate IS the grammar plus the reservation —
  same responsibility); both gates can import it with zero
  dependency change ([base][base] already imports the regex
  from it; [definition][definition] imports [base][base] only
  under `TYPE_CHECKING`, so no direction reverses). Reads: the
  module constant. Effects: none (pure). Lifetime: not cached
  (principle 4 — pure derivation, recomputed per call).
  Enforcement authority stays at the gates (per-subject raise).
  Rejected: `utils/strings.py` (owns case transformation —
  snake/pascal/camel — validation would be a new
  responsibility splitting grammar from rule); a new f39-style
  leaf (both gates already depend on the grammar's module —
  indirection without a second grammar consumer); status quo
  (leaves a real two-site change obligation — C1/C2/C3).
- **Migration (specified, unapplied — blocked).** (1) Add the
  predicate + grammar prose at the owner. (2) Both gates compose
  it (`if not is_valid_graphql_name(x): raise ...` with
  messages, normalization, and order untouched); record the
  per-site separation + trigger at each gate in one clause each.
  (3) Tests at the `tests/` tier (class-creation/read-time
  behavior is unreachable from a live GraphQL query, so the
  live tier cannot host them): `__`-prefix pins for BOTH gates
  (gap: no oracle pins the `__` arm today — both grammar tests
  use `"bad-name"`; the future change must add the two pins or
  the shared arm ships unguarded) plus the census gate below.
  (4) Write the R1/R2 home clauses at their owners. Net shape:
  +predicate +gate +2 pins, -1 conjunct spelling; one
  definition, two enforcement sites.
- **Distinct behavior.** Per-subject messages, `truth.text`
  normalization, trio order, the non-`str`/empty verdicts and
  their timing, the `name`-vs-class-name derivation choice, and
  every R1–R8 exclusion stay where they are.
- **Behavioral proof.** Execution-verified (P1: 7/7 oracles green
  at current bytes, run `dry-20261001T173814-520de9`): rejects
  the wrong result "the gates disagree on `"bad-name"` /
  `""` / non-`str`" (both sides pin all three shapes) and
  "gate B mis-derives the fallback" (pinned). P3 rejects
  "gate B's `__` arm is dead code". The future consolidation
  re-runs the same 7 nodes (see `## Pending execution`); the
  two `__` pins it adds reject "the shared arm regressed on
  one side". No `execution-deferred` row beyond that re-run.
- **Structural gate (specified, unapplied).** AST census over the
  package (the f39 `test_control_field_names_are_spelled_only_in_the_owner`
  shape): exactly one production spelling of
  `_GRAPHQL_NAME_RE.fullmatch` — the owner's predicate body —
  plus a both-gates-call-`is_valid_graphql_name` composition
  assertion. P2 execution-verified the census logic (2 live,
  3 with a synthetic hand copy) and its negative-control
  direction (an added spelling moves the count while behavior
  oracles stay green — the synthetic file is never imported).
  Landed-gate failability via `prove_failability.py` is owed by
  the unblock item, which runs it when the gate lands; the gate
  is not landed now because a count-1 gate is born red against
  today's count-2 tree.
- **Coupling.** Blocked-on-hunt: the predicate placement edits
  [definition][definition] hunk `@@ -247,33 +248,28 @@` and the
  gate-A call-site edit touches [base][base] hunk
  `@@ -1369,44 +1364,41 @@` (+ the :74 import in hunk
  `@@ -60,13 +60,15 @@`); all three are unattributed hunt
  truth-migration hunks on paths with no ledger row. Touching
  nothing. Unblock condition: the hunt's truth migration lands
  for both files (or the maintainer reconciles), then a fresh item applies
  this migration verbatim. No other coupling.
- **Freshness.** HEAD `dd0b6691`; WT pins match dispatch
  (`e7a62d32`/`e0ad32aa`, `e79d7129`/`ff80ef02`).
  Inspected-file fingerprints (WT `git hash-object`, 12 chars;
  full table: targets `e7a62d32d667`/`e0ad32aa5818`,
  `e79d7129ff5b`/`ff80ef028e24`; converters `97f3399ec827`;
  conf `372b23444fbb`; registry `e95c39e7df2f`; scalars
  `54f53f9b43bf`; utils/inputs `0826c9d42c6f`; finalizer
  `09f3e3278911`; mutations/sets `a1035397628a`;
  test-base `bb56c89bbcad`; test-defrel `fee20cf81674`;
  grepped-and-read bodies: walker `b71db9e03f2d`,
  nested_planner `b6ff0a0e9982`, plans `2e4332cc88dd`,
  list_field `b534ea325820`, keyset `513b54e3c319`,
  orders/inputs `2f6e1a2c60a4`, querysets `6d471bd7e6b5`,
  extensions/debug `b26a7897279b`, _graphql_core_patches
  `efadf7fb4e00`, _imports `0b3faec437b0`, strings
  `f5ce078455d9`, types/relay `a9b90a17b373`, connection
  `6c4b01f9dffa`, filters/base `9edbef64dc38`,
  filters/inputs `993f365c0c0e`, testing/relay `572f8d64fd5e`,
  inspect cmd `2e1223dcde80`, relay `63bbba0bc4d6`).
  Installed oracles: graphql-core 3.2.8,
  strawberry-graphql 0.324.0. Any fingerprint change reopens
  the finding.

No sub-rule decomposes out of this family (it is atomic: one
shared conjunct plus the per-site remainder), so no new index
row is owed beyond the tick of the existing `graphql-name-gate`
row. Rejections R1–R8 carry their contract differences and
triggers above; the two docstring homes (R1, R2) are owed to
closeout after the hunt lands, like the migration itself.

Type gates (binding, tree state, all in the workspace copy):
`basedpyright` 0 errors / 0 warnings / 0 notes
(`dry-20261001T173822-0f6706`); `check_any.py` 128 uses at 89
sites, exit 0 (`dry-20261001T173832-11af6d`);
`check_truthful_reads.py --check` 119 files, tier-1 0, errors 0
(`dry-20261001T173833-5d9b06`). Zero edits, so no new
cast/Any/suppression and no `ALLOWED_ANY` move. ruff: no `.py`
path touched, nothing to fix or format. mypy never run, never
cited. Sharded/PG cells: inapplicable by construction — both
gates are pure functions of one string with no queryset, alias,
or dialect decision reachable (Worker-2 judges).

## Defects

None. Two examined-and-cleared notes, neither a defect: (a) the
`__` arm has no oracle on either side today — production
behavior is correct by construction (same line as the pinned
regex arm) and the gap is a required test addition in the
migration above, not a bug; (b) package-side field-grammar
gating is absent with no contract source requiring it (R7) —
proposing it would be a new card for the maintainer, not a DRY defect.

## Pending execution

- `proof: uv run python scripts/workspace.py run dry/gqlname-f41/consolidate -- pytest tests/types/test_base.py::test_meta_name_rejects_invalid_graphql_names_at_type_creation tests/types/test_base.py::test_meta_name_rejects_an_empty_string tests/types/test_base.py::test_meta_name_rejects_a_non_string tests/types/test_definition_relations.py::test_graphql_type_name_rejects_invalid_graphql_names tests/types/test_definition_relations.py::test_graphql_type_name_rejects_empty_name tests/types/test_definition_relations.py::test_graphql_type_name_rejects_a_non_string_name tests/types/test_definition_relations.py::test_graphql_type_name_falls_back_to_the_origin_class_name -n0 --no-cov -q`
  — re-discharges F1 behavioral equivalence when the unblock
  item lands the migration (validated runnable 7/7 at baseline,
  run `dry-20261001T173814-520de9`).

## Judgment

CONFIRM-blocked: the GraphQL-name validity conjunct is one rule
with two independently maintained spellings (3 challenges count
2, externally pinned by graphql-core), owned by
[definition][definition] via a pure predicate — but both edits
land inside hunt truth-migration hunks, so the item ships zero
production changes with the migration, gate, and trigger-homed
rejections fully specified for the unblock item.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[base]: ../../django_strawberry_framework/types/base.py
[conf]: ../../django_strawberry_framework/conf.py
[converters]: ../../django_strawberry_framework/types/converters.py
[definition]: ../../django_strawberry_framework/types/definition.py

<!-- tests/ -->
[test-base]: ../../tests/types/test_base.py
[test-defrel]: ../../tests/types/test_definition_relations.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker-2)

Recorded before opening `## Findings` (Worker-2 step 1).
All counts below re-derived from bodies, `git` bytes, and
bounded searches — never inherited.

### Own trace (pre-Findings)

Rule: GraphQL type-name validity — a surface name is valid iff
it matches the spec character grammar AND lacks the
introspection-reserved `__` prefix.

Sites (roles mine):

- D1 — definition. [base][base]`::_validate_meta` :1384:
  `if not _GRAPHQL_NAME_RE.fullmatch(name) or
  name.startswith("__"):` — declaration gate on `Meta.name` at
  class-creation time. Raises `ConfigurationError` with a
  `Meta.name` subject message.
- D2 — definition. [definition][definition]
  `::DjangoTypeDefinition.graphql_type_name` :269: same conjunct
  on the normalized `name`-or-origin at read time. Raises
  `ConfigurationError` with a `GraphQL type name for ...`
  subject message.
- Shared token, single-owned (not a definition):
  [definition][definition] :33 `_GRAPHQL_NAME_RE` def, imported
  at [base][base] :74. Count 1.
- Consumers: 9 files read `graphql_type_name` by name
  (filters/inputs, filters/base, types/finalizer, types/relay,
  registry, inspect command, testing/relay, connection, relay).
  Zero re-gates, zero re-derivations (relay.py message use and
  registry decode-scan bodies read, not wrapped).
- Oracles: tests spell literal names (`bad-name`, `""`, `42`,
  `7`) plus message fragments (`valid GraphQL name`, `empty
  name`, one exact non-string message). Zero reads of
  `_GRAPHQL_NAME_RE` in `tests/` and in `examples/` (both
  searched independently; both empty).
- Projections: the centralization docstring on
  `graphql_type_name` (verified true — every name-or-origin
  read goes through the property) and the external grammar in
  graphql-core 3.2.8 (`type/assert_name.py::assert_name` char
  rule + `utilities/assert_valid_name.py::is_valid_name_error`
  `__` arm; ASCII classes verified byte-equal to the package
  regex).

Censuses re-derived (whole package, `muse.search` + `grep`):

- `_GRAPHQL_NAME_RE`: 4 tokens (def, import, 2 gate uses).
- `.fullmatch(`: 3 calls (2 gates + scalars BigInt over a
  disjoint grammar).
- `.startswith(`: 27 sites (regex mode; includes 1 docstring
  prose token in utils/querysets.py). `__`-judgments: the 2
  gate conjuncts, the enum sanitizer arm
  (converters.py :649, rewrite-not-reject), the settings
  introspection short-circuit (conf.py :344, Python protocol,
  no grammar). The `private_prefix` site (converters.py :609)
  is Python name-mangling (`_{enum}__`), not a name judgment.
  Rest: single-`_` key filters, ordering `-`, Django `__`
  separators, `as_sql`, SQL comments, module paths — read,
  unrelated.
- `graphql_type_name`: 9 consumer files + the def.
- Validity-helper defs (`def \w*name\w*\(` superset walked):
  zero matching a validity shape; no third gate.
- `re.compile(`: 5 sites; only `_GRAPHQL_NAME_RE` is a
  name grammar (`_NON_IDENT` sanitize, `_NODEID_STRING_RE`
  annotation shape, BigInt, routers consumer pattern).
- `is not None else`: 84 sites; the :257 surface-name
  fallback has no second spelling.

Posited changes (mine) + definition counts:

- X1 reserved-prefix arm changes: count 2. Gate A alone
  lets `Meta.name = "__x"` pass creation then fail at the
  first property read; gate B alone accepts `class __Foo`
  (legal Python — `__name__ == '__Foo'` probe-verified with
  system python3, stdlib only) while gate A rejects the
  identical string. Same string, same rule, two verdicts.
- X2 a new reserved pattern (enum `true`/`false`/`null`
  precedent generalized): count 2 — both sites add the arm
  or declaration and derivation diverge.
- X3 conjunct restatement (call shape / composition change;
  a pure regex-literal change is already count 1 and is not
  this challenge): count 2.
- X4 message reword (scope control): count 1 — subjects
  differ per site (`Category.Meta.name` vs `GraphQL type
  name for ...`); messages stay per site.
- X5 outer arms + normalization (scope control): count 1
  for the mechanism (`truth.is_instance` / `truth.text`
  single-owned, composed by name — different family) with
  per-site verdict sequencing (gate A guards raw consumer
  input at creation; gate B covers the class-name fallback
  and hand-built definitions at read — different timing and
  reachability). Only the conjunct is the family.

Owner I choose: [definition][definition] via a new pure
`is_valid_graphql_name(str) -> bool` predicate beside the
regex; both gates compose it by name. Responsibility: the
types subsystem owns type-name validity; definition.py
already owns the regex, the derivation gate, and the
GraphQL-name surface. Dependency direction agrees (base.py
already imports definition.py for the regex — the predicate
rides the same edge). Refused: utils/strings.py (body read:
transforms only — camel/snake/pascal/flatten — no validity
gate; a predicate there mismatches responsibility),
a new leaf (no cycle to break; one predicate does not
justify a module), the status quo (count stays 2), and
direct graphql-core composition (`GraphQLError` vs the
package's build-time `ConfigurationError` contract, and
`assert_valid_name` is deprecated in 3.2).

Blocked-on-hunt (my judgment, pre-Findings): BLOCKED. Both
gate lines are byte-identical context inside hunt
truth-migration hunks (base.py `@@ -1369,44 +1364,41 @@`
+ the :74 import as context in `@@ -60,13 +60,15 @@`;
definition.py `@@ -247,33 +248,28 @@` — all re-derived
from `git diff HEAD` content plus `git show HEAD:` bytes).
Context-inside-hunk still blocks: the hunk is the atomic unit
of concurrent work; a call-site edit redefines it and
overlaps hunt-rewritten neighbors (`truth.text` above,
`truth.render` below). Concurrent confirmed: `## Owned
changes` lists neither file as an owned path (the one
`types/base.py::` mention is a delegation reference inside
the inspect-command row, and that orphan half was reverted).
Predicate-alone is not a legal partial landing: a predicate
with zero composers relieves no change obligation (principle
11 dead code) while the specified census gate would still
fail on the 2 inline conjuncts — and landing it means
touching a hunt-dirty file under a touch-nothing block.
Zero legal partial landings.

### Reconciliation (post-Findings)

Read `## Findings`, `## Defects`, `## Pending execution`,
`## Judgment` after recording the trace above. Every material
claim reconciles; zero differences require resolution:

- Sites/roles/counts/owner: identical (D1/D2, token count 1,
  9 consumers, oracle independence, X1–X3/C1–C3 count 2,
  X4–X5/C4–C5 scope controls, definition.py predicate owner).
  My X-series maps 1:1 onto C1–C5 including the `class
  __Foo` reachability arm (both sides probe-verified).
- Enumeration: identical on all six instruments (4 / 3 / 27
  / 9 consumers / 0 helpers / 0 test reads), each reproduced
  by me with whole-population searches, never by sample.
  Supplementary: `re.compile(` 5 sites (only one a name
  grammar), `is not None else` 84 sites (matrix "80+"
  corroborated), 120 package `.py` files corroborated.
- R1–R8: every rejection carries a contract difference, a
  trigger, and a home (R1/R2 docstring homes owed after the
  hunt lands — both files hunt-dirty today; R5 re-opener
  clause verified already present in the registry docstring;
  R3/R4/R6/R8 no-home with a stated reason). Every cited
  body re-read at current bytes (R1 :647-652, R2 :344, R3
  scalars :95 + :53, R4 `pascalize_token` :1008 + connection
  suffix + template families, R5 decode body, R6 both
  single-`_` sites, R7 finalizer :266/:294/:306, R8 all 27
  `startswith` sites). R6/R8 "trigger: none" accepted — the
  no-plausible-merge reason is stated, not assumed.
- Matrix: all six axes discharged against the real surface.
  Axis-2 inapplicability judged sound (pure sync verdicts).
  Axis-6 field-grammar absence correctly stays a rejection
  (R7, delegated to Strawberry's schema build, trigger
  names the new-card condition) rather than a defect.
- Migration equivalence (principle 8, verified against
  bodies): De Morgan-exact verdicts, per-site messages /
  normalization / trio order / timing untouched, pure
  uncached predicate (principle 4 satisfied, no shared
  state), same `ConfigurationError` type, no query /
  transaction / cancellation surface. Inspection suffices
  (pure composition-by-name); the landed migration is
  covered by the deferred P1 re-run. No scratch test owed.
- Structural gate (specified-not-landed): sound. Population
  (exactly one production `_GRAPHQL_NAME_RE.fullmatch`
  spelling + both-gates-call assertion) pins the conjunct's
  unique marker; I re-executed `/tmp/f41_census.py`
  read-only — 2 live sites at exactly base.py:1384 +
  definition.py:269, 3 with the never-imported synthetic
  copy (`CENSUS-DISCRIMINATES`) — so the P2
  negative-control direction is independently
  execution-verified. Born-red rationale correct; landed
  failability correctly owed to the unblock item.
- Pending execution: one entry, correctly typed `proof:`.
  All 7 nodes validated to exist (test_base :243/:254/:267,
  test_defrel :480/:190/:199/:206) AND re-run by me in the
  shared tree (`-n0 --no-cov -q`): 7 passed. The entry
  discharges the unblock item's equivalence re-run, so the
  plan item reads `verified, pending execution`.
- Freshness: indexed pins re-hashed same-kind — WT
  `git hash-object` e7a62d32/e79d7129, HEAD `git rev-parse`
  e0ad32aa/ff80ef02, all match dispatch; 8/8 connected
  spot-checks match the artifact table byte-for-byte;
  HEAD `dd0b6691` unmoved; ITEM_BASELINE object exists;
  installed oracles graphql-core 3.2.8 + strawberry 0.324.0
  verified in the venv; `assert_name` callers in
  graphql-core `type/definition.py` confirmed (5 sites).
- Blocked-on-hunt: AGREE on all three prongs (hunks
  re-derived from `git diff HEAD` + `git show HEAD:` bytes;
  concurrent confirmed — neither file is a ledger-owned
  path; zero legal partial landings — predicate-alone is
  principle-11 dead code under a touch-nothing block).
  Context-line-inside-hunk still blocks: the hunk is the
  atomic concurrent-work unit and the call-site edit
  overlaps hunt-rewritten neighbors.
- Examined-and-cleared: (a) `__`-arm oracle gap correctly
  cleared — I confirm the gap is real (no `name = "__`
  test exists; both grammar tests use `"bad-name"`) and
  correctly typed (correct-by-construction behavior with a
  missing pin is not a rule-35 defect; the migration's
  2-pin step is correctly specified as required, not
  optional). (b) Field-grammar absence correctly cleared
  (R7 rejection with trigger; no contract source; the
  "possible new card" is forward-looking, not a live
  routable proposal).
- Sharded/PG inapplicable-by-construction: AGREE — both
  gates are pure functions of one string; no queryset,
  alias, or dialect decision is reachable.
- Zero-edit: item diff vs ITEM_BASELINE is the plan edit
  alone (types/, tests/, examples/ diffs all empty); every
  untracked `.py` is pre-attributed (f39 ledger rows +
  briefed hunt concurrent); the artifact is the only new
  output. No oracle rewritten.
- AGENTS.md prose: reference-style links with the full
  10-group LINK DEFINITIONS block; bare `:NN` refs allowed
  in `docs/dry/dry-*.md`; `tests/` tier with correct
  live-unreachable reasoning; no process provenance;
  banned words N/A (zero new test/production files — the
  artifact's "audit"/"Worker-2" tokens are DRY-domain and
  role language).
- Gates (all re-run by me in the shared tree): basedpyright
  0 errors / 0 warnings / 0 notes; `check_any.py` 128 uses
  at 89 sites, exit 0; `check_truthful_reads.py --check`
  119 files, tier-1 0, errors 0 — each matches the run-11
  baseline and W1's workspace-copy figures. mypy never
  run, never cited. Ruff: ∅ `.py` paths touched, vacuous;
  the artifact path itself passes `ruff check` ("No Python
  files") and `ruff format --check` (exit 0).

Defects: none. W1's zero-defect claim stands; no (Worker-2)
entry owed.

Verdict: VERIFIED. F1 CONFIRM count-2 blocked-on-hunt stands
on my independent trace; migration, gate, R1–R8, and
freshness all check out. One `proof:` entry remains, so the
plan item reads `verified, pending execution`.
