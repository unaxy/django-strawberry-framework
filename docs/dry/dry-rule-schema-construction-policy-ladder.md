# DRY review: `schema-construction-policy-ladder`

Status: verified
Run: 0.0.15 2026-10-01-9

## System trace

The rule is the deployment-policy resolution ladder: a schema-construction
policy resolves from three ordered sources (explicit constructor argument,
deployment setting, fail-closed package default), accepts an instance or a
mapping at either override slot, canonicalizes whatever wins into a private
validated object, and rejects anything else with a typed error naming the
accepted shapes and, for mappings, the valid key vocabulary. The ladder runs
once, at `DjangoSchema` construction; everything downstream (arming, per-field
reads, masking) consumes already-resolved objects and has its own read
precedence, which this trace adjudicates as same-rule or distinct-rule below.

Traced at HEAD bytes (`5c3496e0`) through `git show HEAD:<path>` and
`git grep ... HEAD`. That instrument choice is load-bearing, not stylistic:
all four indexed files are dirty in the working tree with concurrent
`describe_value` -> `truth.*` + lazy-proxy rewrites (144 insertions / 190
deletions across the four, none of it in the plan's `## Owned changes`
ledger), so working-tree reads do not show the bytes this verdict is about.
Every line cited below is a HEAD line; every fingerprint is a HEAD blob.

Sites found, by role:

- Definition (1): `django_strawberry_framework/utils/policies.py::resolve_policy`
  (`:110`), with its wording helper `_article` (`:105`). The whole ladder:
  explicit-instance arm (`:140`), setting-or-absent selection (`:142`),
  no-override canonicalization (`:143`), setting-slot instance arm (`:145`),
  non-mapping rejection (`:152`), materialize-once (`:166`), key-type guard
  (`:178`), unknown-key vocabulary rejection (`:183`), mapping application
  (`:190`). Composes `canonical_policy` by name at three call sites.
- Declarations (2, principle 1 records, not definitions):
  `django_strawberry_framework/error_policy.py::resolve_error_policy` (`:151`)
  and `django_strawberry_framework/resource_policy.py::resolve_resource_policy`
  (`:466`). Each passes exactly five bindings
  (`policy_cls`, `default`, `read_setting`, `display_name`, `unit`) and adds no
  rung, no shape, no message of its own; both docstrings state the twin shape
  is deliberate.
- Rung suppliers (2): `django_strawberry_framework/conf.py::resource_policy_setting`
  (`:583`) and `::error_policy_setting` (`:595`). Thin readers, no validation;
  their docstrings name the resolvers as the validating owners. Each has
  exactly one production caller (its twin's `read_setting=` binding).
- Construction consumer (1): `DjangoSchema.__init__`
  (`django_strawberry_framework/schema.py:839` for resource, `:842` for
  error), settling the `_SchemaEnforcement` record (`:861`). Fed by the
  entry-folding adapter `_consumer_extension_entries` (`:1295`), which picks
  between two spellings of the explicit slot (kwarg vs extension entry,
  mutual-exclusion refusal) and hands the winner to the ladder's explicit arm.
- Operation/request-time read ladders (excluded as distinct rules, R1-R5):
  `extensions/resource_policy.py::_resolved_policy` (`:1554`),
  `resource_policy.py::policy_from_info` (`:880`),
  `extensions/error_policy.py::schema_error_policy` (`:290`),
  `schema.py::_enforcement` (`:549`) over `_FALLBACK_ENFORCEMENT` (`:546`),
  and the degrade floors `extensions/error_policy.py::_degraded` (`:191`,
  `:223`) and `schema.py::_masked_return` (`:1169` floor line).
- Adjacent ladders and resolvers (excluded, R6-R13, R16):
  `views.py::_resolved_max_request_body_bytes` (`:178`),
  `optimizer/nested_fetch.py::resolve_strategy` (`:436`),
  `testing/client.py` endpoint selection (`:134`),
  `consumers.py::resolved_revalidation_window` (`:595`),
  `utils/querysets.py::_SealPolicy` (`:2931`),
  `filters/sets.py::_PACKAGE_POLICY_BASELINE` (`:425`),
  `utils/connections.py::resolve_relay_max_results` (`:791`),
  `utils/permissions.py::resolve_auth_aliases` (`:297`) plus the remaining
  `resolve_*` census (subjects enumerated under the matrix).
- Sibling-family seams (boundary notes, R14-R15, not verdicts on those
  items): `canonical_policy` / `copy_policy` (owned by indexed sibling
  `policy-authority-isolation`) and the mapping-hardening steps
  (materialize-once, key-type guard; precedent shared with
  `conf.py::upstream_patches_enabled`, owned by indexed sibling
  `hostile-mapping-hardening`).
- Oracles: `tests/utils/test_policies.py` (12 tests against a probe policy,
  directly at the owner), `tests/test_error_policy.py` (`:285`, `:290`
  article pins), `tests/test_resource_policy.py` (`:354`, `:359` article
  pins), live `examples/fakeshop/test_query/test_error_policy_api.py` and
  `test_resource_policy_api.py` (wire wording end to end).
- Projections: the `utils/policies.py` module docstring (ladder prose),
  the `DjangoSchema` class docstring accepted-shape paragraphs
  (`schema.py:774`, `:786`), the `RESOURCE_POLICY_KEY` / `ERROR_POLICY_KEY`
  lines (`conf.py:149`, `:159`), the one GLOSSARY narrowing line, and
  historical spec-047 / spec-048.

Connected behavior examined and kept out: the narrowing derivation
(`ResourcePolicy.narrowed`, `effective_bound`), the seal machinery, the
optimizer strategy registry, the test-client transports, the websocket
revalidation window, the django-filter table anchor, and the auth-alias
derivation. Each is named under the matrix with the reason it is not this
rule.

## Verification

### Matrix

1. Cross-flavor policy mirroring. Searched, complete. The importer census
   for the shared body is exact: `resolve_policy` is imported by exactly the
   two flavor resolvers plus the owner-tier test (`tests/utils/test_policies.py:24`);
   the `resolve_*_policy` def census is exactly the two twins; the
   `_PACKAGE_*` census is exactly the two canonical copies; the `DEFAULT_*`
   census is exactly the two templates (re-exported once each from the root).
   Policy-class census: `ErrorPolicy`, `ResourcePolicy` (deployment flavors,
   both on the ladder), `_SealPolicy` (internal ORM seal options, R9),
   `_NormalizedPolicyEntry` (django-filter anchor member, R10). Every other
   setting with a constructor/setting/default shape was read at its owner and
   excluded on contract: views scalar cap (R6), strategy selection (R7),
   test endpoint (R8), revalidation window (R11), relay cap (R12). The full
   `resolve_*` def census at HEAD is 16 names; the nine outside this
   paragraph resolve non-policy subjects (auth aliases, write alias, form /
   serializer / set fields, serializer specs, globalid targets, fragment
   visits, meta models) and share only the verb (R16).
2. Sync/async twins. Ruled inapplicable with reason. Resolution runs once at
   schema construction, which is not execution-colored; there is no async
   twin of the ladder and no await boundary inside it. The enforcement reads
   are uncolored sync functions called from both colors, and the one colored
   enforcement pair (`bounded_rows` / `bounded_rows_async`) already shares
   its policy read through `_raw_list_bound` (single site, read, not
   re-verdict here).
3. Derived rather than repeated knowledge. Searched. The valid-key vocabulary
   (`{field.name for field in fields(...)}`) appears in the ladder's
   unknown-key step and in `ResourcePolicy.narrowed`'s name guard: same
   stdlib spelling, different contracts (R13, excluded). The indefinite
   article is derived once (`_article`, one def, one call site); the only
   other article spellings in reach are caller-spelled literals and the
   oracle pins, which must spell the wording to check it. `display_name` /
   `unit` are threaded parameters, not re-derived. The materialize-once and
   key-guard steps share precedent wording with `conf.py`, which is the
   sibling mapping-hardening family's subject (R14, boundary only).
4. Inverse / round-trip pairs. Ruled inapplicable with reason. The ladder has
   no inverse: a resolved policy is never serialized back to a mapping, the
   `DEFAULT_*` templates are starting values rather than encodings, and
   `canonical_policy` / `copy_policy` are both object-to-object with no
   decode half.
5. Contracts restated in another medium. Searched. Five oracle files (three
   package tiers plus two live wire tiers) pin precedence, canonicalization,
   both rejections, and the article; all read the production behavior, none
   is read by it. Projections (module docstrings, key comments, one GLOSSARY
   line, two historical specs) describe; none owns. No medium carries a
   second ladder.
6. Enforcement by omission. Enumerated the deployment-configurable surface:
   `RESOURCE_POLICY` / `ERROR_POLICY` (both through the one body),
   `MAX_REQUEST_BODY_BYTES` (R6), `NESTED_CONNECTION_STRATEGY` (R7),
   `TESTING_ENDPOINT` (R8), `APPLY_UPSTREAM_PATCHES` (bool/mapping gate,
   sibling mapping family), `SINGLE_PARENT_FAST_PATH` / `HIDE_FLAT_FILTERS` /
   `RELAY_GLOBALID_STRATEGY` (scalar flags read once where their domain
   lives; no contract source requires ladder treatment, and none accepts an
   instance-or-mapping). No third dataclass-policy flavor exists (class
   census under axis 1), and no site resolves a policy without the ladder:
   the only `RESOURCE_POLICY` / `ERROR_POLICY` setting readers are the two
   `read_setting` bindings, and the only mapping-to-policy constructions are
   the `policy_cls(**...)` applications inside the shared body plus the two
   no-argument `DEFAULT_*` templates. No omission, no defect.

### Enumeration

Instrument: `git grep` over HEAD blobs across all 117 package `.py` files,
plus full HEAD reads of the four indexed files and region reads of every
file a hit implicates. Populations censused, not sampled: `resolve_policy`
importers (3: two twins + owner test), `resolve_*_policy` defs (2),
`_PACKAGE_*` sites (2 defs + 7 read sites, each read classified below),
`DEFAULT_*` sites (2 defs + 1 re-export pair), `ErrorPolicy(`/`ResourcePolicy(`
constructions (2 templates + 2 docstring examples), `resolve_*` defs (16),
policy-class defs (4, one a name collision), `or a mapping of` producers
(1 code site + docstring/comment projections + the unrelated
`APPLY_UPSTREAM_PATCHES` message). Every member lands in F1, an R-exclusion,
or a sibling-boundary note; nothing is unassigned.

### Challenges

Each challenge posits a change on one of the ladder's variation axes and
counts authoritative definitions that must move. Consumers, oracles, and
projections that also move are listed, never counted.

- C1 (precedence axis): the setting outranks the explicit argument. Moves:
  `resolve_policy` (`:140`-`:144` arm order) = 1. Twins unchanged (they bind
  slots, not order); construction call sites unchanged (they fill the
  explicit slot); `_resolved_policy`, `policy_from_info`,
  `schema_error_policy` unchanged (they order resolved objects / runtime
  authorities, not configuration sources). Oracles move (precedence pins);
  the module docstring and twin docstrings move as projections.
- C2 (accepted-shape axis): instances behind the setting slot are rejected
  instead of canonicalized (or a third spelling is admitted). Moves:
  `resolve_policy` (`:145` arm) = 1. Same non-movers as C1; the comment at
  `:146` explaining the current acceptance moves with the body. Oracles move
  (the setting-slot instance test); projections move.
- C3 (rejection/vocabulary axis): the unknown-key rejection gains
  per-key reasons, or the non-mapping message changes shape. Moves:
  `resolve_policy` (`:152` / `:183` arms, plus `_article` if the grammar
  moves) = 1. `narrowed`'s name guard does not move (different message,
  different trigger: narrowing vs construction). `upstream_patches_enabled`
  does not move (different subject's message). Oracles move (wording pins
  including the live wire tiers); schema class-docstring shape paragraphs
  move as projections.
- C4 (canonicalization axis): the no-override path returns the shared
  default instead of a private duplicate. Moves: `resolve_policy` (`:143`
  arm) = 1. The twins do not move (they hand in `default`, they do not copy
  it); `canonical_policy` itself does not move (the change is whether the
  ladder calls it on that path). Proves the ladder owns the call discipline
  while the sibling family owns the copy mechanics. Oracle moves (the
  no-source duplicate test).
- C5 (enforcement-separation control): arming precedence flips so the
  schema's policy outranks an extension's explicit policy. Moves:
  `_resolved_policy` alone = 1, and `resolve_policy` does not move. The
  control establishes the exclusion: a change to the operation-time ladder
  touches none of the construction ladder, and C1-C4 touch none of the
  operation-time ladder. Same separation holds for `policy_from_info`
  (authority order), `schema_error_policy` (attribute admission), and
  `_enforcement` (record retrieval): each answers a change the others do
  not move for.

All counts are 1. No posited change moves two definitions.

## Findings

### F1: the construction ladder is single-owned at `resolve_policy`

- Contract + variation: one precedence (explicit > setting > default), two
  accepted shapes per override slot (instance, mapping), canonicalization of
  whatever wins including the no-override path, two typed rejections (shape,
  vocabulary). Varies on precedence order, accepted shapes, rejection
  wording, and call discipline toward the copy mechanics.
- Sites + roles: the definition (`utils/policies.py:110`); two declaration
  twins (principle 1: five bindings each, zero added behavior); two thin
  setting readers (rung suppliers); one construction consumer (both call
  sites) fed by one entry-folding adapter; five oracle files; eight
  projection sites. The enforcement read ladders are excluded (R1-R5), not
  counted: this finding's challenges move none of them and their control
  moves none of it.
- Challenges: C1-C4 above, each count 1; C5 is the separation control.
- Owner + lifetime: `utils/policies.py::resolve_policy`, by responsibility
  (principle 7): both flavor resolvers already delegate to it, it is the
  narrowest module both flavors plus the owner-tier test can import without
  reversing a dependency (flavor modules import it; it imports only
  exceptions), and it holds no state, so no principle-4 lifetime fields are
  owed. Re-derives (not inherits) the index row's owner candidate: the
  census admits no other candidate with the ladder's contract.
- Migration: none. There is no former definition to re-point; the twins are
  already declarations composing by name (principle 6).
- Distinct behavior: the enforcement read precedences stay where they are
  (R1-R5); the copy mechanics stay with the sibling isolation family (R15);
  the mapping-consumption hardening stays available to the sibling mapping
  family (R14).
- Behavioral proof: static-reviewed. A zero-edit single-ownership verdict
  owes no equivalence proof because nothing moves; the evidence is the
  census (importers 3, defs 2+1, constructions 2+body, wording producers 1)
  plus the five challenges. The oracles that would catch a second ladder
  already exist in-tree (probe-tier precedence/shape/vocabulary pins plus
  per-flavor article pins plus two live wire tiers) and are cited, not
  re-run: executing them can only confirm the suite is green, which proves
  nothing about definition count.
- Structural gate: none owed. The realistic bypass is a third flavor
  resolving without the body, and that bypass is already uneconomical: the
  shared body is the only mapping-to-policy constructor, the only wording
  producer, and the only canonicalization caller on the construction path,
  so a bypass must restate all three to behave the same, at which point the
  flavor-tier oracles (which pin the shared wording verbatim) fail. A
  bespoke existence test per helper is explicitly not the shape (DRY.md
  finding record); the wording pins are the gate that already exists.
- Coupling: none. Zero edits, zero dependencies.
- Freshness: HEAD `5c3496e0`. Blobs: `utils/policies.py 4b180e2b`,
  `error_policy.py 7fc87d9f`, `resource_policy.py c554a679`,
  `conf.py eccddc21`, `schema.py 0dad535d`,
  `extensions/error_policy.py 449b8f8a`,
  `extensions/resource_policy.py 11e2a9ac`, `views.py d627d5dd`,
  `consumers.py 06074640`, `optimizer/nested_fetch.py bedaa76e`,
  `testing/client.py 690a4c70`, `utils/connections.py 5bf8f5fa`,
  `utils/querysets.py 69ac3ea3`, `utils/permissions.py 0e13b869`,
  `filters/sets.py 85699ac2`, `list_field.py 37d2e6dc`,
  `__init__.py 8b165672`, `tests/utils/test_policies.py 57ab2170`,
  `tests/test_error_policy.py 58129ec2`,
  `tests/test_resource_policy.py 7e8fb465`, `docs/GLOSSARY.md 95cd34f3`,
  `test_error_policy_api.py 20cf3807`,
  `test_resource_policy_api.py ae7bef60` (full ids in the verification
  notes; prefixes above are unambiguous over this repo's object store).
  Searched population: all 117 package `.py` blobs at HEAD plus the oracle
  and projection files named. Any fingerprint change reopens.

Verdict on F1: CONFIRM single ownership; zero-edit.

### Rejections and exclusions (contract difference + trigger each)

R1. `extensions/resource_policy.py::_resolved_policy` (`:1554`):
explicit extension policy > schema policy > package default, consulted once
per operation to arm the budget. Difference: selects among already-resolved
objects at operation time; no setting rung, no mapping arm, no validation,
fail-closed `isinstance` gate instead of fail-loud rejection (C5 control).
Suggested home: indexed sibling `policy-authority-isolation`, for that item
to confirm or refuse. Trigger: the extension starts accepting raw
mappings or settings at arming time.

R2. `resource_policy.py::policy_from_info` (`:880`): armed budget >
published mirror (exact-type gate) > package baseline copy, read per
request. Difference: orders runtime authorities (ContextVar, request
context), never raises, and its middle rung admits only an exact
`ResourcePolicy`. Suggested home: same sibling. Trigger: construction
precedence starts varying per request (impossible while construction is
process-lived; the trigger documents why the exclusion is stable).

R3. `extensions/error_policy.py::schema_error_policy` (`:290`): schema
attribute (exception-contained read, `isinstance` gate) > package default.
Difference: attribute admission with hostile-schema containment for a
hand-wired plain `strawberry.Schema`; no configuration semantics at all.
Suggested home: same sibling. Trigger: as R1.

R4. `schema.py::_enforcement` (`:549`) over `_FALLBACK_ENFORCEMENT` (`:546`):
settled record > constant fallback record. Difference: retrieval keyed by
schema identity for schemas that never completed `__init__`; answers a
record, resolves nothing. Suggested home: same sibling. Trigger: the
fallback starts resolving configuration instead of answering a constant.

R5. Degrade floors: `extensions/error_policy.py::_degraded` (`:191`) and
`schema.py::_masked_return` (`:1169` floor line). Difference: single-string
publish floors under failure (policy message, else package message), not
precedence over sources. Suggested home: same sibling. Trigger: a floor
starts selecting among policies.

R6. `views.py::_resolved_max_request_body_bytes` (`:178`): constructor >
setting > default over a scalar int with None-as-DISABLE at the setting
rung. Difference: scalar byte-cap domain with a disable spelling the policy
ladder has no analogue for (absent means default, never disabled); no
instance/mapping duality, no canonicalization, per-mount rather than
per-schema. Converges with the prior File `utils/policies.py`
None-as-DISABLE rejection on fresh HEAD-byte evidence. Trigger: the cap
becomes a dataclass policy with instance/mapping spellings.

R7. `optimizer/nested_fetch.py::resolve_strategy` (`:436`): name/instance
selection over a strategy registry. Difference: selection, not
normalization: returns singletons and consumer instances as-is, no
default-object canonicalization, no mapping arm, registry-membership
vocabulary instead of field-name vocabulary. Converges with the prior
selection-vs-policy rejection on fresh evidence. Trigger: strategies
become validated dataclass policies resolved from mappings.

R8. `testing/client.py` endpoint selection (`:134`): per-call url >
constructor path > `GRAPHQL_URL` > `TESTING_ENDPOINT` > default string.
Difference: string URL selection on a test-only surface; no validation, no
mapping arm, no canonicalization. Converges with the prior ladder-vs-ladder
rejection on fresh evidence. Trigger: the endpoint gains validated
structure.

R9. `utils/querysets.py::_SealPolicy` (`:2931`) and its per-surface
constants. Difference: internal ORM option records (row-type, slice,
combinator, alias, evaluatedness axes) with no deployment configuration, no
setting rung, no mapping arm, and no consumer-visible spelling. Converges
with the prior seal-defaults rejection on fresh evidence. Trigger: seal
options become deployment-configurable.

R10. `filters/sets.py::_PACKAGE_POLICY_BASELINE` (`:425`) over
`_NormalizedPolicyEntry` (`:391`). Difference: name collision only; a
frozen django-filter `FILTER_DEFAULTS` ownership anchor compared by value,
sharing the token "policy" and the `_PACKAGE_` prefix with none of the
mechanism. Trigger: none; different mechanism entirely.

R11. `consumers.py::resolved_revalidation_window` (`:595`). Difference: a
scalar validator (exact int/float, finite, non-negative) with no precedence
at all; "shaped after" the views ladder in its own docstring, which routes
it to R6's home, not here. Trigger: none while it takes one value and
returns one number.

R12. `utils/connections.py::resolve_relay_max_results` (`:791`): explicit
cap > schema-config cap > Strawberry default, then the request policy as a
ceiling. Difference: the precedence half mirrors upstream
`SliceMetadata` pagination semantics (its owner), and the policy half
composes `policy_from_info` + `effective_bound` by name rather than
restating either. A consumer of the enforcement side, not a second
construction ladder. Trigger: the cap precedence stops mirroring
`SliceMetadata` while the policy ceiling stops composing by name.

R13. Field-name-set derivation: the ladder's vocabulary step
(`utils/policies.py:181`) vs `ResourcePolicy.narrowed`'s name guard
(`resource_policy.py:414`). Difference: same stdlib spelling
(`{field.name for field in fields(...)}`), different contracts
(unknown-key vocabulary at construction vs narrowing-name guard at
derivation); the one-line composition is not a rule, and extracting it
would couple two call sites whose reasons to change are independent (C3
moves one, never the other). Converges with the prior derivation rejection
on fresh evidence. Trigger: the vocabulary derivation gains
policy-specific logic both sites need.

R14. Mapping-hardening steps (materialize-once `:166`, key-type guard
`:178`) vs `conf.py::upstream_patches_enabled` (`:371`) and the other
hardened mapping readers. Boundary note, not a verdict: the shared
consumption hardening is the indexed sibling `hostile-mapping-hardening`'s
subject (it already indexes `utils/policies.py`); what stays in THIS
family regardless of that item's outcome is the vocabulary rejection
itself (valid names + `display_name`/`unit` wording), which is
ladder-specific. No trigger owed here; that item sets its own.

R15. `canonical_policy` (`utils/policies.py:63`) and `copy_policy` (`:39`).
Boundary note, not a verdict: the copy mechanics are the indexed sibling
`policy-authority-isolation`'s subject (it names both as its owner); this
family's ladder composes `canonical_policy` by name at three call sites
(principle 6), and C4 proves the ladder owns the call discipline while the
sibling owns the mechanics. No trigger owed here; that item sets its own.

R16. The remaining `resolve_*` census (`resolve_auth_aliases`,
`resolve_write_alias`, the six field/spec resolvers, `resolve_meta_model`,
`resolve_backed_model_or_raise`, `resolve_globalid_target_definition`,
`resolve_unvisited_fragment`, `resolve_optional_fields`). Difference: each
resolves a non-policy subject (aliases, fields, models, fragments); the
`resolve_` verb is not the mechanism. Trigger: none.

## Defects

None found. The trace read for contract at every site above; no docstring
contradicts its body on the ladder's behavior, no flavor lacks a guard its
contract requires (axis 6 enumerates the full configurable surface), and no
layering claim is contradicted by the imports (flavors import the shared
body; the shared body imports only exceptions; setting readers are called
only through the `read_setting` bindings).

## Pending execution

None. The verdict is static-decidable (definition count from source
census plus challenges); no equivalence proof is owed because nothing
moves, and no gate is relied on beyond the wording pins already in-tree.
The `--cell sharded` / `--cell pg` cells are inapplicable by construction:
the finding touches no database, alias, or dialect decision (pure
construction-time normalization plus source census). No `proof:` or `gate:`
entry is owed.

## Judgment

The schema-construction policy ladder is already one rule in one body:
`utils/policies.py::resolve_policy` holds the precedence, the shapes, the
canonicalization discipline, and both rejections; the two flavor resolvers
are five-binding declarations; the settings supply one rung each; the
schema calls both resolvers once at construction. Everything that looks
like a second ladder is either an operation/request-time read over
resolved objects and runtime authorities (R1-R5, suggested to the
isolation sibling), a scalar/selection/name-collision neighbor (R6-R13,
R16), or a named seam into an indexed sibling family (R14-R15). CONFIRM
single ownership, zero edits, no new index rows owed.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker-2)

### Worker-2 independent trace (recorded before opening `## Findings`)

Disclosure: a package-wide `resolve_*` census grep surfaced artifact
fragments (trace lines, matrix lines, challenge sketches, the F1 header,
the Judgment paragraph) before this trace was written. The trace below
derives from my own HEAD-byte reads, not from those fragments; the
reconciliation section names every point of agreement or difference.

Target (HEAD `5c3496e0` bytes; WT carries concurrent truth/lazy-migration
dirt on all four files, attributed by content, never relied on):

- `django_strawberry_framework/utils/policies.py` HEAD `4b180e2b`
  (190 lines)
- `django_strawberry_framework/error_policy.py` HEAD `7fc87d9f`
- `django_strawberry_framework/resource_policy.py` HEAD `c554a679`
- `django_strawberry_framework/conf.py` HEAD `eccddc21`

Sites and roles (my census, `git grep` at HEAD over the package):

- Definition (exactly 1):
  `django_strawberry_framework/utils/policies.py::resolve_policy`
  (`:110`-`:190`). Holds the precedence (explicit `:140`, setting-or-absent
  selection `:142`, default `:143`-`:144`), the accepted shapes (instance
  from either slot `:140`-`:141` + `:145`-`:151`, mapping arm
  `:152`-`:190`), the canonicalization discipline (three
  `canonical_policy` calls, one per winning rung), the materialize-once
  consumption (`:166`-`:173` with the iteration-failure wrap), the key-type
  guard (`:178`-`:182`), and both rejections (non-mapping `:153`-`:157`
  with the `_article`-derived grammar, unknown-key `:185`-`:189` naming
  the `fields()`-derived vocabulary). Wording helper
  `::_article` (`:105`) is its private sub-body, same definition.
- Declarations (2, principle-1 records, not definitions):
  `django_strawberry_framework/error_policy.py::resolve_error_policy`
  (`:151`-`:174`) and
  `django_strawberry_framework/resource_policy.py::resolve_resource_policy`
  (`:466`-`:495`). Each is a docstring plus one `resolve_policy(` call
  binding exactly five names (`policy_cls`, `default`, `read_setting`,
  `display_name`, `unit`); neither adds a branch, a rung, or a message.
- Setting rung (2 thin readers, one rung each):
  `django_strawberry_framework/conf.py::resource_policy_setting` (`:583`)
  and `::error_policy_setting` (`:595`), each one
  `getattr(settings, KEY, None)` line. `RESOURCE_POLICY_KEY` /
  `ERROR_POLICY_KEY` are read nowhere else (census: def + one read each).
- Consumers: `django_strawberry_framework/schema.py::DjangoSchema.__init__`
  calls each flavor resolver exactly once (`:839`, `:842`); the resource
  call fills the explicit slot with the extension-entry fold
  (`resource_policy if declared_resource is None else declared_resource`)
  under the double-declaration refusal (`:831`-`:838`) — slot-filling,
  not a second ladder.
- Isolation consumers (resolved-object reads, not ladder sites):
  `canonical_policy` (3 calls inside `resolve_policy`, 2 `_PACKAGE_*`
  import-time defs, 1 per-operation `_operation_policy`);
  `copy_policy` (schema copy-per-read properties, mirror publish,
  `policy_from_info`); `_PACKAGE_*` fallback readers
  (`_FALLBACK_ENFORCEMENT`, `policy_from_info` miss, extension degrades,
  `schema.py::_masked_return` floor).
- Oracles: `tests/utils/test_policies.py` (imports the driver itself plus
  both twins; probe policy; independent literals such as
  `"Unknown probe-policy bound(s): wirth"`), `tests/test_error_policy.py`
  + `tests/test_resource_policy.py` (flavor tiers, `is not` pins, message
  matches), `examples/fakeshop/test_query/test_error_policy_api.py` +
  `test_resource_policy_api.py` (live wire wording, both present at HEAD).
  No oracle enumerates the owner to build its expectation.
- Projections: module/function docstrings stating the ladder.

Challenges (definition counts; `resolve_policy` = RP):

- W2-C1 third policy flavor: a new flavor declares its five bindings;
  RP is generic over `policy_cls`/`fields()` and the wording seeds, so it
  does not move. Count 0 (1 new declaration, not a rule definition).
- W2-C2 new rung between setting and default (e.g. an env-var override):
  arm order + selection move in RP alone; twins bind slots, not order;
  readers unchanged. Count 1.
- W2-C3 fail-open (unknown keys ignored instead of rejected): the
  `:185`-`:189` arm drops in RP alone. Count 1.
- W2-C4 precedence flip (setting outranks explicit): `:140`-`:142` arm
  order moves in RP alone. Count 1.
- W2-C5 setting-slot instances rejected: the `:145` arm moves in RP
  alone (plus its `:146` comment, same body). Count 1.
- W2-C6 rejection rewording (either message, or the article grammar):
  RP alone (`:153`-`:157` / `:185`-`:189` / `_article`). Count 1.
- W2-C7 no-override path returns the shared default: `:143`-`:144` moves
  in RP alone; `canonical_policy` itself does not move. Count 1.
- W2-C8 new bound/option on a flavor: 0 on the ladder (vocabulary derives
  from `fields(policy_cls)`); the flavor `__post_init__` + oracles move.
- W2-C9 separation control: flip the operation-time precedence in
  `extensions/resource_policy.py::_resolved_policy` (explicit > schema >
  package): RP does not move; flip any W2-C2..C7 change: `_resolved_policy`
  does not move. Two ladders, one exclusion.

Owner I would choose: `utils/policies.py::resolve_policy` (principle 7).
Both flavors already delegate to it; it is the narrowest module both
flavor modules plus the owner-tier test import downward with no reversal.
The schema cannot own it (flavors do not import the schema; ownership
there reverses the dependency). Either flavor resolver cannot own it
(the other would import a sibling flavor for its machinery, which
principle 7 forbids). `conf.py` cannot own it (thin readers with no
domain vocabulary; ownership there couples settings to policy classes).

Six-axis matrix (my discharge against the real surface):

1. Cross-flavor mirroring — searched. Def census is exactly 3 (1 driver
   + 2 twins); `resolve_policy` production importers are exactly the two
   twins; `read_setting` has 1 call site + 2 bindings. No third flavor.
2. Sync/async twins — inapplicable by construction: pure construction-time
   normalization, no I/O, no awaits; no async twin exists.
3. Derived knowledge — searched. Both `known` sets derive from `fields()`
   (RP over `policy_cls`, `ResourcePolicy.narrowed` over `self`); defaults
   derive from dataclass field defaults via construction; keys read from
   `*_KEY` constants once each. W2-C8 moves 0 definitions.
4. Round-trip pairs — inapplicable: one-way normalization, no
   encode/decode pair exists on this surface.
5. Contracts in another medium — searched. Oracles pin behavior with
   independent literals; projections (docstrings, specs 047/048) describe.
   No oracle reads the owner to build its expectation.
6. Enforcement by omission — searched. Exactly 2 policy flavors exist;
   both resolve through the driver; the schema calls both once
   (`schema.py:839`, `:842`); no flavor resolves elsewhere. No gap.

Neighbor exclusions I derived (each with its contract difference):

- N1 `views.py::_resolved_max_request_body_bytes`: scalar int ladder whose
  setting rung reads `None` as DISABLE while RP reads `None` as absent at
  both rungs; different subject, different sentinel contract.
- N2 `optimizer/nested_fetch.py::resolve_strategy`: name/instance
  selection returning shared singletons by design vs RP returning a
  private policy by design; opposite sharing contracts.
- N3 `extensions/resource_policy.py::_resolved_policy`: operation-time
  precedence over resolved objects, no mapping arm, no canonicalization,
  no rejections; different timing and mechanism (W2-C9 control).
- N4 `conf.py::upstream_patches_enabled` mapping arm: bool-or-mapping gate
  over a fixed four-name open world vs RP's dataclass-field closed world
  with `__post_init__` domain validation + canonicalization.
- N5 `ResourcePolicy.narrowed` + `effective_bound`: request-time
  narrowing-only derivation with its own widening refusal; different
  trigger (per-field tightening vs construction normalization).
- N6 `canonical_policy` / `copy_policy` / `_PACKAGE_*` / `policy_from_info`
  / `begin_resource_budget` / extension degrades: authority isolation over
  resolved objects; the construction ladder feeds them, never duplicates
  them.
- N7 flavor `__post_init__` domain gates + `DEFAULT_*` templates: per-flavor
  value vocabulary; RP is generic over it (W2-C8).
- N8 `exceptions.py::describe_value` tails: consumed renderer, unchanged by
  every W2-C challenge; not a ladder definition.

### Reconciliation with `## Findings` (read only after the trace above)

Method: every W1 census re-derived with my own `git grep`/`git show HEAD`
instruments; every cited line re-read; all 23 freshness prefixes
re-hashed. Agreements first, then every difference explicitly.

Adjudication, one line per claim:

- F1 count-1 + owner: CONFIRM. My W2-C2..C7 match C1..C4 challenge for
  challenge (precedence, shapes, wording, call discipline), each count 1;
  my W2-C9 matches the C5 control; my W2-C1 (third flavor, count 0) and
  W2-C8 (new bound, count 0) extend coverage W1 sketches in prose. Owner
  re-derived identically with the same principle-7 eliminations (schema
  reverses, sibling flavor forbidden, conf has no vocabulary). The
  stressed changes from dispatch (third flavor 0, new rung 1, fail-open 1)
  force no count > 1 with a landable owner: no consolidation exists.
- R1-R5 (operation/request-time reads): each contract difference verified
  at HEAD (R1 arming selection + C5 control; R2 ContextVar/mirror/baseline
  authority order, never raises; R3 hostile-schema containment; R4
  identity-keyed retrieval answering a constant record; R5 single-string
  publish floors). Triggers adequate (R2's documents its own stability).
  Sibling suggestions correctly homed: all five sites live in files the
  indexed `policy-authority-isolation` row already covers, and W1 phrases
  them as suggestions "for that item to confirm or refuse" — recorded
  here with differences + triggers, not silently dropped.
- R6: CONFIRM (scalar ladder, None-as-DISABLE at the setting rung, read at
  `views.py:178`-`:230`; matches my N1).
- R7: CONFIRM (selection returning singletons as-is vs private-policy
  construction; opposite sharing contracts; matches my N2).
- R8: CONFIRM (test-only URL-string selection at `testing/client.py:134`
  + the conf-docstring ladder; no validation, different subject).
- R9: CONFIRM (`_SealPolicy` region has no settings/Mapping/deployment
  surface; internal ORM options).
- R10: CONFIRM (`_PACKAGE_POLICY_BASELINE` `:425` over the
  FILTER_DEFAULTS anchor `:391`; token collision only).
- R11: CONFIRM (scalar validator + "Shaped after ..." routing to R6).
- R12: CONFIRM (precedence mirrors `SliceMetadata`; policy half composes
  `effective_bound(policy_from_info(info).max_page_size, cap)` by name).
- R13: CONFIRM on difference + trigger (construction vocabulary vs
  narrowing guard; C3/W2-C6 moves one, never the other); citation slip D1
  below, verdict-neutral.
- R14/R15 seam rows: both name REAL indexed rows
  (`hostile-mapping-hardening` indexes `utils/policies.py`;
  `policy-authority-isolation` owns `canonical_policy` + `copy_policy`).
  Boundary-note framing correct (no verdict on those items); the reserved
  claims (vocabulary rejection stays here; C4 call-discipline split)
  verified — my W2-C7 agrees.
- R16: CONFIRM on substance (every named subject is non-policy:
  aliases, fields, models, fragments); count-label note D4 below.
- Matrix: all six axes agree with my discharge (1/3/5/6 searched, 2/4
  inapplicable with reason). The axis-2 `_raw_list_bound` single-site
  claim verified (`:1000`, both colors call it).
- Enumeration completeness: HOLDS. Every population I censused matches
  (importers 3, defs 2+1, `_PACKAGE_*` 2 defs + 7 read sites,
  `DEFAULT_*` 2 + re-export pair, constructions 2 templates + body
  application + 2 docstring examples, policy classes 4, wording 1 code
  site). Notes D4/D5 qualify two headline labels, not the coverage.
- Freshness: 23/23 prefixes re-hash clean at HEAD `5c3496e0` (still the
  HEAD at verdict); comparable; any change reopens.
- "No new index rows owed": ENDORSED. No new family named; F1 confirms
  the existing row's owner; R1-R5 suggest to an existing row; R14/R15
  boundary-note existing rows. Worker-0 owes transcription of the
  rejections, not new rows.
- Pending execution ("None" section present): CORRECT, plain `verified`.
  No `proof:` owed: static-decidable (census + challenges), nothing
  moves, and executing the suite would prove greenness, not definition
  count. The section's presence (vs template "absent when none") is
  justified: it carries the cells reason DRY.md requires stated.
- Cells inapplicable by construction: CORRECT. Pure construction-time
  normalization + source census; no database, alias, or dialect decision.
  The live oracle tiers are cited, not executed, so no cell runs either.
- Structural gate ("none owed" + wording pins): ADEQUATE with nuance D6.
  Zero-edit shape: no `## Implementation` (grep count 0); tracked
  item diff is the plan edit alone; 4/4 WT pins match dispatch pins;
  status 460 = 194 modified + 266 untracked with the artifact untracked.
- AGENTS.md on the diff: clean. No production path touched
  (ASCII/`pragma`/provenance vacuous); artifact is per-cycle scratch
  (raw `path:NN` allowed, no style cleanup owed).
- Ruff: VACUOUS — no tracked `.py` touched (the one tracked change is
  the plan `.md` edit, not a ruff subject). No ruff run owed.
- Type gates (shared venv via `uv run`; no workspace run — nothing
  source-mutating to prove): `uv run mypy` clean (119 files),
  `uv run basedpyright` 0/0/0, `uv run python scripts/check_any.py`
  exit 0 (130 allowed `Any` at 90 sites).
- Defects: none in production. No `(Worker-2)` `## Defects` entry: the
  notes below are scratch-record accuracy, below the `## Defects` bar
  (and W1 sections stay byte-intact).

Differences from W1, each explicitly reconciled (all verdict-neutral
scratch-record notes; none spends the verdict):

- D1 R13 cites the vocabulary step as `utils/policies.py:181`; HEAD `:181`
  is the key-guard message line — the step is `:183` (`known = ...`).
  Site unambiguous (named symbol + file); difference + trigger stand.
- D2 Trace cites `_enforcement` (`:549`) / `_FALLBACK_ENFORCEMENT`
  (`:546`); actual lines are `:551` / `:545` (`:549` is blank, `:546` is
  the first arg line). Symbols unambiguous; R4 stands.
- D3 Trace attributes both degrade-floor lines to `_degraded`
  (`:191`, `:223`); `:223` is `degraded_result`, a distinct function.
  Both sites real; R5's own citations correct; exclusion stands.
- D4 `resolve_*` headline "16 names" vs 18 module-level defs at HEAD by
  my instrument. W1's own named union covers all 18 exactly (F1's 3 + R7
  + R12 + R16's 13), so enumeration completeness holds by union; only
  the headline label is off. No site unassigned, no hidden ladder.
- D5 "`or a mapping of` ... 1 code site + ... the APPLY_UPSTREAM_PATCHES
  message": conf.py carries that message at 2 raise sites (`:426`,
  `:485`, one function). Message-singular phrasing is accurate as a
  message census; conf-internal in any case, not ladder.
- D6 "The wording pins are the gate that already exists" overclaims
  slightly: wording pins gate drift, not a byte-perfect bypass copy
  (which would pass every behavior oracle, per DRY.md's own negative
  control). No mechanical bypass-gate is constructible here (the flavor
  population is open; bespoke existence tests are forbidden), and
  durable protection exists as owner prose (principle 10) + review.
  Conclusion "none owed" stands.

Verdict: `verified` (plain — no `proof:` remains, no pending execution).
Zero-edit CONFIRM of single ownership at
`utils/policies.py::resolve_policy`; R1-R16 carry contract differences +
triggers; no new index rows owed (endorsed); no defects.

