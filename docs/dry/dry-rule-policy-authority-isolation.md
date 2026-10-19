# DRY review: `policy-authority-isolation`

Status: verified
Run: 0.0.15 2026-10-01-9

## System trace

The rule is policy authority isolation: every object a bound or a masking
decision is read from is unreachable from consumer code; every policy object
handed OUT is a private duplicate; per-operation and per-request reads order
runtime authorities under per-seam containment; package fallbacks answer where
no authority was settled; degrade floors publish the policy message alone
where a seam cannot decide. Two policies (error, resource), one copy
mechanics pair, one read discipline per authority kind, one masking body over
three seams.

Traced at HEAD bytes (`5c3496e0`) through `git show HEAD:<path>` and
`git grep ... HEAD`, with HEAD-byte copies under the OS temp dir for
line-numbered reading. Seven of the eight indexed files are dirty in the
working tree with concurrent truth/lazy-migration rewrites (239 insertions /
357 deletions across the seven, none of it in the plan's `## Owned changes`
ledger, and the rewrites touch mechanism-adjacent lines: `isinstance` to
`truth.*` gates, signature reflows, one parameter rename), so working-tree
reads do not show the bytes this verdict is about. Every line cited below is
a HEAD line; every fingerprint is a HEAD blob. `utils/connections.py` is
clean at HEAD blob `5bf8f5fa`.

Sites found, by role:

- Definitions (8, each count 1):
  `django_strawberry_framework/utils/policies.py::copy_policy` (`:39`, F1)
  and `::canonical_policy` (`:63`, F2); the resource operation/request-time
  reads `resource_policy.py::_operation_policy` (`:663`),
  `::_armed_budget` (`:608`), `::policy_from_info` (`:880`),
  `::armed_resource_policy` (`:739`), `::check_deadline` (`:923`) with its
  deadline helpers (`:620`, `:820`, `:847`), the mirror
  (`:631`, `:647`, `:874`, `:118`-`:119`) and
  `extensions/resource_policy.py::_resolved_policy` (`:1554`, F3); the error
  admission read `extensions/error_policy.py::schema_error_policy` (`:290`,
  F4); the schema record `schema.py::_SchemaEnforcement` (`:465`) with its
  store (`:506`), fallback (`:545`) and retrieval (`:551`, F5); the explicit
  extension holding `extensions/resource_policy.py::_AcceptedPolicy`
  (`:1413`) with its store (`:1437`) and copy-per-read property (`:1531`,
  F6); the masking application `extensions/error_policy.py::
  mask_execution_result` (`:311`) with its gates (`:238`, `:266`) and floors
  (`:191`, `:223`, F7); the narrowing statements
  `resource_policy.py::ResourcePolicy.narrowed` (`:402`) and
  `::effective_bound` (`:1526`) with `::_effective_deadline` (`:820`, F8).
- Declarations (principle 1, not definitions): the two `_PACKAGE_*`
  canonical copies (`error_policy.py:144`, `resource_policy.py:459`), each
  one `canonical_policy` call binding its flavor; the two `DEFAULT_*`
  templates (`error_policy.py:137`, `resource_policy.py:450`), each read
  exactly once, by its canonical copy; the six `PrivateAuthority`
  instantiations composing the one generic in `utils/private_state.py`
  (`:90`).
- Consumers (compose by name, stay at their boundary): the schema
  copy-per-read properties (`schema.py:966`, `:980`); the arming call
  (`extensions/resource_policy.py:1604`, canonicalizing through
  `begin_resource_budget`); the charge bodies (`scan_document_text`,
  `charge_document`, bound-int reads only, policy never escapes);
  `policy_from_info` callers (`list_field.py:506`,
  `resource_policy.py:954`, `:1009`, `utils/connections.py:810`);
  `check_deadline` callers (`connection.py:1339`,
  `mutations/resolvers.py:279`, `relay.py:512`, `:597`,
  `resource_policy.py:1008`); the three masking seams (extension teardown
  `:429`, transport source `consumers.py:1459`, schema return
  `schema.py:1174`) sharing one body and both gates; the resume binding
  (`extensions/resource_policy.py:1606`, through
  `operation_state.py::rebind_on_resume`); `bounded_rows` twins through
  `_raw_list_bound` (`resource_policy.py:1000`); re-exports (`__init__.py`,
  `extensions/__init__.py`).
- Oracles: owner-tier `tests/utils/test_policies.py` (three
  private-duplicate pins over a probe policy); package-tier
  `tests/test_error_policy.py` (`:225`, `:258`, `:331`-`:339`),
  `tests/test_resource_policy.py` (`:280`, `:311`, `:339`, `:377`-`:404`,
  `:511`, `:724`, `:3496`-`:3520`, `:3936`-`:4004`), `tests/test_schema.py`
  (`:563`, `:587`), `tests/test_list_field.py` +
  `tests/utils/test_connections.py` (stash/clear/begin coverage),
  `tests/extensions/test_operation_state.py` (`:1023`); live-tier
  `test_error_policy_api.py` (`:171`, `:1023`),
  `test_resource_policy_api.py` (`:431`, `:473`, `:610`, `:2804`, `:2824`),
  `test_list_field_api.py` (`:3500`, `:3535`),
  `test_list_field_async_api.py` (`:2169`), `test_extension_isolation_api.py`
  (chain isolation). Every oracle is behavioral (`is not` identity,
  `__dict__`-write isolation, tampered-template immunity); none names the
  copy mechanics.
- Projections: the `utils/policies.py` module docstring (copy discipline
  prose), both policy module docstrings (template/authority separation),
  the `_SCHEMA_ENFORCEMENT` / `_EXPLICIT_POLICY` / `_active_budget` holding
  comments, the schema class-docstring policy paragraphs, and one spec-047
  canonicalization line (`:478`). No GLOSSARY or KANBAN line names the
  mechanics.

The sibling `schema-construction-policy-ladder` item suggested its R1-R5
operation/request-time reads to this family "for that item to confirm or
refuse". All five are CONFIRMED as members here, each single-owned: R1
`_resolved_policy` and R2 `policy_from_info` in F3, R3
`schema_error_policy` in F4, R4 `_enforcement` over `_FALLBACK_ENFORCEMENT`
in F5, R5 the degrade floors in F7. That item's verdicts are not
re-litigated: the construction ladder, its twins, and its mapping arm stay
that family's, cited here only as boundaries. No row of that item was found
factually wrong; its `_PACKAGE_*` "2 defs + 7 read sites" buckets the same
11 code occurrences this trace censuses (its 7 are the R1/R2/R3/R5 arms;
its F1 holds the 2 resolve defaults; its R4 the 2 fallback reads).

Connected behavior examined and kept out: the construction ladder itself
(sibling family), the mapping-hardening steps (sibling
`hostile-mapping-hardening`), the seal machinery (`_SealPolicy`, R-a), the
django-filter ownership anchor (`_PACKAGE_POLICY_BASELINE`, R-b), the
optimizer execution frame and its sibling `PrivateAuthority` holdings
(R-c, R-e), the scalar/selection neighbor ladders (R-g), and the
operation-state resume machinery (sibling
`operation-bound-extension-mechanism`).

## Verification

### Matrix

1. Cross-flavor policy mirroring. Searched, complete. Both deployment
   flavors compose the same F1/F2 mechanics by import (no mirrored copy
   bodies); both declare a `_PACKAGE_*` fallback and a `DEFAULT_*`
   template; both schema properties are copy-per-read. The per-side reads
   differ by contract, not by duplication: the resource side arms a
   per-operation budget (F3) because it accounts one operation's spending,
   while the error side admits a policy per masking decision (F4) because
   it holds no per-operation state (R-i). `_SealPolicy` shares the token
   and the frozen shape and none of the mechanics (R-a);
   `_NormalizedPolicyEntry` is a value-compared anchor (R-b); the
   optimizer's ContextVar-over-stash idiom is precedent, not a twin (R-e);
   every scalar/selection neighbor resolves a non-policy subject (R-g).
2. Sync/async twins. Searched. Every policy read is an uncolored sync
   function called from both colors. The one colored enforcement pair
   (`bounded_rows` / `bounded_rows_async`) shares its policy read through
   the single `_raw_list_bound`; `execute` / `execute_sync` share the
   single `_masked_return`; the masking teardown is a sync generator the
   engine enters on both paths. No colored duplication.
3. Derived rather than repeated knowledge. Searched. Bound values flow
   from exactly one read per seam (`policy_from_info`, the armed
   snapshot, the enforcement record); no seam re-derives a bound from
   settings, `_meta`, or a second construction. `policy.max_*`
   attribute reads are reads off the one authority object per seam, not
   restatements of a rule. The DST key vocabulary is two single
   declarations; the indefinite article is derived once; the ladder
   vocabulary and the narrowed name guard are the sibling ladder's R13
   boundary, cited, not re-litigated.
4. Inverse / round-trip pairs. Ruled inapplicable with reason. Copies,
   canonicalizations, and masks are one-way object-to-object maps: a
   resolved policy is never serialized back to a mapping, a masked error
   is never unmasked, and no decode half exists for any of them.
5. Contracts restated in another medium. Searched. Four owner/package
   oracle files plus five live wire files pin identity, handout
   isolation, tampered-template immunity, admission, arming, and floors;
   all read production behavior and none is read by it. Projections
   (module docstrings, holding comments, schema paragraphs, one spec
   line) describe; none owns. No medium carries a second implementation.
6. Enforcement by omission. Enumerated two flavors over every isolation
   axis: construction canonicalization (both, via the sibling ladder),
   package fallback (both `_PACKAGE_*`), per-read copies (both schema
   properties), per-use/request reads (F3, F4), floors (F7 by failure
   mode, R-j). The error side's lack of a ContextVar (R-i) and the
   resource side's lack of a whole-response floor (R-j) are
   contract-established asymmetries, each with its trigger below, not
   gaps. Scalar-flag settings hand out no objects and need no isolation;
   no third dataclass-policy flavor exists (class census: `ErrorPolicy`,
   `ResourcePolicy`, plus the excluded `_SealPolicy` and
   `_NormalizedPolicyEntry`). No omission, no defect.

### Enumeration

Instrument: `git grep` over HEAD blobs across all 117 package `.py`
files, plus full HEAD reads of the eight indexed files and region reads
of every file a hit implicates (consumers seam, holding generic, seal
and baseline regions). Populations censused, not sampled: `copy_policy`
(1 def + 6 call sites, 5 files), `canonical_policy` (1 def + 6 call
sites, 4 files), `_PACKAGE_*` (2 defs + 11 code reads at 11 statements,
5 files), `DEFAULT_*` (2 defs, read only by their canonical copy plus
one re-export pair), `ErrorPolicy(`/`ResourcePolicy(` constructions (2
templates + 2 docstring examples), `policy_from_info` (1 + 4),
`armed_resource_policy` (1 + 2), `schema_error_policy` (1 + 2),
`_resolved_policy` (1 + 2), `_enforcement` (1 + 5), `_armed_budget`
(1 + 5 internal readers), `_operation_policy` (1 + 3),
`mask_execution_result` / `masking_is_active` / `is_maskable_result`
(1 + 3 each, the same three seams), `degraded_result` (1 + 4),
`_active_budget` (def + get/set/rebind/reset, all inside the lease
lifecycle), DST keys (2 declarations + publish/read/clear/restore,
2 files), `narrowed` (1 def, 0 production callers, 9 oracle calls),
`effective_bound` (1 + 3), `check_deadline` (1 + 5), begin/end/adopt/
resume bindings (1 + 1 each), `object.__new__` (4 sites, 4 contracts),
`PrivateAuthority` (1 generic + 6 instantiations), policy-class defs
(4, two excluded). Every member lands in F1-F8, an R-exclusion, or a
sibling-boundary note; nothing is unassigned.

### Challenges

Each challenge posits a change on one of the family's variation axes and
counts authoritative definitions that must move. Consumers, oracles, and
projections that also move are listed, never counted.

- C1 (handout axis): duplicates must survive a new hostile field shape
  (a policy gains a mutable member the shallow field-dict copy would
  share). Moves: `copy_policy` (`:58`-`:60`) = 1. All six handouts (both
  schema properties, both `policy_from_info` arms, the mirror publish,
  the extension `_policy` read) follow by construction.
  `canonical_policy` does not move (it constructs through the validated
  constructor, a different build). Oracles move (tamper pins gain the new
  shape); the copy docstring moves as projection.
- C2 (admission axis): canonicalization must reject a new hostile shape
  (a metaclass answering field reads per call). Moves: `canonical_policy`
  (`:91`-`:102`) = 1. All six canonicalizations (three ladder arms, two
  package copies, the per-operation `_operation_policy`) follow.
  `copy_policy` does not move (its sources are already authority-owned).
  The F1/F2 merge is refused under R-h: merging validates the per-field
  hot path on every read or bypasses admission validation.
- C3 (arming axis): arming precedence flips so the schema's policy
  outranks an extension's explicit policy. Moves: `_resolved_policy`
  (`:1561`-`:1569`) = 1. `policy_from_info`, `schema_error_policy`, and
  the construction ladder do not move (different authorities, different
  lifetimes). Oracles move (arming-precedence pins).
- C4 (request-read axis): request authority order flips (mirror outranks
  the armed budget). Moves: `policy_from_info` (`:916`-`:920`) = 1. The
  arming ladder and the error admission read do not move. Oracles move
  (mirror-tamper pins invert).
- C5 (error-admission axis): a policy subclass is admitted where only an
  `ErrorPolicy` passes today. Moves: `schema_error_policy` (`:304`-`:308`)
  = 1, plus its two callers' containment reasoning as consumers
  (consumers seam, extension `_policy`). The resource reads do not move.
- C6 (record axis): the enforcement record gains a third member. Moves:
  `_SchemaEnforcement` (`:465`) = 1 declaration; its two inhabitants
  follow (the settle call and `_FALLBACK_ENFORCEMENT`), as declarations
  follow their record, not as second definitions. Retrieval
  (`_enforcement`) is unchanged in shape.
- C7 (floor axis): the entry floor must carry a correlation id. Moves:
  `_degraded` (`:191`) = 1. `degraded_result` composes it, and both
  whole-response callers (teardown, `_masked_return`) follow. The
  resource miss-path baseline does not move (different failure mode,
  R-j). Oracles move (floor-shape pins).
- C8 (mirror-vocabulary axis): the DST keys are renamed. Moves: the two
  key declarations (`:118`-`:119`) = 1 declaration site. Publish, both
  reads, clear, and the restore scope follow by name. No enforcement
  logic moves.
- C9 (narrowing axes, three legitimate variations): (a) the deadline arm
  of `narrowed` changes (None-handling). Moves: `narrowed` = 1
  (`effective_bound` and `_effective_deadline` have no deadline arm).
  (b) the trusted carve-out changes. Moves: `effective_bound` = 1 (the
  other two have no trusted arm). (c) the mirror type gate changes.
  Moves: `_effective_deadline` = 1 (the other two admit no consumer
  objects). Each legitimate axis moves exactly its own statement; the
  shared remainder is the one-line tighter-wins idea, which is stdlib
  comparison, not a rule (F8).
- C10 (explicit-holding axis): the accepted record gains the arming
  instant. Moves: `_AcceptedPolicy` (`:1413`) = 1 declaration; settle
  and the `_policy` read follow. The schema record does not move
  (different authority kind). The holding generic does not move (its
  contract is kind-agnostic).
- C11 (masking-application axis): masking must preserve a new result
  field. Moves: `mask_execution_result` (`:311`) = 1. All three seams
  (teardown, transport source, schema return) follow; none restates the
  classification or the replacement. Oracles move (masked-shape pins
  including both live wire tiers).

All counts are 1. No posited change moves two definitions.

## Findings

### F1: handout duplicates are single-owned at `copy_policy`

- Contract + variation: every policy object handed to consumer-reachable
  code is a private duplicate built by field-dict copy without
  re-validation, because the source already validated itself and this
  runs on the per-field hot path. Varies on the duplicate build only.
- Sites + roles: the definition (`utils/policies.py:39`); six call
  sites composing by name (schema `resource_policy` `:966`,
  `error_policy` `:980`, `policy_from_info` `:918` + `:920`, mirror
  publish `:643`, extension `_policy` `:1552`); identity + tamper
  oracles at both tiers; the copy docstring as projection.
- Challenges: C1 above, count 1.
- Owner + lifetime: `utils/policies.py::copy_policy`, by
  responsibility (principle 7): the narrowest module both flavors, the
  schema, and both extensions already import without reversing a
  dependency (it imports only exceptions), and the only candidate whose
  contract is trusted-source duplication. Stateless; no lifetime fields
  owed. Re-derives (not inherits) the index row's owner candidate: the
  census admits no second handout body.
- Migration: none. Every handout already calls it.
- Distinct behavior: admission canonicalization stays separate (F2,
  R-h); narrowing derivation stays separate (F8).
- Behavioral proof: static-reviewed. A zero-edit single-ownership
  verdict owes no equivalence proof; the evidence is the census (1 def,
  6 calls, 5 files, zero `object.__new__` handout twins) plus C1. The
  oracles that fail a missing copy already exist in-tree (per-site
  `is not` + `__dict__`-tamper pins) and are cited, not re-run.
- Structural gate: the per-site tamper pins are the gate that already
  exists. The realistic bypass is a handout returning the authority
  itself, which the identity pins fail at once; a duplicated body
  passes behaviorally, but nobody duplicates a three-line importable
  helper when the import is cheaper, and a name-census gate over a
  semantically-defined population (handout-ness) is AST-fragile and
  explicitly not the shape. No new gate owed.
- Coupling: none. Zero edits, zero dependencies.
- Freshness: HEAD `5c3496e0`
  (`5c3496e00d1e63653b2a2f857c2b4dd81f05eebc`). Family-wide input
  fingerprints (full blob ids; any change reopens every finding):
  `utils/policies.py 4b180e2bbf08a93e1ffa4c7668502d7559058410`,
  `error_policy.py 7fc87d9f88bcdcc91ebfe525c509d93ae31ba42d`,
  `resource_policy.py c554a6799cc631ae836d27e17b93991d8f050f14`,
  `extensions/error_policy.py 449b8f8ad69a63b9a5bff8de448b1ab162760338`,
  `extensions/resource_policy.py 11e2a9acdf41380a500755df441bc7e05d479145`,
  `schema.py 0dad535d3e2f7ab1b47ed0d1adf07ce1e5caa03c`,
  `list_field.py 37d2e6dc7311484d78726b89dc4a1d461f171398`,
  `utils/connections.py 5bf8f5fa533f4c075cbb9915d471dedf028ff41e`,
  `consumers.py 0607464005666293c81142602b4ace4341ba7f34`,
  `conf.py eccddc21c635dd9a2cf282a3d22e50847e62ef84`,
  `utils/private_state.py ec4d8fc8fa6fd893020fae333c1ff8cbfdf84e06`,
  `utils/context.py 36675564a6af34b8ec573767bcc7c8e7fbc89c10`,
  `utils/querysets.py 69ac3ea3fc6e0b1ac3ffaa11e989e7831ad00a90`,
  `filters/sets.py 85699ac22e1d076877d32fc76a0a9427c2f05eab`,
  `connection.py 999696529e18160aff1e465951ebe7e88dd4613b`,
  `relay.py 037723cd688e953f55cda983cf4703746ba478c5`,
  `mutations/resolvers.py d77a6c683c8af20ef2a4b8024bc76d75e00857fb`,
  `types/resolvers.py 09d40f34ddeca4fa7f191fd05b2c8a6bec1f5cdf`,
  `extensions/operation_state.py 1b43066c99465efa7642d75ac48c1b596bae44dc`,
  `optimizer/_context.py 274a138b8da616368ac2670aa9f6e93561b21ff6`,
  `optimizer/extension.py b7b6c4342e71ec1dbb4047f697745d2796272f6e`,
  `extensions/debug.py 47bc60c9ddc6a4d7c87189b339653abbc20eebfd`,
  `utils/permissions.py 0e13b869c69aaf19f912f465086d055e41e0a608`,
  `sets_mixins.py 42e8c8624e8b34e79217e557c6f38ca17c8e8451`,
  `__init__.py 8b1656724a150cc1a628c2bff5ba91fdba621ce2`,
  `tests/utils/test_policies.py 57ab21701c2885eb8ed734c93a12c473955397d1`,
  `tests/test_error_policy.py 58129ec24faba999683a3a828e837823d7bf9cb9`,
  `tests/test_resource_policy.py 7e8fb465ebb13e919fe42ea48c28abc253073894`,
  `tests/test_schema.py ee3e29121656aed1ff1081879798aaabd86bf9fb`,
  `test_error_policy_api.py 20cf3807eccafeae8892eec1e5237c84b049e67a`,
  `test_resource_policy_api.py ae7bef60173211f55d3e09e022228f69747fa846`,
  `test_extension_isolation_api.py 2744212cf0693cc283253aa9e786882304cfdd44`,
  `test_list_field_api.py 4ad8d8f237a4a2ed477b00ceebcb7c29a0d2eaa6`,
  `test_list_field_async_api.py 4a570915e2b8d518c61b64bc3c92f3a1c7b272a7`.
  Searched population: all 117 package `.py` blobs at HEAD (mechanism-
  token census; every hit classified) plus the oracle and projection
  files named. Working-tree pins at submission match the dispatch pins
  on all eight indexed files; the verdict reads HEAD bytes only.

Verdict on F1: CONFIRM single ownership; zero-edit.

### F2: admission canonicalization is single-owned at `canonical_policy`

- Contract + variation: every policy object admitted from
  consumer-held code (constructor argument, setting, import-time
  template, arming input) is re-read field by field into a fresh,
  validated, exact-typed object; the original is discarded. Varies on
  the admission build and its typed rejection.
- Sites + roles: the definition (`utils/policies.py:63`); six call
  sites (three ladder arms, two package copies, `_operation_policy`);
  the `_operation_policy` one-line flavor binding as a declaration;
  duplicate-identity oracles; the canonical docstring as projection.
- Challenges: C2 above, count 1; the F1/F2 merge is the refused
  control (R-h).
- Owner + lifetime: `utils/policies.py::canonical_policy`, same
  principle-7 reasoning as F1 (shared module, shared importers, no
  state). The two mechanics share an owner module but are two rules
  with different contracts and different reasons to change.
- Migration: none. Distinct behavior: the trusted fast path (F1),
  the mapping arm's fresh construction (R-f).
- Behavioral proof: static-reviewed (census + C2 + the in-tree
  duplicate pins). Structural gate: same tamper-pin gate as F1 (an
  admitted object that IS the caller's fails the `is not` pins).
  Coupling: none. Freshness: the family table (F1).

Verdict on F2: CONFIRM single ownership; zero-edit.

### F3: the resource operation/request-time reads are each single-owned

- Contract + variation: per operation, arm exactly one budget
  (explicit extension policy, else the schema's, else the package
  baseline) as a private snapshot under a lease; per request, answer
  the armed budget, else the published mirror under an exact-type
  gate, else a copy of the baseline; publish the mirror as a copy
  beside the arming; derive one absolute deadline for both. Covers
  the sibling's R1 (`_resolved_policy`) and R2 (`policy_from_info`),
  CONFIRMED as members here.
- Sites + roles: `_resolved_policy` (1 + 2: arming call, no-scope
  fallback), `_operation_policy` (1 + 3), `begin_resource_budget`
  and its end/adopt/resume bindings (1 + 1 each), `_armed_budget`
  (1 + 5 internal readers), `policy_from_info` (1 + 4),
  `armed_resource_policy` (1 + 2, package-internal by docstring, not
  exported), `check_deadline` with `_absolute_deadline`,
  `_deadline_expired`, and the mirror helpers (1 def each),
  `_publish_budget_mirror` / `stash_resource_policy` /
  `clear_resource_context` (1 def each; the last two are callerless
  public APIs with oracles in `tests/test_list_field.py`,
  `tests/test_resource_policy.py`, `tests/utils/test_connections.py`),
  the DST key pair (1 declaration site). The admission verdict
  (`record_` / `admission_rejection`) rides the same lease through
  the same `_armed_budget` read: a composed consumer, not a second
  per-operation read. The read-vs-handout boundary holds at every
  site: `_resolved_policy` answers the singleton only to callers
  that canonicalize (`begin_resource_budget`) or read bound ints
  (`charge_document`, `scan_document_text`, policy never escapes);
  every object crossing to consumer code is a copy (F1).
- Challenges: C3, C4, C8 above, each count 1.
- Owner + lifetime: `resource_policy.py` for all of them (principle
  7): the module owns the ContextVar, the lease lifecycle, and the
  mirror keys, and every legitimate consumer (extensions, fields,
  connections) already imports it. Principle-4 lifetime: the armed
  budget lives in `_active_budget` for one operation, published at
  `begin_resource_budget`, ended at `end_resource_budget`, closed
  across copied contexts by lease close; the mirror lives on the
  request context for the operation, saved and restored by
  `restored_context_keys` (that save/restore rule is `utils/context.py`'s,
  composed by name).
- Migration: none. Distinct behavior: the error admission read (F4),
  the record retrieval (F5), the deadline narrowing statement (F8).
- Behavioral proof: static-reviewed (census + C3/C4/C8 + the in-tree
  arming, mirror-tamper, and write-isolation pins at both tiers).
  Structural gate: the per-site pins (armed-vs-mirror precedence,
  mirror rewrite reaching no bound, copy-per-`policy_from_info`).
  Coupling: none. Freshness: the family table (F1).

Verdict on F3: CONFIRM single ownership; zero-edit.

### F4: the error admission read is single-owned at `schema_error_policy`

- Contract + variation: admit the schema's carried policy under an
  `isinstance` gate with hostile-schema containment, else the package
  baseline. Covers the sibling's R3, CONFIRMED as a member here.
- Sites + roles: the definition (`:290`, two fallback arms, one
  function); two callers (extension `_policy`, consumers per-event
  seam, which resolves once per subscription and gates per event);
  fallback oracles at both tiers.
- Challenges: C5 above, count 1.
- Owner + lifetime: `extensions/error_policy.py` (principle 7): the
  module owns the hand-wired-schema seam the containment exists for,
  and both callers already import it. Stateless read; no lifetime
  fields owed. The singleton is answered only to package-internal
  field readers (F7 gates + masking), never handed out.
- Migration: none. Distinct behavior: the resource reads (F3), the
  record retrieval (F5). Behavioral proof: static-reviewed (census +
  C5 + fallback pins). Structural gate: the fallback pins (wrong-type
  attribute, raising schema). Coupling: none. Freshness: the family
  table (F1).

Verdict on F4: CONFIRM single ownership; zero-edit.

### F5: the schema enforcement record is single-owned in `schema.py`

- Contract + variation: what one `DjangoSchema` construction settled
  (both resolved policies, the extensions-settled flag) is held where
  no name on the schema reaches, retrieved per read, with a constant
  fallback record answering for a schema that settled none. Covers
  the sibling's R4, CONFIRMED as a member here.
- Sites + roles: the record declaration (`:465`, 1), the store
  (`:506`, 1 of 6 `PrivateAuthority` instantiations), the fallback
  constant (`:545`, 1), the retrieval (`:551`, 1 + 5 readers: the
  extensions setter, both policy properties, `get_extensions`,
  `_masked_return`).
- Challenges: C6 above, count 1.
- Owner + lifetime: `schema.py` (principle 7): the module owns the
  schema lifecycle the record is filed under, and the record type is
  meaningless anywhere else. Principle-4 lifetime: settled before
  the base constructor runs, held strongly beside a weak reference
  that drops the entry when the schema dies (the generic's
  contract); the flag flips once, in the extensions setter.
- Migration: none. Distinct behavior: the explicit extension
  holding (F6, a different authority kind under the same generic),
  the operation reads (F3), the admission read (F4). Behavioral
  proof: static-reviewed (census + C6 + the in-tree settle/flag/
  fallback pins). Structural gate: the record pins (re-`__init__`
  refusal, attribute-write isolation, unsettled-schema fallback).
  Coupling: none. Freshness: the family table (F1).

Verdict on F5: CONFIRM single ownership; zero-edit.

### F6: the explicit extension policy holding is single-owned

- Contract + variation: the override one resource extension was
  constructed with is canonicalized at acceptance, held where no
  name on the extension reaches, and read back as a copy per read;
  no override settles as none (inherit, not a pinned snapshot).
- Sites + roles: the record (`:1413`, 1), the store (`:1437`, 1 of
  6 instantiations), the `__init__` canonicalization (`:1525`, 1),
  the copy-per-read property (`:1531`, 1 + its arming reader).
- Challenges: C10 above, count 1.
- Owner + lifetime: `extensions/resource_policy.py` (principle 7):
  the module owns the extension lifecycle the holding is filed
  under. Lifetime matches F5's (settle at construction, weak-drop
  at death) through the same generic; two instantiations of one
  generic are two declarations, not two definitions, because the
  authority kinds (schema record vs extension override) change for
  independent reasons.
- Migration: none. Distinct behavior: the schema record (F5).
  Behavioral proof: static-reviewed (census + C10 + the in-tree
  `_policy` copy pins). Structural gate: those pins (rebind/delete/
  write reaching no later operation). Coupling: none. Freshness:
  the family table (F1).

Verdict on F6: CONFIRM single ownership; zero-edit.

### F7: masking application and floors are single-owned

- Contract + variation: one classification, one replacement, one
  whole-response floor, applied at three seams (operation teardown,
  transport result source, schema return) under one activity gate
  and one shape gate; any seam that cannot decide publishes the
  policy message alone. Covers the sibling's R5, CONFIRMED as a
  member here.
- Sites + roles: `mask_execution_result` (1 + 3, the three seams),
  `masking_is_active` (1 + 3, the same seams), `is_maskable_result`
  (1 + 3, the same seams), `_degraded` (1 + its two whole/entry
  callers), `degraded_result` (1 + 4: mask failure, adopt failure,
  teardown failure, `_masked_return` floor). `_masked_return`
  pre-reads the package default as its floor precisely so the
  degrade cannot itself raise on the read it guards.
- Challenges: C7, C11 above, each count 1.
- Owner + lifetime: `extensions/error_policy.py` (principle 7): the
  module owns the masking contract all three seams apply, and the
  transport seam already imports it function-locally to preserve
  the channels-free import graph. Stateless application; no
  lifetime fields owed.
- Migration: none. The three seams were already one body; there is
  nothing to re-point. Distinct behavior: the resource miss-path
  baseline (R-j, a different failure mode). Behavioral proof:
  static-reviewed (census + C7/C11 + the masked-shape and floor
  pins at both tiers). Structural gate: those pins (per-event and
  return seams cannot drift on gate, shape, or replacement).
  Coupling: none. Freshness: the family table (F1).

Verdict on F7: CONFIRM single ownership; zero-edit.

### F8: narrowing-only is three single-owned statements of one idea

- Contract + variation: a held policy tightens freely and never
  loosens (`narrowed`, raising); a seam combines a request bound
  with a field declaration to the tighter of the two unless
  literally trusted (`effective_bound`, selecting); a
  consumer-writable deadline mirror narrows the armed deadline and
  never widens it (`_effective_deadline`, type-gated). The shared
  content is the one-line tighter-wins idea; each statement's
  contract (raise vs select vs contain), subject (derivation vs seam
  combination vs mirror), and variation axes are its own.
- Sites + roles: `narrowed` (1 def, 0 production callers, 9 oracle
  calls: a consumer derivation API), `effective_bound` (1 + 3:
  list-field ceiling, `_raw_list_bound`, relay-cap ceiling),
  `_effective_deadline` (1 + 1: `check_deadline`).
- Challenges: C9a/b/c above, each count 1. The contrived change
  "tighter wins becomes looser wins" moves all three, but it inverts
  the security posture no deployment asks for; it is not a
  legitimate variation axis, and consolidating on it would couple
  three contracts behind mode flags (principle 5) to share what is
  stdlib comparison (principle 11).
- Owner + lifetime: `resource_policy.py` for all three (principle
  7): the module owns the budget domain every statement narrows
  within. Stateless derivations; no lifetime fields owed.
- Migration: none. Distinct behavior: the copy mechanics (F1: no
  validation, trusted source) and the admission mechanics (F2:
  validation, untrusted source) — the prior handout-vs-narrowing
  separation stands on fresh evidence (different inputs, outputs,
  and error postures). Behavioral proof: static-reviewed (census +
  C9 + the narrowing, hostile-bound, and deadline pins). Structural
  gate: those pins (widening rejected/narrowed, trusted-`True`
  only, subclass mirror refused). Coupling: none. Freshness: the
  family table (F1).

Verdict on F8: CONFIRM single ownership; zero-edit.

### Rejections and exclusions (contract difference + trigger each)

R-a. `utils/querysets.py::_SealPolicy` (`:2931`) and its per-surface
constants. Difference: internal ORM option records (row-type, slice,
combinator, alias, evaluatedness axes) with no deployment
configuration, no canonical/copy mechanics, no per-request reads, no
mirror, no package fallback — the mechanism-token census touches none
of them. Shares the token "policy" and the frozen shape only.
Trigger: seal options become deployment-configurable policy objects
handed across the consumer boundary.

R-b. `filters/sets.py::_PACKAGE_POLICY_BASELINE` (`:425`) over
`_NormalizedPolicyEntry` (`:391`). Difference: name collision only; a
frozen django-filter table anchor compared by normalized value at its
ownership check, with none of the isolation mechanics. Trigger: none;
different mechanism entirely.

R-c. Sibling `PrivateAuthority` holdings: debug acknowledgement
(`extensions/debug.py:591`), operation carriers + package-managed
(`extensions/operation_state.py:282`, `:301`), optimizer configuration
(`optimizer/extension.py:943`). Difference: the same generic holding
non-policy authorities; each instantiation declares its own kind.
Trigger: a sibling starts holding a deployment policy — it then joins
the F5/F6 holding discipline, still through the generic, not as a new
mechanism.

R-d. Sibling `object.__new__` sites: set-machinery bare instance
(`sets_mixins.py:748`), permission-gate invocation instance
(`utils/permissions.py:569`), query-AST node rebuild
(`utils/querysets.py:2069`). Difference: construction without
`__init__` for machinery dispatch, each under its own contract —
none duplicates a validated policy for handout. The prior AST-rebuild
rejection stands trigger-checked (still a rebuild at `:2069`, still
no policy subject). Trigger: a second site duplicates a validated
policy for handout without re-validation.

R-e. The optimizer's ContextVar-over-stash frame
(`optimizer/_context.py`). Difference: the same idiom applied to a
different subject (optimizer execution state vs the resource budget);
the budget module cites it as precedent. Extracting a shared driver
would couple two domains with independent lifecycles. Trigger: a
third ContextVar-over-stash authority with shared lifecycle
operations (arm/read/disarm/rebind) — then a driver, not a copy.

R-f. The mapping arm's fresh construction
(`utils/policies.py:190`, `policy_cls(**plain)`). Difference: builds
a new object the caller never held and validates it through the same
`__post_init__` gate — freshness by construction, never a copy, never
a re-read. Boundary with F2, owned by the sibling ladder. Trigger:
the arm starts handing back caller-held or unvalidated objects.

R-g. Scalar/selection neighbor ladders: views byte cap, strategy
selection, test endpoint, revalidation window, relay-cap precedence
(a consumer composing `policy_from_info` + `effective_bound` by
name), auth aliases and the remaining `resolve_*` census. Difference:
no policy object crosses a consumer boundary at any of them, so no
copy, read-ladder, mirror, or fallback mechanics exist to share;
the negative mechanism-token census is empty outside the enumerated
files. Converges the sibling ladder's neighbor direction for this
family's mechanism. Trigger: a neighbor starts handing validated
policy objects to consumer code.

R-h. Merging `copy_policy` into `canonical_policy`. Difference:
trusted fast path (no validation, per-field hot path) vs untrusted
admission (re-read + re-validate + typed rejection) — different
inputs, outputs, error postures, and reasons to change. Merging
validates the hot path on every read or bypasses admission
validation; the separation is recorded at the owner (the `copy_policy`
docstring's constructor paragraph). Trigger: re-propose only with
both premises gone — the per-read path no longer hot AND admission
no longer needing validation.

R-i. The error side holds no per-operation armed budget. Difference:
not an omission — no per-operation error state exists, because
masking decides per result from the settled policy; the extension
and `schema_error_policy` docstrings establish read-per-use. Trigger:
a spec row requiring per-operation error-policy state.

R-j. The resource side has no whole-response degrade floor.
Difference: not an omission — resource failures are typed
rejections (`ResourceLimitExceeded`) or the baseline copy, never an
uncertifiable response; no seam publishes half a response. Trigger: a
resource seam that can fail to decide — it then needs a floor, homed
in F7.

R-k. `dataclasses.replace` on the enforcement record (`schema.py:946`)
vs in `narrowed` (`resource_policy.py:420`). Difference: different
subjects (record flag flip vs policy derivation under narrowing
checks), each single-sited; the shared spelling is stdlib
construction. Trigger: none while one shapes records and the other
derives policies.

## Defects

None found. The trace read for contract at every site above. The four
shapes that could have been defects resolve to contract on the bytes:
`_resolved_policy` and `schema_error_policy` answer the package
singleton only to callers that canonicalize it or read bound ints off
it (F3, F4 — the read-vs-handout boundary, accounted site by site);
`narrowed`, `stash_resource_policy`, and `clear_resource_context`
have no production callers because they are public consumer APIs,
each with oracles; the error side's lack of arming and the resource
side's lack of a degrade floor are contract-established asymmetries
(R-i, R-j). No docstring contradicts its body on isolation behavior,
no flavor lacks a guard its contract requires (axis 6 enumerates the
full surface), and no layering claim is contradicted by the imports
(flavors, schema, and extensions import the mechanics; the mechanics
import only exceptions).

## Pending execution

None. Every verdict is static-decidable (definition counts from the
source census plus the eleven challenges); no equivalence proof is
owed because nothing moves, and no gate is relied on beyond the
tamper, identity, precedence, and floor pins already in-tree. The
`--cell sharded` / `--cell pg` cells are inapplicable by construction:
the finding touches no database, alias, or dialect decision (pure
construction/read/mask logic plus a source census). No `proof:` or
`gate:` entry is owed. The three static gates were re-run read-only
in the shared tree at submission as informational confirmation of the
zero-edit (nothing changed, so nothing could redden): mypy clean
(119 source files), basedpyright 0 errors / 0 warnings / 0 notes,
check_any 130 allowed uses at 90 sites.

## Judgment

Policy authority isolation is already one family of single-owned
rules: `copy_policy` hands out every duplicate (F1),
`canonical_policy` admits every object (F2), each resource read
(arming, armed, request, mirror, deadline) lives in exactly one body
(F3), the error admission read in one (F4), the schema record and the
explicit extension holding each in one authority kind under the one
holding generic (F5, F6), the three masking seams share one body with
one entry floor and one whole-response floor (F7), and narrowing-only
is three statements of one idea whose legitimate axes each move one
site (F8). The sibling ladder's R1-R5 are confirmed as members, not
second ladders. Everything outside is a neighbor by mechanism
absence (R-a-R-g, R-k), a refused merge (R-h), or a
contract-established asymmetry with its trigger (R-i, R-j). CONFIRM
single ownership, zero edits, no new index rows owed: every sub-rule
is adjudicated in this artifact and there is nothing left to
dispatch.

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

Run: 0.0.15 2026-10-01-9. Pass 1, address `dry/polauth-f13/verify`.
HEAD `5c3496e0` (matches dispatch); ITEM_BASELINE `c385a77f79732206e698312f3ae8c5fb4592acc3`.
Probe path: shared venv / stdlib-only drivers + `git show HEAD:` / `git grep HEAD`
census instruments (slots 1-3 venvs damaged for import-execution, slot-4
unselectable; no workspace-slot execution used, no `--cell` runs).

### Worker-2 independent trace (recorded before opening `## Findings`)

Method: fresh HEAD-byte reads of all 8 indexed files (full reads of
`utils/policies.py`, `error_policy.py`, `extensions/error_policy.py`;
`resource_policy.py` / `extensions/resource_policy.py` / `schema.py` /
`list_field.py` / `utils/connections.py` in full for WT plus HEAD-byte
region verification of every isolation-relevant def), plus package-wide
`git grep HEAD` censuses for the rule's mechanism tokens
(`canonical_policy`, `copy_policy`, `_PACKAGE_*` / `DEFAULT_*`,
`policy_from_info`, `schema_error_policy`, `effective_bound`, `narrowed`,
`_operation_policy`, `armed_resource_policy`, `check_deadline`,
`stash_resource_policy`, `mask_execution_result`, `object.__new__`,
`_SCHEMA_ENFORCEMENT`). The worktree carries concurrent truth/lazy-migration
+ prose dirt on 7 of the 8 indexed files (`utils/connections.py` clean);
every hunk attributed by content below, none relied on. `utils/truth.py`
and `utils/lazy.py` do not exist at HEAD (untracked concurrent work), so
all `truth.*` / `unwrap_lazy_object` spellings are dirt. Pre-run-9 blob pins
differing from `5c3496e0` are never staleness (binding constraint).

Dirt attribution (HEAD `5c3496e0` vs worktree, isolation-relevant hunks only;
all concurrent-external, left untouched):
- `utils/policies.py`: module-docstring hostile-mapping rewording;
  `canonical_policy` containment (`try/except` -> typed `ConfigurationError`)
  replaced by propagation; `resolve_policy` `isinstance` -> `truth.is_instance`
  + lazy-unwrap arms, mapping-consumption containment removed, subclass-key
  normalization added. `copy_policy` body identical but for a `# truth:` note.
- `error_policy.py`: `describe_value` -> `truth.describe` (2 sites). Bodies identical.
- `resource_policy.py`: imports/`__reduce__`/`_require_positive_int` message
  migration; `ResourcePolicy` docstring seam-list +`types/resolvers.py`
  mention added (WT-only: `check_deadline` callers in `types/resolvers.py`
  exist in WT, zero at HEAD); `narrowed` else-arm `value > current` via
  `cast` (behavior-identical for exact ints); `_deadline_expired` /
  `check_deadline` / async-cleanup / `validate_trusted_flag` migration.
  `copy_policy` / `canonical_policy` call sites, `_operation_policy`,
  `policy_from_info`, `effective_bound`, `stash` / `begin` / `end` / `armed`
  bodies: no hunks.
- `extensions/error_policy.py`: docstring +3 lines; `_degraded` guarded
  message read (fallback to package message) replaced by direct read;
  `masking_is_active` `enabled`-containment + broad DEBUG containment
  replaced by direct read + narrow containment; `schema_error_policy`
  containment + `isinstance` gate replaced by direct read + exact gate;
  `on_operation` whole-body containment replaced by straight-line hooks.
  `_masked` / `_replacement_for` / `mask_execution_result` / `_process_result` /
  `is_maskable_result` bodies: no hunks.
- `extensions/resource_policy.py`: 2 `_ValueBudget` measurement-containment
  hunks only. `_AcceptedPolicy` / `_EXPLICIT_POLICY` / `_policy` /
  `_resolved_policy` / arming bodies: no hunks.
- `schema.py`: prose + import migration; `_entry_resource_policy`
  `_is_class` -> `truth.is_type` (same gate) with helper deleted.
  `_SCHEMA_ENFORCEMENT` block, both policy properties, `_masked_return`: no hunks.
- `list_field.py`: validation/message migration only; `policy_from_info` /
  `effective_bound` call sites untouched.

Fingerprints (all 8 WT pins match dispatch pins; HEAD pins match too):
- `utils/policies.py` WT `8d02c54b` / HEAD `4b180e2b`; `error_policy.py` WT
  `b8c9c2e5` / HEAD `7fc87d9f`; `resource_policy.py` WT `814eb7e9` / HEAD
  `c554a679`; `extensions/error_policy.py` WT `c2f5eb5a` / HEAD `449b8f8a`;
  `extensions/resource_policy.py` WT `a7f7363f` / HEAD `11e2a9ac`;
  `schema.py` WT `66f2aa9c` / HEAD `0dad535d`; `list_field.py` WT `6c0992f2` /
  HEAD `37d2e6dc`; `utils/connections.py` WT=HEAD `5bf8f5fa` (clean).

All line numbers below are HEAD bytes.

Population (definitions + consumers; oracles/projections listed, never counted):
- D1 `utils/policies.py::copy_policy` (:39): the handout-duplicate body
  (`object.__new__` + `__dict__.update`, no revalidation). Code callers (6):
  `resource_policy.py:643` (mirror publish), `:918` + `:920`
  (`policy_from_info` armed + mirror arms), `schema.py:966` + `:980` (both
  per-read properties), `extensions/resource_policy.py:1552` (`_policy`).
- D2 `utils/policies.py::canonical_policy` (:63): the admission body (re-read
  each field once, rebuild + revalidate, containment -> typed error at HEAD).
  Code callers (6): `resolve_policy` 3 arms (`:141/:144/:151`),
  `resource_policy.py:459` + `error_policy.py:144` (the two `_PACKAGE_*`
  defs), `resource_policy.py:674` (`_operation_policy`).
- D3 schema enforcement record: `schema.py::_SchemaEnforcement` (:465),
  `_SCHEMA_ENFORCEMENT` (:506), `_FALLBACK_ENFORCEMENT` (:545),
  `_enforcement` (:551). Readers: both properties (:966/:980),
  `_masked_return` (:1141), extension-chain settle (:861/:946, flag arm only).
- D4 explicit extension holding: `extensions/resource_policy.py::
  _AcceptedPolicy` (:1413), `_EXPLICIT_POLICY` (:1437), `__init__` settle
  (:1525, via `_operation_policy`), `_policy` (:1531, copy per read).
  Readers: `_resolved_policy` (:1554), `schema.py::_entry_resource_policy`
  (:1379, exact-type gate).
- D5a `extensions/resource_policy.py::_resolved_policy` (:1554):
  explicit-copy > schema-attr (`isinstance` gate) > package singleton;
  sole caller `on_operation` (:1572) arms via `begin_resource_budget`.
- D5b `resource_policy.py::policy_from_info` (:880): armed-copy > mirror
  (exact-type gate) > baseline-copy. Callers: `list_field.py:506`,
  `resource_policy.py:954` (`check_deadline` fallback arm),
  `resource_policy.py:1009` (`_raw_list_bound`), `utils/connections.py:810`.
- D6 `extensions/error_policy.py::schema_error_policy` (:290): schema-attr
  (contained read, `isinstance` gate) > package singleton. Callers:
  extension `_policy` (:406), `consumers.py:1451` (per-event seam).
- D7 masking application: `mask_execution_result` (:311) + `_replacement_for`
  (:363) + `_is_unexpected` (:104) + `_masked` (:160) + gates
  `masking_is_active` (:238) + `is_maskable_result` (:266); floors `_degraded`
  (:191, per-entry) + `degraded_result` (:223, whole-response). Applied at 3
  seams composing by name: teardown `_process_result` (:411)+`on_operation`
  (:443), `consumers.py:1458-1459` per-event, `schema.py:1141`
  `_masked_return`. `new_correlation_id` (`error_policy.py:177`) has the one
  caller `_masked`.
- D8a `ResourcePolicy.narrowed` (:402): whole-policy derivation, raises on
  widen. Zero package callers at HEAD (public consumer API; pinned by
  `tests/test_resource_policy.py:377-398` + GLOSSARY/spec-047 projections).
- D8b `resource_policy.py::effective_bound` (:1526): per-bound combination,
  `trusted is True` widening carve-out. Callers: `list_field.py:534`,
  `utils/connections.py:810`, `resource_policy.py:1009`.
- D8c `resource_policy.py::_effective_deadline` (:820): deadline narrowing
  (tighter of armed + consumer-written). Sole caller `check_deadline` (:923).
- Supporting single-owned seams (each count 1, no second site):
  `_operation_policy` (:663, callers: `begin_resource_budget` :677,
  `stash_resource_policy` :647, extension `__init__` :1503);
  `begin/end_resource_budget` (:677/:788) + `_armed_budget` (:608) +
  `_publish_budget_mirror` (:631); `armed_resource_policy` (:739, package-
  internal non-copy read, callers: extension `:1613` scan arm + `:1668`
  admission arm); `check_deadline` (:923, callers: `connection.py:1339`,
  `relay.py:512` + `:597`, `mutations/resolvers.py:279`, `:1008`);
  `stash_resource_policy` (:647, zero package callers, test-pinned mirror
  API); `clear_resource_context` (mirror removal); `validate_collection_bound`
  / `validate_trusted_flag` (:1499/:1509, sole caller `list_field.py:1620-1621`);
  `_raw_list_bound` (:1000, shared by both `bounded_rows` colors);
  `_deadline_expired` (:847, sole caller `check_deadline`).
- Templates vs authorities: `DEFAULT_*` (2 defs, exported, re-exported once
  each from the root; zero package reads — template only) vs `_PACKAGE_*`
  (2 defs; code reads: 2 `default=` rungs, `policy_from_info` miss arm,
  `_resolved_policy` fallback, `_FALLBACK_ENFORCEMENT` x2,
  `schema_error_policy` x2 (containment + gate arms), `_masked_return` floor
  init, `_degraded` message fallback, teardown except floor).
- Oracles (independent: probe policies, `is not` identity pins, spelled
  expectations; spot-read `tests/utils/test_policies.py:1-60`, never
  owner-reading): `tests/utils/test_policies.py`, `tests/test_resource_policy.py`,
  `tests/test_error_policy.py`, `tests/test_schema.py`, `tests/test_list_field.py`
  (stash pins), `tests/extensions/test_operation_state.py`, live
  `examples/fakeshop/test_query/test_{resource,error}_policy_api.py` +
  `test_extension_isolation_api.py` + list/keyset tiers.
- Projections: module/class docstrings stating the isolation contracts
  (`copy_policy`, `canonical_policy`, both policy modules, both extension
  modules, `_SchemaEnforcement`, `PrivateAuthority`); GLOSSARY + spec-047/048
  clauses; `docs/` prose. Describe, never own.

Posited sub-rules (my own decomposition W2-A..H; owners by principle 7):
- W2-A handout-copy discipline. Contract: every consumer-reachable policy
  surface hands out a duplicate, never the authority. Owner: `copy_policy`
  (narrowest: generic `TypeVar`, imports nothing policy-shaped, every
  consumer already imports it; dependency direction wins over any
  flavor-local home).
- W2-B admission canonicalization. Contract: every object entering
  enforcement is re-read + rebuilt + revalidated into a private exact
  instance. Owner: `canonical_policy` (same module; the re-read contract
  lives with the only body performing it).
- W2-C schema enforcement record. Contract: the schema's two resolved
  policies live in a record no consumer-visible name answers with, with a
  constant fallback for never-constructed schemas. Owner: the
  `schema.py::_SCHEMA_ENFORCEMENT` block (the schema owns its enforcement
  record; `PrivateAuthority` is the mechanism, not the rule).
- W2-D explicit extension holding. Contract: a directly supplied extension
  instance's explicit policy is canonicalized at construction into a
  private record and handed out as a copy per read. Owner: the
  `extensions/resource_policy.py::_EXPLICIT_POLICY` block (the entry owns
  its explicit declaration).
- W2-E resource runtime reads. Contract: operation-time arming selection
  (D5a) and request-time authority order (D5b), each with its own gates.
  Owners: `_resolved_policy` + `policy_from_info`, one per seam (each
  narrowest at its seam; two reads, not one rule).
- W2-F error admission read. Contract: contained attribute read with
  fail-closed masking fallback. Owner: `schema_error_policy`.
- W2-G masking application + floors. Contract: one classifier + one
  replacement + one shape gate + one active gate applied at three seams;
  per-entry and whole-response floors. Owner: `mask_execution_result`
  (+ `_degraded` / `degraded_result` floors in the same module).
- W2-H narrowing-only. Contract: a held policy may be tightened freely and
  never loosened, stated once per subject. Owners: `narrowed` (whole-policy
  derivation) + `effective_bound` (per-bound combination) + `_effective_deadline`
  (deadline combination) — three single-owned statements, not one body.

Change challenges (each: change posited + definitions forced):
- W2-C1 third policy flavor needing the handout discipline: `copy_policy`
  is already generic; 0 existing defs move (new declarations compose). CONFIRMS W2-A.
- W2-C2 per-request mutation (resolver writes a handed-out copy): no-op by
  construction (copies at all 6 call sites); hardening the discipline moves
  `copy_policy` only = 1. The 3 non-copy internal reads
  (`armed_resource_policy`, `check_deadline`'s `budget.policy`,
  `_masked_return`'s record read) are package-internal with no consumer path —
  verified by caller census (2+1+1, all package code). `_resolved_policy`'s
  singleton return is re-canonicalized by its sole caller before any bound
  reads it. No second handout body.
- W2-C3 canonicalization semantics change (e.g. reject subclasses outright
  instead of re-reading): `canonical_policy` = 1; all 6 call sites unchanged
  (still call it). CONFIRMS W2-B.
- W2-C4 new canonical entry point (new transport arming path): new
  `_operation_policy`-style call site; 0 existing defs move.
- W2-C5 operation-time precedence change: `_resolved_policy` = 1;
  `policy_from_info` untouched (different authority order). W2-C6 request-time
  authority order change: `policy_from_info` = 1. Refused merge D5a/D5b: arming
  selection among configurations vs authority order among runtime stores;
  different rungs, gates, callers, failure modes (arming never fails closed
  to a copy; request reads always answer copies).
- W2-C7 error admission gate change (`isinstance`->exact or containment
  dropped): `schema_error_policy` = 1 (the WT dirt performs exactly this
  change in exactly this body — concurrent work that incidentally proves the
  count). Both consumers (teardown + per-event seam) unchanged.
- W2-C8 third stored policy on the schema record: `_SchemaEnforcement` +
  settle literal + `_FALLBACK_ENFORCEMENT` literal = 1 rule-site (one record
  def, edited once); `_enforcement` retrieval unchanged.
- W2-C9 new masking seam: composes `mask_execution_result` + gates by name;
  0 existing defs move. Classification change: `_is_unexpected` = 1. Floor
  change: `_degraded` = 1 (whole-response floor composes it via
  `degraded_result`).
- W2-C10 trusted carve-out removed: `effective_bound` = 1. Whole-policy
  narrowing semantics (deadline arm): `narrowed` = 1. Deadline narrowing
  (mirror-earlier rule): `_effective_deadline` = 1. Refused merge of the
  three: whole-policy raising derivation vs per-bound `min` combination with
  a trusted carve-out vs deadline-instant combination with domain admission —
  different subjects, inputs, and failure modes; one body would need a mode
  flag (principle 5).
- W2-C11 mutable policy field (representation-assumption break): moves
  `copy_policy` + `canonical_policy` + both `__post_init__` gates. Count 2
  rule-bodies for one representation change — recorded as a shared-
  representation contract change (the fields-are-primitives assumption stated
  at `_SchemaEnforcement` + `_AcceptedPolicy`), NOT duplication: each rule
  still has exactly one definition, and no landable single owner can hold
  both a no-revalidation handout copy and a re-reading admission copy
  without a mode flag (principle 5). NOT a revision candidate.

Rejections (contract difference + trigger each; standing rejections trigger-checked):
- W2-N1 `_SealPolicy` (`utils/querysets.py:2931`, ORM seal options): internal
  execution options, never a deployment policy, never crosses a consumer
  boundary. Trigger: seal options become deployment-configured. (Converges
  with f12 R9.)
- W2-N2 `_PACKAGE_POLICY_BASELINE` + `_NormalizedPolicyEntry`
  (`filters/sets.py:425/:391`, django-filter anchor selection): lookup-policy
  table for field selection, unrelated subject. Trigger: none (name share only).
- W2-N3 `FetchMode` (`utils/connections.py:191`, "fetch policy"): planner's
  count/probe derivation. Trigger: none (name collision only).
- W2-N4 transport `allowed_operation_types` snapshot (`schema.py`, one-shot
  tuple materialization): per-operation input snapshot, not an authority
  boundary; mechanism cousin of mapping materialize-once, different rule.
  Trigger: the snapshot starts enforcing across requests.
- W2-N5 query-AST `object.__new__` rebuild (`utils/querysets.py:2069`) vs
  `copy_policy`: node reconstruction vs policy handout; different subjects,
  different post-conditions (rebuilt node vs unvalidated duplicate).
  Trigger-checked standing File-`utils/policies.py` rejection: still two
  subjects at HEAD. Trigger: a shared "duplicate without validating" helper
  with one contract.
- W2-N6 `_OperationBoundExtension` (`extensions/operation_state.py:485`,
  indexed `operation-bound-extension-mechanism` family): per-operation
  instance binding + `__init__` refusal; the policy extensions' base, not
  their policy rule. Trigger: none (already indexed elsewhere).
- W2-N7 `PrivateAuthority` (`utils/private_state.py`): shared MECHANISM used
  by W2-C/W2-D, not a second definition of either holding rule (principle 5:
  share the lifecycle, keep the adapters). Trigger: a holding that bypasses
  the mechanism with its own identity-keyed store.
- W2-N8 connection `max_results` has no trusted carve-out: request-time
  resolver input, never a construction declaration — a per-request value must
  never widen the request policy, so the absence is by construction, not an
  omission (axis 6: no contract source requires it; `effective_bound`'s
  carve-out is for field-construction declarations). Trigger: a
  field-constructed connection bound appears without the flag validation.
- W2-N9 error extension holds no explicit policy (vs W2-D): the error policy
  is configured only via `error_policy=` / setting; no `policy=` param
  exists on `DjangoErrorPolicyExtension`. Contract-established asymmetry.
  Trigger: the error extension gains an explicit-policy parameter.
- W2-N10 `isinstance` (error/schema reads at HEAD) vs exact-type (resource
  mirror, entry read) gates: contract-established asymmetry. The error path
  fails toward masking with containment at every read (`masking_is_active`
  try/except, `_degraded` guard, teardown except floor), so a subclass
  cannot disable masking; the resource mirror's values flow into SQL and
  error rendering, so only an exact instance is admittable. Trigger: either
  gate changes without its containment story (the WT dirt IS this trigger
  firing concurrently — exact gate + dropped containment; owned by that
  concurrent work, not this item).
- W2-N11 `resolve_policy` ladder (f12 F1): construction-time precedence over
  SOURCES with shapes + validation + typed rejection. Boundary with this
  family: f12 owns precedence + call discipline (every arm canonicalizes);
  this family owns the copy bodies + runtime reads over RESOLVED objects.
  `canonical_policy` is this family's def and f12's callee; `_PACKAGE_*`
  defs are declaration sites serving two rules (f12's default rung, this
  family's template/authority separation) with different change axes.
  Trigger: an arm stops canonicalizing (f12 owns) or the copy body changes
  meaning (this family owns).
- W2-N12 mapping-consumption hardening inside `resolve_policy`
  (materialize-once, key guards, iteration containment): indexed sibling
  `hostile-mapping-hardening` family (f12 R14 seam). Trigger: owned there.
- W2-N13 seal-policy defaults vs the deployment ladder; W2-N14 per-subject
  rejection grammars: standing File-`utils/policies.py` rejections,
  trigger-checked, still distinct at HEAD. Triggers: as originally recorded.

f12 R1–R5 membership (my independent verdicts, evidence above):
- R1 `_resolved_policy` -> MEMBER of W2-E (operation-time read). R2
  `policy_from_info` -> MEMBER of W2-E (request-time read). R3
  `schema_error_policy` -> MEMBER of W2-F. R4 `_enforcement` /
  `_FALLBACK_ENFORCEMENT` -> MEMBER of W2-C. R5 degrade floors -> MEMBER of
  W2-G. f12/f13 boundary: construction-time resolution (precedence over
  sources, shapes, validation, typed rejection) vs authority isolation
  (private duplicates, runtime read precedence over resolved
  objects/authorities, enforcement storage, masking application, narrowing).
  No site is a definition in both (interface at `canonical_policy` call
  discipline vs body, per W2-N11); nothing dropped (f12 R6–R13/R16 stay
  neighbors, R14 seams to `hostile-mapping-hardening`, R15 IS this family's
  W2-A/W2-B core and is adjudicated here, not merely asserted).

Matrix discharge (against this family's real surface):
1. Cross-flavor mirroring: SEARCHED (census above). Error/resource twins
   share the copy/canonical/resolve bodies; per-flavor admission reads differ
   by contract (W2-N10). No third flavor; name collisions excluded (W2-N1..N3).
2. Sync/async twins: COMPARED BY BEHAVIOR. `bounded_rows`/`bounded_rows_async`
   share `_raw_list_bound`; `check_deadline` is sync-called from both colors;
   the masking teardown is one sync generator entered on both paths. No twin
   definitions of any isolation rule.
3. Derived knowledge: SEARCHED. `max_list_rows` (list_field x2 + `_raw_list_bound`)
   and `max_page_size` (connections) all derive FROM `policy_from_info`, the
   one request-policy reader; fields are read off the returned copy, the
   precedence is never re-derived. Count 1.
4. Inverse/round-trip pairs: SEARCHED. begin/end (lease), stash/clear
   (mirror), mask/idempotent-re-mask (classifier, not a flag). Each pair
   single-owned; settle/recall is W2-N7's mechanism, owned elsewhere.
5. Contracts in another medium: SEARCHED. Oracles listed above spell
   expectations independently (probe policies, identity pins); docstrings +
   GLOSSARY + specs are projections. 0 definitions outside production code.
6. Enforcement by omission: ENUMERATED. `check_deadline` callers at HEAD
   (connection head, relay x2, mutations pipeline, `_raw_list_bound`) match
   the HEAD docstring seam list exactly; every raw-list path funnels through
   `bounded_rows(_async)`; every connection through `resolve_connection` +
   `resolve_relay_max_results`. No member lacks a guard its contract
   requires. WT `types/resolvers.py` additions are concurrent dirt, not HEAD
   omissions. W2-N8 is asymmetry-by-construction, not omission.

### Reconciliation with `## Findings` (read only after the trace above)

Method: every W1 census re-derived with my own `git show HEAD:` / `git grep
HEAD` instruments (never W1's temp copies); every cited line re-read at HEAD;
all 34 freshness prefixes re-hashed; all three type gates re-run
whole-package; the item-scoped diff and all eight WT pins re-verified.
Agreements first, then every difference explicitly. My sub-rule labels
(W2-A..H) map onto W1's 1:1 (A->F1, B->F2, E->F3, F->F4, C->F5, D->F6,
G->F7, H->F8); challenges W2-C1..C11 cover W1's C1..C11 axis for axis.

Adjudication, one line per claim:
- F1 count-1 + owner: CONFIRM. My D1 census matches exactly (1 def + the
  same 6 call sites); my W2-C1/C2 match C1 (third flavor 0, per-request
  mutation no-op, discipline hardening 1). Owner `copy_policy` is the
  narrowest valid (principle 7: generic, dependency direction wins). The
  3 non-copy internal reads + the `_resolved_policy` singleton arm are
  accounted with no consumer path (caller censuses re-derived).
- F2 count-1 + owner: CONFIRM. My D2 census matches (1 def + the same 6
  call sites); my W2-C3/C4 match C2. Owner `canonical_policy` agreed.
- F3 each-single-owned + owner: CONFIRM. `_resolved_policy`,
  `policy_from_info`, `_operation_policy`, begin/end/adopt/resume,
  `_armed_budget` (1+5 readers re-derived), `armed_resource_policy`
  (1+2), `check_deadline` (1+5 callers re-derived) + deadline helpers,
  mirror trio, DST pair: each count 1, no second site. Owner
  `resource_policy.py` + principle-4 lifetime agreed. R1/R2 membership
  confirmed with evidence (arming selection vs authority order contracts).
- F4 count-1 + owner: CONFIRM. My D6/W2-C7 match C5 (gate change 1; the
  WT dirt performs exactly this change in exactly this body —
  concurrent proof of the count). Owner `schema_error_policy` agreed.
  R3 membership confirmed with evidence.
- F5 count-1 + owner: CONFIRM. Record/store/fallback/retrieval each 1;
  the 5 retrieval readers re-derived exactly (setter, both properties,
  `get_extensions`, `_masked_return`). Owner + lifetime agreed. R4
  membership confirmed with evidence.
- F6 count-1 + owner: CONFIRM. Record/store/settle/copy-read each 1.
  Owner agreed. The F5/F6 two-instantiations-are-declarations reasoning
  agreed (independent change reasons per authority kind).
- F7 count-1 + owner: CONFIRM. One body + two gates at the same three
  seams (1+3 each, re-derived), `_degraded` 1+2, `degraded_result` 1+4
  with W1's four labels verified. Owner agreed. R5 membership confirmed
  with evidence (entry + whole-response floors).
- F8 three-statements + owner: CONFIRM. `narrowed` (0 production
  callers, 9 oracle calls re-derived), `effective_bound` (1+3),
  `_effective_deadline` (1+1) each count 1 on its own axes (C9a/b/c
  match my W2-C10); the contrived-change control + principle-11
  reasoning agreed. The standing handout-vs-narrowing separation
  confirmed on fresh evidence (verified: different inputs, outputs,
  error postures). Owner `resource_policy.py` agreed.
- f12 R1-R5 membership: CONFIRMED with evidence each (mapped to
  F3/F3/F4/F5/F7 with contracts + challenges + the `_PACKAGE_` bucket
  reconciliation 7+2+2=11, which matches my own 11-read census).
  f12/f13 boundary clean: construction ladder/twins/mapping arm stay
  f12's, cited as boundaries; nothing dropped (R15's substance IS F1/F2
  here; R14 seams to `hostile-mapping-hardening`, correctly unclaimed).
- R-a: CONFIRM (my N1; trigger adequate). R-b: CONFIRM (my N2). R-c:
  CONFIRM (6 instantiations re-derived; `:282` cites the statement's
  first line, legitimate). R-d: CONFIRM (4 sites/4 contracts
  re-derived; standing rejection trigger-checked). R-e: CONFIRM
  (precedent citation verified in the `_active_budget` comment). R-f:
  CONFIRM (`:190` verified; freshness-by-construction boundary with F2
  correct). R-g: CONFIRM (mechanism-token census negative outside the
  enumerated files, re-derived; relay-cap is a by-name consumer).
  R-h: CONFIRM (refused merge; my W2-C11 substance; trigger adequate —
  both premises gone). R-i: CONFIRM (verified: no per-operation error
  state; read-per-use docstrings; trigger adequate). R-j: CONFIRM
  (verified fresh: typed raises + baseline copy; no half-response
  seam; trigger homes any future floor in F7). R-k: CONFIRM (both
  lines verified; stdlib-spelling separation correct).
- Matrix: axes 1/2/3/5/6 discharge CONFIRMED against the real surface
  (each re-derived: flavor census 4 classes 2 excluded; twins compared
  by behavior; derivation from the one reader; oracles independent by
  spot-read; omission enumerated with HEAD seam list matching callers
  exactly). Axis 4 "inapplicable with reason": ACCEPTED (see D2 below).
- "No new index rows owed": ENDORSED. F1-F8 all adjudicated here with
  CONFIRM verdicts (no explicitly-named new rule left undispatched per
  the run-9 refinement); R-a-R-k are rejections for transcription.
  Worker-0 owes: flip the row with the F1-F8 evidence + transcribe
  rejections. No new rows.
- Pending-execution "None": CORRECT → plain `verified`. Static-decidable
  (census + challenges), nothing moves, gates cited in-tree. No `proof:`
  owed, no `gate:` owed.
- Cells inapplicable by construction: CORRECT. No database, alias, or
  dialect decision in the finding.
- Structural gates + negative controls: ADEQUATE for zero-edit CONFIRM.
  Existing behavioral pins fail the realistic bypasses (authority
  handout fails `is not`; mirror rewrite fails bound pins; wrong-type
  attribute fails fallback pins); identity-based, not name-based. The
  no-new-gate reasoning (byte-duplication uneconomical, name-census
  AST-fragile, explicitly not the shape) is a reasoned scope decision.
- Freshness: 34/34 fingerprints re-hashed, ALL MATCH (comparable; any
  change reopens). WT pins match dispatch 8/8; dirt stat 239/357
  reproduced exactly (no drift on indexed files since submission).
- Zero-edit: CONFIRMED. No `## Implementation`; `git diff
  ITEM_BASELINE --name-only` is the plan edit alone (artifact is
  untracked); status count 461 reproduced; HEAD unmoved at `5c3496e0`.
- AGENTS.md diff check: the tracked item diff is Worker-0's plan edit
  alone; W1 touched no tracked files. Ruff on touched tracked paths:
  VACUOUS (none). Type gates re-run whole-package in the shared tree:
  mypy clean (119 source files), basedpyright 0/0/0, check_any 130
  allowed at 90 sites — all three match W1's informational numbers
  exactly.

Differences, every one explicitly (all verdict-neutral; none names a
consolidation, so none spends the verdict):
- D1 (my trace's error, corrected): W1's `_resolved_policy` "(1 + 2:
  arming call, no-scope fallback)" is correct; my trace said "sole
  caller". The second caller (`on_parse` fallback,
  `extensions/resource_policy.py:1671`) verified. Def count 1 either
  way; F3 stands.
- D2 (axis 4 discharge style): W1 rules round-trip inapplicable (one-way
  maps, no decode half); I searched lifecycle pairs (arm/disarm,
  publish/remove). W1's reason is accurate for the transform core, and
  under my stricter reading each pair-half is single-owned with no
  second site — no consolidation missed either way. ACCEPTED with
  supplement.
- D3 (file-count labels): W1's "(6 sites, 5 files)" / "(6 sites, 4
  files)" vs my production-only 3/3. Reconciled as convention: W1's
  tallies include the owner-tier oracle file
  (`tests/utils/test_policies.py`) — 4 prod + 1 oracle = 5, 3 prod + 1
  oracle = 4. Consistent under that reading; no site unassigned under
  either. The def + call-site counts (what the verdicts rest on) match.
- D4 (C1 analysis): W1's C1 moves `copy_policy` alone, reasoning the
  admission side "constructs through the validated constructor". My
  W2-C11 analyzed the alternative fix placement (both bodies move).
  Dissolved on analysis: W1's reading is the sharper one — a mutable
  member is handled once in `__post_init__` (where domain validation
  lives by contract), `canonical_policy`'s body is unchanged, and
  `copy_policy`'s body moves precisely because it bypasses the
  constructor by design. Under both placements the F1 count is 1 and
  R-h stands. Agreed with W1.
- D5 (C5 phrasing): "a policy subclass is admitted where only an
  `ErrorPolicy` passes today" reads oddly against HEAD's `isinstance`
  gate (subclasses already pass the gate; containment carries the
  trust). The count (1: gate + containment in one body) is right
  regardless of direction; scratch-prose looseness only.
- D6 (F3 chain phrasing): `scan_document_text` reads the armed snapshot
  via `armed_resource_policy()`, not `_resolved_policy`'s return
  directly; naming it among that function's callers' readers is
  imprecise. The security conclusion (policy never escapes to consumer
  code) verified true. Scratch-prose looseness only.
- D7 (R15 label): W1 never names f12's R15 (the one "R15" hit in this
  file is my own trace line). R15's substance — the copy mechanics
  belong to this family — IS adjudicated as F1/F2, and the dispatch
  required confirm-or-refuse only for R1-R5. Nothing dropped.
- D8 (fingerprint table): `tests/utils/test_connections.py` is cited as
  an oracle home in F3 (verified: stash pins at HEAD) but carries no
  table row. The verdict evidence (census + challenges on production
  bytes) does not depend on its bytes. Record-completeness note only.
- D9 (my N9 vs W1's R-i): complementary asymmetries, not a conflict.
  R-i covers the operational side (no per-operation error state);
  my N9 covers the configuration side (no `policy=` param on
  `DjangoErrorPolicyExtension` — verified: no `__init__` override, the
  class docstring resolves configuration to the schema). No second
  holding exists to consolidate; F6's resource-scoped contract stands.
- D10 (granularity): W1's R-f (mapping-arm construction) and R-k
  (`replace` spelling) are finer-grained than my trace (I folded the
  former into N12, never posited the latter). Both verified correct.
  No conflict — W1 more thorough.

Stress synthesis (zero-edit family: independent consolidation search):
the dispatch's four probed changes force — third flavor 0 (generic
mechanics), per-request mutation no-op by construction (copies at all
6 sites; 3 internal non-copy reads verified consumer-unreachable),
new masking seam 0 (composes by name), narrowing-that-widens 1 per
statement with the merge refused on mode-flag grounds. The only
count-2 shape (mutable-field representation break, D4) has no landable
single owner under either fix placement. No `revision-needed`
candidate; no `blocked` position (nothing would land on concurrent
dirt — zero edits).

Defects: none found. Nothing encountered meets the defect bar (contract
row + feasible project shape + reaching input); D1-D10 are
verdict-neutral record notes in the f12-D-note precedent and live here,
not under `## Defects`. W1's sections stay byte-intact.

Verdict: `verified` (plain — no `proof:` remains, no pending execution).
Zero-edit CONFIRM of single ownership across F1-F8; f12 R1-R5 confirmed
as members with evidence; R-a-R-k carry contract differences + triggers;
no new index rows owed (endorsed); 0 defects.
