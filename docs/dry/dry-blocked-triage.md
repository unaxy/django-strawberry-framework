# DRY review: blocked-triage

Status: verified
Run: 0.0.15 2026-10-10-14

## System trace

Population: the 18 Family rows whose verdict is blocked-on-hunt (13
ticked artifacts with zero-edit F1 CONFIRMED findings + 5 unticked
nominations in 3 Folder artifacts). The 2 record-only rows
(`globalid-setting-snapshot`, `relay-pk-suppression-read-mirror`)
stay unapplied by maintainer decision and are not triaged.
Method: every site re-derived at current bytes against
`git show HEAD:<path>` (HEAD `23b5f421`); old line numbers never
trusted. Each site line is HEAD-clean (context line or outside any
hunk) or hunt-dirtied (`+`/`-` line in a hunk matching the
truth-migration / except-deletion / review-F1 vocabulary with no
`## Owned changes` row); contiguous dirt blocks the edit. Each row
is judged fresh under bar 4A; prior F1/R1+/trigger records are
inputs, never verdicts.
Population notes (say, not silently change): f40's inclusion is
CONFIRMED (plan index + Families rows both verdict blocked-on-hunt).
f37's plan row says "blocked on concurrent dirt" (the
except-`BaseException`-deletion population, not truth-migration):
inclusion confirmed, attribution wording differs. f46 re-derives to
count-2: site A (inputs five-gate) retired under committed drift
(`899cb35b` per verified FF-2; no five-spelling in inputs.py at WT
or HEAD today).

## Triage

| rule | bar 4A? | landable? | action |
|---|---|---|---|
| e8 `queryset-seed-and-model-read` | yes: 2-edit obligation, db-routing (alias pin) + multi-line logic each, fix deletes a copy into the existing owner | no: batched inline WT-only, `relay.py @@ -310,6 +329,99` | stays-blocked |
| e9 `prepared-view-handoff-shape` | yes: payload-shape change forces 2; each half a multi-statement protocol (guarded read + stamp / validate + match + delattr) | no: pack mount-read dirt, `middleware/request_body.py @@ -245,10 +246,7` (unpack + owner HEAD-clean) | stays-blocked |
| f33 `active-terms-purity-agreement` | no: each arm is one comparison + one verdict raise (single-expression check), no security facet, no drift | no: render lines dirt, `orders/sets.py @@ -648,18 +657,18` (re-derived) | below bar: active-terms-purity-agreement — single-expression verdict arms — trigger: an arm gaining further branches or the verdicts diverging |
| f36 `canonical-input-provisional-name` | no: guard restatement is one f-string; suffix half byte-identical (no drift) | no: guard f-string dirt, `rest_framework/resolvers.py @@ -1275,7 +1287,7` (owner HEAD-clean) | below bar: canonical-input-provisional-name — one-expression restatement — trigger: restatement growing branches or suffix spellings diverging |
| f37 `generated-choice-enum-name-template` | no: two one-line f-string templates; naming, no drift (plan: "blocked on concurrent dirt", except-deletion pop.) | no: D1 dirt, `types/converters.py @@ -944,32 +929,15` (D2 HEAD-clean) | below bar: generated-choice-enum-name-template — single-expression twins — trigger: template gaining branches or copies drifting |
| f38 `mutation-discovery-own-snapshot-read` | yes: window/timing change forces 2; each body multi-branch (snapshot arm + live chain + miss); helper carries the full derivation | no: both bodies dirt, `forms/sets.py @@ -194,55 +199,78` + `rest_framework/sets.py @@ -788,20 +769,27` | stays-blocked |
| f40 `registered-djangotype-definition-validation` | yes: proof-arm change forces 2; each proof multi-arm (~12-20 lines); predicate carries the full proof (inclusion CONFIRMED per plan rows) | no: all three paths dirt (`testing/relay.py @@ -63,25 +64,21`; `list_field.py @@ -174,57 +172,37`; `registry.py` 15 hunks) | stays-blocked |
| f41 `graphql-name-gate` | no: one boolean conjunct per gate; grammar fixed by the external GraphQL spec (4A: not a rule we own) | no: both gate hunks dirt (`types/base.py @@ -1386,56 +1380,53`; `types/definition.py @@ -249,34 +250,28`; import `@@ -60,13 +60,15`) | below bar: graphql-name-gate — single-expression externally-specified grammar — trigger: a package-owned naming rule beyond the spec with multi-line logic at both gates |
| f42 `mro-map-key-lookup` | yes: copies ALREADY drifted (identity-scan vs hash-dispatch, divergence execution-verified) + real scan logic each | no: every touch line dirt (helper-intro `converters.py @@ -349,17 +351,27` + legs + CLI `inspect @@ -510,8 +515,8`); audit-flagged input (c) DOESN'T hold: R1 stands, count stays 2-in-WT (see entry) | stays-blocked |
| f46 `canonical-container-membership` | no (count re-derived 3→2, site A spent): five-tuple constants + one-expression gate; dispatch holds the only real logic; robustness, not security | no: gate B + dispatch dirt (`write_transaction.py @@ -829,6 +835,19` + `@@ -1007,17 +1023,7`; `canonical.py @@ -70,33 +70,33`) | below bar: canonical-container-membership — constant + single-expression gate — trigger: per-member branch logic or gate/dispatch divergence |
| f60 `bound-filter-model-field-walk` | no: three tolerant attribute reads per site, zero branches (4A excludes attribute reads); _meta split is migration in flight, not drift | no: site-1 _meta line dirt, `filters/base.py @@ -738,7 +705,7` (site 2 HEAD-clean); audit-flagged input (b) HOLDS: walks identical modulo receiver except the _meta line | below bar: bound-filter-model-field-walk — lenient read chains — trigger: walk gaining branches or spellings diverging on the model-absent contract |
| f63 `write-pipeline-alias-recovery` | no: db-routing relevant BUT the fix is a new helper wrapping one conditional expression (4A bars exactly this) | no: D-b WT-only, `relay.py @@ -310,6 +329,99`; audit-flagged input (a) HOLDS as fact: D-a WT :315-323 all HEAD-clean lines — no partial landing (below bar + twin-consistency refusal + helper seat in dirt) | below bar: write-pipeline-alias-recovery — one-expression helper fix — trigger: recovery growing multi-branch logic (alias-pair selection, pin-or-fail) or D-a/D-b drifting |
| f64 `canonical-unordered-partition` | no: one-expression halves + constant tables; halves agree (no drift); fix is two one-expression predicates | no: U table+gates + O or-chain + owner hunks all dirt (`inputs.py @@ -515,19`/`-565,14`/`-806,37`; `write_transaction.py @@ -1047,20 +1053,20`; `canonical.py @@ -1,4`/`-70,33`) | below bar: canonical-unordered-partition — single-expression inverted halves — trigger: halves gaining per-side branch logic or diverging |
| `lookup-table-declared-filters-read` (filters FAM-4) | no: one static_attr read + cast x2 in one flow (single expression) | no: both reads dirt, `filters/inputs.py @@ -1043,7 +1075,11` + `@@ -1088,7 +1124,11` | below bar: lookup-table-declared-filters-read — one read spelled twice — trigger: read gaining fallback/validation branches or the two reads diverging |
| `custom-loop-queryset-return-assertion` (filters FAM-5) | no: one isinstance assert + message x4; the two wordings are intentional per-site subjects, not drift | no: all four dirt, `filters/sets.py @@ -4037`/`-4292`/`-4418`/`-4429` | below bar: custom-loop-queryset-return-assertion — single-expression asserts — trigger: assertion gaining branches (per-site accepted types) or predicate divergence |
| `mutation-payload-name` (mutations FAM-1) | no: one f-string suffix x2; fix is a new helper wrapping one f-string | no: site B dirt, `mutations/fields.py @@ -254,7 +277,7` (site A HEAD-clean) | below bar: mutation-payload-name — single-expression suffix twins — trigger: suffix rule gaining branches or spellings diverging |
| `static-read-callability` (mutations FAM-2) | no: one boolean expression x2 (helper exists, so no machinery — but 4A(ii) still fails) | no: helper WT-added + inline dirt, `mutations/sets.py @@ -1038,27 +1016,28` | below bar: static-read-callability — single-expression callability twins — trigger: recognized-descriptor set growing arms or sites diverging |
| `real-class-membership-test` (utils FAM-1, count-6) | no: one any() expression x6 (docstring 2-word drift is prose, not code); fix needs a new one-expression helper | no: all six spellings WT-added `+` lines (`inputs.py @@ -515,19`; `write_transaction.py @@ -829,6`; `resolvers.py @@ -757,6`; `errors.py @@ -194,109`; `directives.py @@ -62,18`; `sets_mixins.py @@ -595,16`) | below bar: real-class-membership-test — one-expression mechanism x6 — trigger: mechanism gaining policy branches or copies diverging in code |

## What shrinks

### e8 `queryset-seed-and-model-read`

The rule: a fresh unevaluated base queryset for a model, optionally
pinned to a database alias — the model's `_default_manager`,
conditional `.using()`, detached via `.all()`. Two independent
definitions remain: `utils/querysets.py::base_queryset` (WT :289-315,
the owner: abstract-model guard plus conditional pin plus detach,
composed by name at 14 package call sites) and the batched inline in
`relay.py::_resolve_real_pks_batched` (WT :407-413: comment plus
`Manager | QuerySet` annotation plus `_default_manager` plus
conditional `.using()`, no `.all()`). The single inline retired via
committed drift: `_resolve_real_pk` now composes
`base_queryset(model_for(resolved_type), using=using)` at WT :324-329,
byte-identical to HEAD :305-310, and the owner's relay-exclusion
docstring clause is gone with it. The concrete change that today
takes two edits: any manager-choice or alias-pinning revision (extend
the abstract-model guard, change the conditional-pin shape). Miss the
batched site and the batched NodeID-to-pk mapping seeds on the wrong
manager or alias: a wrong-database lookup that reports an existing
row not-found, alias-unobservable on one database. The owner stands
by principle 7: it already owns seed responsibility, every legitimate
consumer (including relay, which already imports both `base_queryset`
and `model_for` from that module at WT :74-76) reaches it with no new
edge. The landing is one shape: the batched inline becomes the same
one-line owner call (no import edit needed); the copy is deleted, no
helper is created. Behavior staying distinct: the `__in`
group-mapping versus the single `.filter().first()` chain, the
`id_attr == "pk"` early-outs, and the alias recovery above each site
(the adjacent f63 rule, closed below-bar separately). Landing note:
routing through the owner adds the `.all()` detach to the batched
path; that is behavior-preserving per the family's Django-source
proof (a fresh manager's `.all()` is an unevaluated clone, and no
test pins survival of a contract-violating `.all()` override). Net
package lines: about minus 5. It clears 4A because the obligation is
database-routing relevant with multi-line logic on both sides, and
the fix deletes a copy into an existing owner with zero machinery.

### e9 `prepared-view-handoff-shape`

The rule: the request-scoped `(mount token, prepared view instance)`
2-tuple handoff — stamped only when the resolved callback carries a
mount, consumed only when the stamp is an exact 2-tuple whose slot 0
is the consuming mount's own token, exactly once. Two independent
definitions: the pack in
`middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.process_view`
(WT :250-252: guarded mount read plus conditional tuple stamp) and
the `prepared_view` closure in `views.py::_RequestBodyBoundaryMixin.as_view`
(WT :583-588: read plus strict validate plus identity match plus
`delattr` plus return). Neither invokes the other; they agree by
parallel spelling. The concrete change that today takes two edits: a
payload-shape revision (slot order, arity, container). Miss one side
and the middleware stamps what the view rejects, so the prepared view
is silently unused and dispatch falls back to the upstream callback —
the boundary ordering the protocol exists to enforce is lost with no
error. The owner is `django_strawberry_framework/_boundary_ordering.py`
(HEAD-clean today) via a pack helper plus a consume helper, by
principle 7: it already owns exactly this protocol (marks, method
name, exemption, prose) and both sites already import from it, so the
migration adds no edge; `views.py` is excluded by dependency direction
(the middleware must run the boundary without importing views) and the
middleware by responsibility (it owns where the boundary runs, not the
grammar both ends share). The landing: the owner gains
`stamp_prepared_view` (guarded read plus conditional stamp,
re-derived against the landed read bytes) and `consume_prepared_view`
(read plus validate plus match plus `delattr` plus return); the pack
block becomes one stamp call and the closure body one consume call,
with the sync/async arms untouched. Behavior staying distinct: token
creation (`mount = object()` plus the callback stamp) stays in
`as_view` as the single-owned representation facet; the `None`-gate
skip and the single-consume travel with their halves; boundary,
`setup`, CSRF, and recognition behavior are untouched. Net package
lines: about plus 30 helper lines with docstrings, minus 8 call-site
lines. It clears 4A because each half carries multi-statement
decision logic (guarded read plus conditional stamp; three-part
validation plus identity match plus destructive consume), and each
helper wraps a genuine protocol half rather than one expression.

### f38 `mutation-discovery-own-snapshot-read`

The rule: when a discovery default runs during class validation
(before the metaclass stamps the snapshot) it reads the backing class
from live `Meta`; on every later call it reads the class's OWN stamped
snapshot, never an inherited one. Two independent definitions:
`forms/sets.py::_default_mutation_get_form_fields` (WT :202-213:
own-namespace snapshot read plus window if/else plus tolerant live
chain plus typed miss raise) and
`rest_framework/sets.py::SerializerMutation.get_serializer_for_schema`
(WT :783-794: own-namespace read plus window conditional plus
pass-through miss). The concrete change that today takes two edits: a
stamp-timing or own-read revision (snapshot slot rename, validation
order change, own-namespace rule change). Miss one flavor and a
subclass redefining its backing class validates against the parent's
snapshot — the default hook discovers the wrong serializer's or form's
fields — or a post-declaration `Meta` mutation leaks into the input
shape; the window-A and window-B oracles each pin one half of this
failure. The owner is `mutations/sets.py` via a new
`snapshot_or_meta_backing(cls, slot, key)` helper, by principle 7: it
owns the metaclass factory (the source of the stamp-timing fact) and
the snapshot record, and both flavors already import it at runtime, so
the helper adds no new edge — while the forms-default alternative
would force a `rest_framework` to `forms` sibling-flavor runtime edge
for machinery, which principle 7 forbids. The landing: the helper
carries the own-snapshot arm (plain `getattr` on the slotted record,
required because `static_attr` would return the member descriptor
uninvoked) plus the tolerant live arm plus the `None` miss; D1 becomes
one helper call plus its unchanged typed raise plus `get_form_fields`,
and D2 one helper call plus its unchanged pass-through. Behavior
staying distinct: miss strictness per flavor (typed raise versus
pass-through) and slot/key selection as helper arguments. Net package
lines: near-zero (the helper approximates the two deleted bodies). It
clears 4A because each body carries real multi-branch derivation
logic (two timing windows plus a tolerant read chain plus a miss
verdict), and the helper carries that full derivation rather than
wrapping one call.

### f40 `registered-djangotype-definition-validation`

The rule: a probe counts as a usable `DjangoType` class if and only
if it is a `DjangoType` subclass whose attribute definition `is` the
registry's definition for it and whose `origin is` the probe — a
four-arm proof (subclass, attribute, registry, origin). Two
independent definitions: the step-1a block in
`testing/relay.py::global_id_for` (WT :67-86: subclass gate plus
attribute read plus registry read plus origin-identity proof plus
fused raise) and the identity core in
`list_field.py::_validate_djangotype_target` (WT :188-199: class and
subclass message gates plus attribute read plus registry read plus
triple-identity proof plus raise). The concrete change that today
takes two edits: a proof-arm revision (inherited-definition
acceptance, identity weakening, a new arm). Miss one site and the
testing helper mints ids for types the list field rejects, or rejects
types the field accepts — the construction-time guards disagree about
which classes are usable, and the 23-node oracle suite pins their
agreement. The owner is `registry.py` via a new
`registered_own_definition` predicate returning
`DjangoTypeDefinition | None`, by principle 7: the registry owns
registration and canonicality (`register_with_definition` writes the
pair the proof verifies; `get_definition` is the canonical read), and
both consumers already import it, so zero new import edges — while
routing the testing helper through `list_field.py` would import
sibling-flavor machinery against its import-light contract, and the
base validator's factory messages plus resolver seam are the wrong
envelope for a mint guard (`DjangoType` arrives via an in-function
import on the `definition_for_graphql_name` cycle precedent). The
landing: the predicate carries the four-arm proof; the base validator
keeps its class/subclass message arms plus resolver seam and replaces
the proof block with one owner call plus its existing unregistered
message; the testing helper replaces its proof block with one owner
call plus its existing fused message. Behavior staying distinct:
per-subject messages, the resolver-callability seam, the Relay-shape
fifth guard, and the finalized gate plus stamp read below the proof.
Net package lines: near-zero (the predicate approximates the two
deleted proof blocks). It clears 4A because each proof carries real
multi-arm decision logic (~12-20 lines each), and the predicate
carries that full proof rather than wrapping one expression.

### f42 `mro-map-key-lookup`

The rule: the first class in the field's real MRO keying a
model-field class map, or absence — varying on MRO source, scan
order, membership test, and snapshot. Two independent definitions in
the worktree (three at HEAD): `types/converters.py::_class_map_lookup`
(WT :359-375: registry snapshot plus nested identity-scan loop serving
both value legs, `scalar_for_field` at :390 and
`_field_output_type_for` at :540) and
`management/commands/inspect_django_type.py::_matched_scalar_key`
(WT :517-520: plain-`in` MRO walk plus concrete-name fallback). The
copies have already drifted, and that drift is execution-verified:
the helper matches keys by identity (never `__hash__`/`__eq__`) while
the CLI predictor uses plain `in`, so hostile input takes the typed
path on one half and hash-dispatch on the other. The concrete change
that today takes two edits: a lookup-semantics revision (membership
test, snapshot posture, MRO source). Miss the CLI site and the
predictor names a map row the resolver did not fire — the inspect
command's converter column disagrees with construction behavior.
Audit-flagged input (c) does NOT hold: the
`utils/converters.py::convert_with_mro` phase-2 walk (WT :144-148) is
not a third counted copy. It is textually twin but contract-distinct:
it walks a caller-supplied registry over disjoint (forms/DRF/filter)
key spaces, runs preemptibly after phase-1 `isinstance` prechecks
toward a phase-3 raising fallthrough, and makes its own snapshot
(`dict` copy with a GIL-atomicity rationale) and MRO-source
(`type(field)`) decisions. A change to the lookup rule (pair return,
miss posture, owned-map rows) never moves it, and a change to the
dispatch skeleton never moves the counted pair — different contracts,
different reasons to change — so R1's listed-not-counted exclusion
stands and the count stays 2-in-WT (3-at-HEAD). The owner is
`types/converters.py` via one key lookup returning the `(key, value)`
pair or `None`, by principle 7: it owns both key spaces and the WT
value helper, the CLI already imports from it (no reversal), and it is
the narrowest module every legitimate consumer can import — while
`utils/converters.py` owns disjoint flavor dispatch and hosting there
would move the rule away from its maps. The landing: the pair-return
lookup (snapshot via `dict` copy, no fallthrough verdict inside, since
subscripting after an identity scan would re-dispatch `__hash__`);
`scalar_for_field` becomes pair-or-raise with its message byte-identical;
`_field_output_type_for` becomes pair-value-or-`None`;
`_matched_scalar_key` composes the owner and deletes the last
plain-`in` walk, closing the divergence; `_class_map_lookup` and
`_MISSING` retire if subsumed under the constraint of exactly one walk
body. Behavior staying distinct: miss postures per site (raise, `None`,
fallback name), the direct path-map subscript, and the skeleton's
prechecks plus factory. Net package lines: near-zero. It clears 4A
because the copies already drifted on a load-bearing axis with real
scan logic on both sides, and the fix is a genuine extraction (pair
return, snapshot, subsumption) rather than a wrapper.

## Freshness

HEAD `23b5f421`; pins are WT `git hash-object` / HEAD `git rev-parse`
(8 chars), re-derived this run. Production: `relay.py` 9257a51b /
025f2a6a; `utils/querysets.py` 641b158e / 4d8a3d39;
`middleware/request_body.py` 7422cee9 / e038bdd1; `views.py` 72ec3e2d /
0492167d; `_boundary_ordering.py` f91ccd73 clean; `orders/sets.py`
fd453bec / 2d35adfa; `utils/inputs.py` 0b8d3daa / c199eaa4;
`rest_framework/resolvers.py` 4d05a330 / 14ffc9c8;
`types/converters.py` d8905d0a / 38f102ab; `serializer_converter.py`
077a4ee2 / e804b074; `forms/sets.py` 6681c33c / 946701af;
`rest_framework/sets.py` d3a16114 / 2ecaab56; `mutations/sets.py`
6f2fa2f9 / a123aea8; `testing/relay.py` 8a31c1ad / f94b3577;
`list_field.py` b5cfe957 / c84cefb2; `registry.py` c5aa2050 / 47b52c52;
`types/base.py` f42bcee3 / a63b7edf; `types/definition.py` dfad92ca /
2562cb6f; `inspect_django_type.py` 86785d55 / 86a308ab;
`utils/converters.py` 53ce2b2e / eb0f708d; `utils/canonical.py`
23a7c41a / a1209117; `utils/write_transaction.py` 50909be8 / 2b9f861c;
`filters/base.py` 77c2e7a6 / a43513a7; `filters/inputs.py` a269a3fe /
d77a113c; `filters/sets.py` d6bb78d1 / b8740187; `mutations/inputs.py`
a9428e11 / f821661e; `mutations/fields.py` 62a15151 / 3908afa9;
`utils/errors.py` e9572ea9 / 9cf4e952; `utils/directives.py` 23421f6b /
09e0de24; `sets_mixins.py` 616dbf20 / dd358f85. Artifacts read
(`git hash-object`, untracked): e8 94f3c58b, e9 2fe58d8b, f33
10a1aee2, f36 ff9ae246, f37 f1f0ae34, f38 14782e58, f40 e6c3720b, f41
5fe47f0b, f42 73b524e9, f46 1695273e, f60 fd3f7ef6, f63 661ba002, f64
88a779b8, folder-filters 69637e95, folder-mutations 3d9abb8f,
folder-utils 1efc52d7, project a712509e, plan d2392e1d, DRY.md
cd9548e5, worker-1.md d5cbc7c5, AGENTS.md ea65c820, START.md 0abfeda6.
Any fingerprint change reopens the affected rows.

## Defects

None found in this trace (read-only item; the batched-seed `.all()`
delta and the unpinned `__` oracle arm ride their family records).

## Pending execution

None (no suites in this item).

## Judgment

Five rows meet bar 4A (e8, e9, f38, f40, f42) and stay blocked on
hunt-dirtied lines with zero landable surface; thirteen fall below
the bar as single-expression, constant, or externally-specified
rules and close with triggers. No row is landable now, so no
re-dispatch is owed until the concurrent lines land.

## Independent verification (Worker-2)

Own judgments, formed from the 13 F1 records + 5 FAM nominations + project CC-6/7/8 + live-vs-HEAD bytes before reading `## Triage`; bar = 4A strict (named change; logic/security/drift; no machinery); landable = migration touches no hunt-dirtied line. Reconciliation follows each row after `→`.
- e8: meets (alias-pin change → owner + batched inline; db-routing + multi-line both sides; fix deletes the copy) / blocked (`relay.py @@ -310,6 +329,99`, WT-only batched) → agree.
- e9: meets (payload-shape change → pack + unpack; guarded-read+stamp / validate+match+delattr; helpers wrap protocol halves) / blocked (`middleware/request_body.py @@ -245,10 +246,7`) → agree.
- f33: below (same-method arms; one comparison + one verdict raise each; no security facet, no drift) / blocked (`orders/sets.py` render hunk) → agree.
- f36: below (guard restatement is one f-string; suffix half byte-identical, no drift) / blocked (guard line dirt) → agree.
- f37: below (two one-line templates; fix would wrap one expression) / blocked (D1 except-deletion hunk) → agree.
- f38: meets (timing change → both bodies; snapshot arm + live chain + miss each; helper carries the derivation) / blocked (both bodies dirt) → agree.
- f40: meets (proof-arm change → both proofs; ~12-line 4-arm proofs; predicate carries the proof) / blocked (all three paths dirt) → agree; inclusion confirmed (plan Families row verdicts blocked-on-hunt).
- f41: below (one boolean conjunct per gate; grammar fixed by the external GraphQL spec, not a rule we own) / blocked (both gate hunks dirt) → agree.
- f42: meets (identity-scan vs hash-dispatch drift, execution-verified; real scan logic; pair-return extraction) / blocked (every touch line dirt) → agree.
- f46: below (count re-derived 3→2, site A spent; five-tuple constants + one-expression gate; C5 is robustness, not security) / blocked (gate B + dispatch dirt) → agree.
- f60: below (three tolerant attribute reads per site, zero branches; the _meta split is TR104 in-flight migration, not drift) / blocked (site-1 `_meta` line dirt; site 2 HEAD-clean) → agree.
- f63: below (db-routing relevant BUT the fix is a new helper wrapping one conditional expression — exactly what 4A bars) / blocked (D-b WT-only; D-a lines HEAD-clean, no partial landing) → agree.
- f64: below (one-expression halves + constant tables; halves agree; fix is one-expression predicates) / blocked (both halves + owner dirt) → agree.
- lookup-table-declared-filters-read: below (one static_attr read + cast ×2 in one flow) / blocked (both reads dirt) → agree.
- custom-loop-queryset-return-assertion: below (one isinstance assert + message ×4; two wordings are intentional per-site subjects, not drift) / blocked (all four dirt) → agree.
- mutation-payload-name: below (one f-string suffix ×2; fix wraps one f-string) / blocked (site B dirt; site A HEAD-clean) → agree.
- static-read-callability: below (one boolean expression ×2; existing helper, so no machinery — but 4A(ii) still fails) / blocked (helper WT-added + inline dirt) → agree.
- real-class-membership-test: below (one any() expression ×6; is_subclass/negated spellings are the same rule, not code drift; fix is a one-expression helper) / blocked (all six WT-added) → agree.
Challenge (a): no meets-bar row pushes down — e8/e9/f38/f40 carry multi-line logic each side with non-wrapper fixes; f42's drift is execution-verified on a load-bearing axis. Challenge (b): no below-bar row hides a core — f33's verdict is a constant-ish sentence in one method, f46/f64 duplicate constants + single expressions, f63's only fix is the barred wrapper, row-5's spellings agree semantically.
Audit inputs: (a) HOLDS — D-a WT :315-323 all context lines (the import `-` line is HEAD-only), no partial landing (below bar + twin-consistency + seat in dirt); (b) HOLDS — walks identical modulo receiver except the `_meta` line (:707-709 vs :1278-1280); (c) rightly "doesn't hold" as a flag — R1 stands, `convert_with_mro` phase-2 (WT :144-148) is contract-distinct (caller-supplied registry, disjoint key spaces, preemptible phase), count stays 2-in-WT.
f46 re-derivation verified: `_hashable_meta_value` + `_META_CONTAINER_TYPES` 0 hits at WT and at HEAD `23b5f421`; FF-2 + `899cb35b` citations exact. The 2 record-only rows were correctly left out (plan + artifact agree).
Fingerprints: all 30 production pins re-derived (`git hash-object` WT + `git rev-parse HEAD:`) — 30/30 match; artifact pins spot-checked 5/5 with one explained delta (plan blob moved by Worker-0's own post-submission dispatch appends — owner movement, verdict-neutral).
Shape caps pass: trace 21, table 18 one-liners, freshness one block, defects 2 lines, judgment 5, total 308 = 100 + 208 shrinks. Pin nits, all verdict-neutral (content as described, same hunks): e9 pack :250-252 (actual :249-251), e8 batched :407-413 (seed :408-412), f40 proofs ±2 lines.
Verdict: every row's bar call and block call holds on fresh bytes; landable 0 stands; no re-dispatch owed. Status → verified.
