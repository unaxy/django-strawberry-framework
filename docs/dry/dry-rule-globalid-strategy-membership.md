# DRY review: `globalid-strategy-membership`

Status: verified
Run: 0.0.15 2026-10-12-22

## System trace

Rule: strategy-to-payload-shape mapping. `MODEL_LABEL_STRATEGIES` /
`TYPE_NAME_STRATEGIES` (types/relay.py:587-588) back 3 directional predicates,
2 direct set readers (`encode_typename:678`, `_accepted_globalid_type_names:959/961`),
1 derived union (`FRAMEWORK_GLOBALID_STRATEGIES`, filters/base.py:91);
`STRING_GLOBALID_STRATEGIES` (types/base.py:160) is the adjacent vocabulary.
Census over 121 package files: 5 predicate call sites (finalizer.py:399/423/458,
relay.py:969/971), zero elsewhere; no second shape literal; one
`{"callable", "custom"}` code literal (filters/base.py:100). Closure captures RAW
strategy; decode/filter/audits read RECORDED `str | None`; root + write flavors
delegate to `decode_global_id`. Drift CONFIRMED at 3 source sites + 5 spec
sentences; the `_emits`/`_accepts_model` split is KEPT, reader map corrected.

## Verification

### Matrix

1. Cross-flavor: mutations/rest/forms decode via `decode_model_global_id` into `decode_global_id`; no second membership.
2. Sync/async: no twin surface; every site is a pure sync set read.
3. Derived: FRAMEWORK-union vs STRING-literal is F3; 2-site `label_lower` is Django-owned, excluded.
4. Round-trip: encode vs Step-2 vs filter set vs audit halves agree via the single-owned sets.
5. Media: spec-031 D4/5/6/8/10/13 + DoD are projections (2 fixed, 3 homed D1-D3); row 902 homed D4.
6. Omission: all 9 enforcement readers enumerated; each guards its own domain; none missing.

### Challenges

C1 new string strategy + new shape: forces vocab + encoder branch + filter arm +
Step-1 routing + FRAMEWORK derivation (5 real-logic edits); composition removes 0.
C2 drop `type+model` from `TYPE_NAME_STRATEGIES`: 1 edit (the set); Step-2 + filter follow. Count 1.
C3 emit/accept set split: 1 definition edit + one-token consumer repoints (desired allegiance calls). Count 1.
C4 encode-only string strategy: joins STRING, never FRAMEWORK; proves the (c) split. Count 1 per contract.
Every plausible change moves exactly 1 membership definition; inline reads are consumers. Below bar.

## Findings

F1 encoder-vs-`_emits` (a): REJECT. Domain split: `encode_typename` decides over
RAW strategy (live callable or string; never `None`/`"custom"`), `_emits` over
RECORDED `str | None`. Same verdict, different values + fallback structure. C1-C3
count 1. Fix: owner comment (true readers + trigger) + `_emits` docstring. Proof:
inverse AST identity, execution-verified. Trigger: closure captures recorded value.
F2 filter-vs-`_accepts` (b): REJECT. Deliverable split: `_accepted_...` DERIVES a
name SET (payload strings, rendered in the mismatch message :1074); predicates
ENFORCE booleans. Shared tokens over one definition, count 1. Fix: owner comment
+ `_accepts_type` docstring. Oracles: `test_accepted_globalid_type_names_*`,
Decision-13 block, live `test_products_api.py:1701` + library mismatch pins. Proof:
inverse AST, execution-verified. Trigger: filter/decode acceptance diverge, or a
second name-set deriver appears.
F3 FRAMEWORK-vs-STRING (c): REJECT unification. Intension split: STRING is the
CONFIGURABLE vocabulary (validators, precedence, mint gate); FRAMEWORK is the
DECODABLE set (shape union). C4 proves a change joining one, never the other.
Fix: separation clause + trigger at FRAMEWORK comment; STRING readers corrected;
spec-031:57 fixed (:294 homed D1). Proof: inverse AST + citations gate (new token
resolves). Trigger: both contracts share one record (a single strategy table).
F4 `_emits` vs `_accepts_model` identical bodies: KEPT (brief-directed). True map
at the owner: audit reads emit + accept halves, Step-2 the accept half;
encoder/filter read the sets directly per F1/F2.

## Defects

D1 spec-031:294 (foreign-dirty): P5 tail "...the encoder, and the decode-shape
enforcement all read...". Apply the :57-shaped fix once the hunk lands (Worker-0).
D2 spec-031:70 (foreign-dirty): P4 tail "read via `_accepts...` and shared with...".
Apply the :317-shaped fix (Step-2 via predicates, audit via `_emits`/`_accepts_model`, filter direct).
D3 spec-031:566 (foreign-dirty): same P4 tail ("read through"). Same fix as D2.
D4 plan row 902 "opposite-halves readers" inherits the false encoder claim. Worker-0
plan-text fix ("audit-emit vs audit-accept+decode; encoder reads the set"); row shut.

## Pending execution

None. Sharded/pg inapplicable by construction (no DB/alias/dialect path).
No pytest (prose-only; inverse proof + gates discharge; Worker-2 judges cells).

## Judgment

Composition removes no change obligation on any prong (count 1 throughout). The
drift was real at 3 source sites and is corrected with durable triggers, plus 2
of 5 spec sentences (remainder homed). Zero executable change, all gates green.

## What shrinks

Rule: strategy-to-payload-shape membership reads (sets vs directional predicates
vs configurable vocabulary).
Change: zero-edit on executable code (rejections F1/F2/F3 with contract differences
+ firable triggers); prose correction at 4 touchable sites (3 source comment /
docstring regions + 2 spec sentences); 3 spec sentences + 1 plan parenthetical
homed as defects/notes (foreign-dirty lines and Worker-0-owned plan text).
Owner before/after: `MODEL_LABEL_STRATEGIES` / `TYPE_NAME_STRATEGIES` comment block
in `django_strawberry_framework/types/relay.py` (unchanged owner; reader map now
true); `FRAMEWORK_GLOBALID_STRATEGIES` comment (gains the vocabulary-vs-decodable
separation); `STRING_GLOBALID_STRATEGIES` comment (gains the true reader list).
Net lines (workspace copy vs live tree): types/relay.py +16/-9 (net +7),
filters/base.py +6/-1 (net +5), types/base.py +7/-4 (net +3),
spec-031-globalid_encoding-0_0_9.md 2 substitutions (net 0). Total +29/-14 prose,
0 executable lines added/removed/altered (proven by identical docstring-stripped
AST digests on all 3 `.py` files).
Machinery attestation: no new helper, driver, registry, mode flag, constant, or
predicate; one new citation token inside a comment (resolves via the citations
gate); no test added or removed (existing per-strategy oracles at package + live
tiers already pin every verdict the corrected prose describes).

## Implementation (Worker-1)

Edits live ONLY in slot-3 (`dry/globalid-strategy-membership/consolidate`); live
tree carries this artifact alone. 7 prose hunks: relay.py owner comment (true
readers + F1/F2 triggers), `_emits` + `_accepts_type` docstrings, FRAMEWORK
comment (F3 clause + trigger), STRING comment (true readers), spec-031:57 + :317.
Gates in-copy via `workspace.py run`, all exit 0: ruff check
`dry-20261012T064325-b83425`, format `dry-20261012T064331-d52977`, basedpyright
`dry-20261012T064338-99a8d2` 0/0/0, floor `dry-20261012T064348-5a1368` 0/0/0,
truthful-reads `dry-20261012T064359-d2cff3` tier-1 0, trailing-commas
`dry-20261012T064406-97b56d` 0 violations, citations `dry-20261012T064419-93a641`
(87 resolve). `check_public_types` skipped (no public symbol touched).
Inverse proof, execution-verified: before-vs-consolidate stripped digests match
per file (relay `27417adb`, filters `a91af559`, base `ddc26e3d`); files differ
from each other (non-vacuous control). Retirement in copy: P1/P2/P3 0 hits;
P4 only spec :70/:566, P5 only :294. Attribution: spans byte-identical to HEAD
(relay 567-625, filters 85-102, base 152-163, spec :57/:317); relay +93-106 is the
ledgered trigger comment, all other hunks foreign concurrent (163 added `truth.`
lines), none overlapping. Fingerprints (live pre-edit): relay `3b4447ae`,
filters `82c153fc`, base `7e65b2bd`, spec `aaa5ab53`; HEAD `c37a08a0`;
ITEM_BASELINE `7bfc588d`; 121 package files; spec-031 D4/5/6/8/10/13.
Ledger proposal on verified: 4 rows (3 package + spec-031), prose-only, symbols:
membership comment, 2 docstrings, 2 set comments.

## Independent verification (Worker-2)

Own trace (pre-Findings; sites from live-tree grep, not artifact):
Defs: `types/relay.py::MODEL_LABEL_STRATEGIES` / `::TYPE_NAME_STRATEGIES`
(shape memberships); `types/base.py::STRING_GLOBALID_STRATEGIES` (configurable
vocab); `filters/base.py::FRAMEWORK_GLOBALID_STRATEGIES` (derived union,
decodable); `filters/base.py::ENCODE_ONLY_GLOBALID_STRATEGIES`
(`{"callable","custom"}` message/audit set); 3 predicates in `types/relay.py`
(bool over recorded `str|None`). Consumers: `types/relay.py::encode_typename`
(raw `GlobalIDStrategy`, callable-first) reads MODEL set directly;
`filters/base.py::_accepted_globalid_type_names` (recorded `str|None` to
`set[str]|None` + mismatch names) reads both sets directly;
`types/relay.py::decode_global_id` Step-2 reads via accept predicates;
`types/finalizer.py` audit (399/423/458) reads via emit/accept predicates;
`filters/base.py::_decode_and_validate_global_id` reads FRAMEWORK + ENCODE_ONLY;
`types/finalizer.py::_audit_globalid_filter_strategies` reads ENCODE_ONLY;
`types/base.py::_validate_globalid_strategy` + `testing/relay.py::global_id_for`
read STRING. Oracles spell literals; projections are owner comments + spec-031.
OC1 add model-label-shaped string strategy: STRING + MODEL_LABEL move (2 defs,
2 contracts: vocab vs shape); encoder/filter/FRAMEWORK follow, 0 edits.
OC2 drop `type+model` from TYPE_NAME: 1 edit (the set); Step-2 + filter follow.
OC3 emit/accept split: 1 def edit (split sets) + one-token consumer repoints.
OC4 encode-only string strategy: joins STRING, never FRAMEWORK (split proof).
Owners I would choose: shapes + predicates stay in `types/relay.py`; vocab
stays in `types/base.py`; decodable union + encode-only set stay in
`filters/base.py`. Verdicts pre-Findings: (A) `encode_typename` inline vs
`_emits_model_label` REJECT (raw-vs-recorded domains, `callable` vs
`str|None`, slot decision vs bool); (B) `_accepted_*` inline vs accept
predicates REJECT (name-set derivation + message vs bool verdict, 0
obligation removed); (C) FRAMEWORK union vs STRING literal REJECT
(configurable vs decodable intension, OC4 trigger); (D) emit/accept identical
bodies KEEP split (directional names, split-sets trigger at owner).
Reconciliation (post-Findings; every difference explicit): F1/F2/F3/F4 AGREE
(raw-vs-recorded, set-vs-bool, configurable-vs-decodable, keep split); W1 C1
(new shape: 5 edits, removes 0) complements my OC1 (new member existing shape:
STRING+MODEL, 2 defs 2 contracts); C2/C3/C4 match OC2/OC3/OC4. Tagging: I
listed predicates under Defs; strictly they are by-name consumers of the set
defs (bodies `return x in SET`, follow with 0 edits) — verdict unaffected,
count 1 stands (sets are the defs). Owners match (unchanged). Census
re-derived: 121 files; 5 predicate CALLs (finalizer 399/423/458, relay
969/971), zero elsewhere; shape literals only at defs; `{"callable","custom"}`
code literal only filters/base:100; 9 shape readers (4 direct/derived + 5
via-predicate), each own domain, none missing; `label_lower` 2-site is
Django-owned, correctly excluded. Matrix 1-6 confirmed (flavors delegate to
`decode_global_id`; pure sync; F3 + Django exclusion; halves agree via single
sets; 2 spec fixed + 3 homed; 9 readers). Inverse-AST re-derived in-copy:
relay `27417adb`, filters `a91af559`, base `ddc26e3d`, before==consolidate per
file, all three distinct (non-vacuous). Retirement in consol: P1/P2/P3 0 hits;
P4 only :70/:566; P5 only :294 (:57 + :317 fixed). Attribution: touch spans
byte-identical to HEAD (relay HEAD 392-595 gap clean; filters HEAD 82-207
clean; base STRING HEAD 151+ clean; spec :57/:317 clean); HEAD-vs-BEFORE is
ledgered relay trigger (+96,8) + 163 added `truth.` lines (37/17/109), none
overlapping. D1-D3 foreign-dirty CONFIRMED (truth. hunks on :70/:294/:566
same lines); deferral correct, non-blocking (spec projections; source truth
fixed; verdict independent). D4 row 902 wording-only, Worker-0-owned, row
shut; non-blocking. Pending None + sharded/pg inapplicable CORRECT (prose-only,
no DB path; inverse proof execution-verified, no deferred proofs). Gates
re-run in slot-3 via `workspace.py run` (heavy, exit 0): citations
`dry-20261012T065413-34cabb` 87 resolve; basedpyright
`dry-20261012T065420-fb4518` 0/0/0; ruff check `dry-20261012T065428-d8eb8d`
pass; ruff format `dry-20261012T065434-7b7134` 3 formatted. Diff prose rules:
no process provenance (`audit` names code's own `_audit_*`); new
`types/base.py::STRING_GLOBALID_STRATEGIES` token resolves; zero tests correct
(0 executable bytes, existing oracles pin every verdict). Zero-edit search: no
`== "model"` etc. outside owner; mutations/sets literal is Meta-slot domain;
`_accepts_type` single-caller kept (directional contract + Step-2 symmetry,
P11 boundary name); single-table/exclusion-derivation rejected (new machinery).
Fingerprints live match W1 pre-edit (`3b4447ae`, `82c153fc`, `7e65b2bd`,
`aaa5ab53`); live untouched. Defects (Worker-2): none found. Verdict: verified.

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
