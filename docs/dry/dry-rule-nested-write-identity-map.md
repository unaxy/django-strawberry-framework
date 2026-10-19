# DRY review: `nested-write-identity-map`

Status: verified
Run: 0.0.15 2026-10-11-20

## System trace

Target: `_SERIALIZER_OPERATION_NESTED_WRITE_METHOD` ([sets.py][sets] live :295-298,
HEAD :304-306) + its sole reader :379 inside `_validate_serializer_nested_fields`.
Re-derived the Worker-0 evidence claim by claim, trying to disprove; every claim held.
Domain chain, all at live bytes: the sole production caller :697 passes the local bound at
:612 `operation = require_non_delete_operation(...)`; no reassignment between (:700/:714/:726
are reads); the whitelist returns `truth.text(operation)` iff it is in
`NON_DELETE_WRITE_OPERATIONS`, else raises ([mutations sets][msets] :136-151). Membership
re-derived from the 4-row registry ([operations][ops] :35-87): create (form T), update
(form T), delete (form F), form (excluded) -> exactly {"create","update"}, pinned by
`test_derived_mappings_and_sets` ([test-ops][testops] :119). `truth.text` copies through
the base `str` slot (`type(v) is str` proved live), so the value reaching :379 is value-
AND type-identical to the map's literals. Reader census (whole-repo rg): exactly 1 (:379);
zero test/example callers of the map; direct-call tests pass only "create"/"update"
([test-sets][testsets] :1724-1930). Spec sweep: no `spec-*.md`/`SPECS` sentence names the
map -> no spec rewrite owed. The prior file-item rejection
(`serializer-write-method-vs-operations-vocabulary`, R-ops) stands untouched: it rejected
FOLDING the map into the DRF-free vocabulary module; this item DELETES it, adding no DRF
axis anywhere.

## Verification

### Matrix

1. Cross-flavor: forms/model flavors carry no write-method map (only the validated snapshot
slot); no mirror. 2. Sync/async twins: class-creation sync validation; no twin. 3. Derived
knowledge: THE find - the map re-spells "method name = operation name" on a
whitelist-closed domain. 4. Round-trip: no method->operation inverse anywhere. 5. Other
media: docstring bullet + error message both key off `write_method`, unchanged; the one
unique comment token (`raise_errors_on_nested_writes`) moved to the use site. 6. Omission:
family {create, update} both enforced (one override test per member); no missing member.

### Challenges

- Third registry verb (a new `supports_form_mutation` row): with the map, a raw `KeyError`
at :379 (untyped, escapes the envelope) + 1 map edit; without it, a typed
`ConfigurationError` demanding the new override (`None is None` on the missing attr), and
the check moves only if the method name differs from the verb. The map is no designed gate.
- DRF renames a write method: 1 edit either way (map value vs a new mapping). Symmetric.
- Override-policy change (e.g. demand both overrides): the check site only, either way.
Bar verdict: an honest principle-11 deletion (abstraction with no responsibility), not a
2-definition count - the removed site carries no logic.

## Findings

### F1 - delete the identity map (confirmed, implemented)

- **Contract + variation.** operation -> DRF write method; identity on {"create","update"}.
- **Sites + roles.** Definition: the dict (deleted). Consumer: :379 (now `operation`).
Oracles: create/update override tests + empty-mapping + snapshot tests (all unchanged).
Projection: the use-site comment (moved rationale incl. `raise_errors_on_nested_writes`).
- **Challenges.** Above; the removed site moves on none of them with real logic.
- **Owner + lifetime.** No owner needed: the whitelist owns the domain, DRF owns the names.
Nothing stored, so no lifetime.
- **Migration.** Dict + stale comment deleted; :379 is `write_method = operation` + comment.
- **Shrinkage.** -13/+4 lines in [sets.py][sets]; no new helper, flag, or registry.
- **Distinct behavior.** None on the reachable domain (proof below); unreachable third values
fail loud either way (`KeyError` before, `ConfigurationError` after).
- **Behavioral proof** (`execution-verified`, runs under `## Implementation`): 106/106
[test-sets][testsets] + 7/7 [test-ops][testops] pass unchanged; the swap-mutation probe
(`write_method = "update" if operation == "create" else "create"`) failed exactly the 5
declared rows (both override tests, both happy paths, the snapshot test) while the
empty-mapping control passed: "pinned: the 5 failing row(s) are exactly the declared
`expect_failing`", restore byte-proved.
- **Negative control.** None owed: bypass is not the threat (envelope robustness, not security).
- **Coupling.** None.
- **Freshness.** Edited blob (copy) `2f61a2cc`; live pre-edit `d3a16114` (map + comment :288-298
and use :379 byte-identical to HEAD :297-307/:400; adjacent dirt is the concurrent truth
conversion, touch lines clean). Domain/test live blobs: [operations][ops] `612c458d`,
[msets][msets] `6f2fa2f9`, [testsets][testsets] `015be0fc`, [testops][testops] `5dba2df`;
dirt in all four avoids the proof lines (verified hunk by hunk: whitelist body is the same
membership contract, the pin assertions untouched, the registry untouched). Census
population: whole-repo rg for the map name (2 hits: def + use) + the `operation` flow in
[sets.py][sets].

## Defects

None.

## Judgment

Identity map on a whitelist-closed exact-`str` domain, one reader, no logic: P11 deletion.
Domain re-derived down to the hostile-subclass axis; oracles pass unchanged and the swap
probe pins the resolution 5 rows deep. Net -13/+4, all gates green. Reconsider only if a
second operation->method consumer appears, or a verb arrives whose DRF method differs from
its name (then a real translation earns a home again).

## Implementation (Worker-1)

Copy `slot-2` at `dry/nested-write-identity-map/consolidate` (synced 2026-10-11T22:10:45Z;
shared tree unmoved at every run). Edit: deleted [sets.py][sets] :288-298 (comment + dict),
replaced :379 with a 3-line rationale comment + `write_method = operation`; no other files.
Runs: ruff check --fix + format (clean); `pytest -n0 tests/rest_framework/test_sets.py` 106
passed (`dry-20261011T221135-964937`); `pytest -n0 tests/mutations/test_operations.py` 7
passed (`dry-20261011T221143-0a2e80`); prove (`dry-20261011T221241-71e12f`, pinned 5/5,
manifest `docs/dry/temp-tests/nested-write-identity-map/manifest.json`); basedpyright 0/0/0
(`dry-20261011T221312-53e40b`), floor 0/0/0 (`dry-20261011T221425-b361de`), truthful-reads 0
errors, trailing-commas 0 violations, citations 3347 OK. Item diff is the -13/+4 hunk pair,
nothing else.

## What shrinks

- The `_SERIALIZER_OPERATION_NESTED_WRITE_METHOD` dict (4 lines) and its 7-line comment go
away entirely: 11 lines deleted at the module level, replaced by nothing.
- The reader line becomes `write_method = operation` under a 3-line comment that keeps the
one unrecoverable token from the old comment (`raise_errors_on_nested_writes`) and states
the invariant a future reader needs: the value is whitelist-proven, and the DRF method
shares the operation's name, which is why no mapping exists. A reader who wonders "should
there be a table here" gets the answer at the use site instead of loading a module constant.
- What could never carry a change: the map's keys repeat the whitelist's membership (owned
by the operations registry + `require_non_delete_operation`) and its values repeat DRF's
method names (owned by DRF). Any change to either side moves the real owner; the map only
ever trailed as a third spelling. Deleting it removes the trailing obligation, not by
merging two definitions with logic, but by removing a definition with none.
- The raw-`KeyError` failure mode on an out-of-domain value leaves with the dict. It was
unreachable through the sole caller (and through every direct-call test), so its removal is
not behavior change; the failure that remains reachable-in-theory is the typed
`ConfigurationError` the module's contract already promises.
- Relation to the earlier R-ops rejection: that verdict kept the map file-local by refusing
to push a DRF axis into the vocabulary module. This change agrees with that refusal and
goes one step further - the axis is not pushed anywhere because there is no translation to
own. If a future verb ever breaks the name identity (verb `archive` handled by DRF method
`update`, say), that is the trigger: reintroduce a real operation->method table at that
time, owned by the serializer flavor, with its own oracle row per member.

## Independent verification (Worker-2)

Own trace, recorded before opening `## Findings`. Domain re-derived from the
registry: CREATE (form+, name create) and UPDATE (form+, name update) satisfy
the `supports_form_mutation and name != "form"` predicate; DELETE (form-) and
FORM (name == form) fail it, so `NON_DELETE_WRITE_OPERATIONS` is exactly
`{create, update}` (oracle spells the equality: `test_operations.py` 7 tests).
Producers of `operation` at the use: exactly one production caller,
`rest_framework/sets.py::SerializerMutation._validate_meta` (live :612) passing
`require_non_delete_operation`'s return; tests pass only `"create"`/`"update"`
literals; no other production caller (whole-tree grep); no test reads the map.
Reassignment audit: bound :612, passed :700, compared :714, snapshotted :726 -
no rebinding; inside the callee `operation` is read once (:379). Hostile-subclass
axis: the gate checks `truth.is_instance(str)` then runs `truth.text` (exact-str
copy via the `str` slot) for BOTH the membership test and the return, so a `str`
subclass's hostile `__hash__`/`__eq__`/`__str__` never runs and the use receives
an exact `str`. Third-value trace: any vocabulary third value (`delete`/`form`/
typo) is not a `ModelSerializer` attr (executed probe), so post-delete the
`static_attr`-is-`static_attr` comparison is `None is None` -> `ConfigurationError`;
loud either way, and unreachable through the whitelist regardless. Verdict from
my own trace: PROCEED with deletion - an identity map (keys == values) whose
keys re-spell the upstream-whitelisted domain and whose `KeyError` gate no
reachable input can strike; a principle-11 abstraction with no responsibility,
and deleting it removes the whitelist<->keys drift vector. Matrix (own
discharge): cross-flavor - no twin (`NON_DELETE_OPERATION_INPUT_KIND` is a real
create->CREATE translation, kept); sync/async - class-creation sync only, no
twin; derived - the message interpolates the same value, no second derivation;
round-trip - one-directional check; media - no spec/test/doc spells the map
(spec-039 prose states the override behavior, which is preserved); omission -
both members mapped, `delete` excluded upstream. Item diff re-derived:
slot-2 vs live is sets.py -13/+4 only (map+comment out, `write_method =
operation` + rationale in); slot-2 walker == live (sibling port, not this item);
slot-3 sets == live.

### Reconciliation + ruling (after reading Findings)

- No material difference: domain, sole caller, no-reassign, exact-`str`, census, spec sweep, challenges, and the P11 verdict all agree; the R-ops note is endorsed (deletion is not folding). Nuance recorded: exotic-attr third values (e.g. `save` with a `save` override) could pass silently post-change, but no wire input can produce them through the whitelist - unobservable per principle 8, not a defect.
- Proofs re-derived in slot-4 (runs `dry-20261011T222602-c25091`/`222611-b88851` pre, `222639-f5821e`/`222643-5a399c` post): 106/106 + 7/7 green both sides of my own re-applied byte-identical edit (`2f61a2cc`); swap pin re-run with my own manifest (`dry-20261011T222710-e6a706`): exactly the 5 declared rows fail, the control passes, restore SHA-256-proved.
- Freshness: all 6 blobs recomputed identical (`d3a16114`/`2f61a2cc`/`612c458d`/`6f2fa2f9`/`015be0fc`/`5dba2df`); touch lines byte-identical to HEAD (adjacent hunk context-only); all 5 pin rows + control byte-identical HEAD-vs-live; whitelist/message/pin dirt attribution confirmed hunk by hunk.
- Shape: missing `## Pending execution` is COMPLIANT - the contract says "Absent when none"; zero deferred proofs (all execution-verified) and zero witnesses, and an empty section would violate "No empty placeholders".
- Gates: ruff check + format --check pass on the edited file (`dry-20261011T222735-a753f3`/`222736-5ba9b3`); basedpyright/truthful-reads/trailing-commas/citations not re-run - no doubt (comment + `str`=`str` assignment; no imports/types/exports/tokens touched). Banned-substring hits are pre-existing prose outside the hunks (rule is tests-scoped; zero test files touched); link scaffold carries all 10 groups; `:NNN` cites are permitted in `docs/dry/dry-*.md`.
- Verdict: verified. No defects. Bar met as an honest principle-11 deletion (abstraction with no responsibility; drift vector removed; no machinery; behavior preserved on the reachable domain).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[msets]: ../../django_strawberry_framework/mutations/sets.py
[ops]: ../../django_strawberry_framework/mutations/operations.py
[sets]: ../../django_strawberry_framework/rest_framework/sets.py

<!-- tests/ -->
[testops]: ../../tests/mutations/test_operations.py
[testsets]: ../../tests/rest_framework/test_sets.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
