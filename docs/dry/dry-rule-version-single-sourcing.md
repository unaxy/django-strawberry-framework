# DRY review: `version-single-sourcing`

Status: verified
Run: 0.0.15 2026-09-19-1

Family `version-single-sourcing`. Provisional owner
`django_strawberry_framework/__init__.py::__version__`. Seed sites
`django_strawberry_framework/__init__.py`, `pyproject.toml`; re-derived below,
not trusted. Prior records used only as rejected-candidate triggers:
[dry-file-__init__.md][dry-file-init] F2 (sole `__version__` literal,
hatchling derivation, `test_version` as oracle; structural gate deferred
to the family item) and the sibling family artifact
[dry-rule-logger-single-sourcing.md][dry-rule-logger] (precedent for the
gate SHAPE only: population-level cardinality pin with its negative
control executed in a disposable workspace — not a substitute for this
family's own proof).

## System trace

Rule: the release version literal and the packaging derivation that reads
it. One authoritative declaration; every other site derives it by
reference or pins it as an independent expectation.

Whole-repo mechanism sweep (every `__version__` binding, version literal,
`[tool.hatch.version]` config, `importlib.metadata` read, and install-pin
reference traced to its file; populations below):

- `__version__ =` binding: exactly 1 site,
  `django_strawberry_framework/__init__.py::__version__`
  (`__version__ = "0.0.15"`). The only other `__version__` code hits are
  READS of somebody else's release: `filters/sets.py` reads
  `django_filters.__version__` via `getattr` (upstream floor audit), and
  `tests/filters/test_sets.py` reads the same upstream attribute.
- Quoted `"0.0.N"` literals in `.py`: exactly 2 first-party sites — the
  root binding above, and `tests/base/test_init.py::test_version`
  (`assert __version__ == "0.0.15"`, the spelling oracle). All remaining
  dotted-version literals in tests (`tests/test_export_dry_review.py`,
  `tests/test_bug_hunt.py`) are scratch-fixture strings written to
  throwaway packages under tmp dirs, never the released package.
- `[tool.hatch.version]`: exactly 1 site, `pyproject.toml`
  (`path = "django_strawberry_framework/__init__.py"`), paired with
  `dynamic = ["version"]` under `[project]`. No static `version =` key
  exists anywhere in `pyproject.toml`.
- `importlib.metadata.version` / `pkg_resources` / `get_distribution`
  reads of the own package: 0 sites.
- Lock file: the `uv.lock` root entry
  (`name = "django-strawberry-framework"`) carries
  `source = { editable = "." }` and NO version field — not a
  declaration.
- Docs badge / install pin of the own release: none.
  `docs/README.md` installs unpinned
  (`pip install django-strawberry-framework`); no badge spells a
  version.

Roles:

- **Definition (1):**
  `django_strawberry_framework/__init__.py::__version__`.
- **Derived consumers (read, never restate):**
  hatchling build (`pyproject.toml` `dynamic` + `[tool.hatch.version]`
  `path`); `docs/dry/export_dry_review.py::VERSION_PATTERN` +
  `_package_version` (regex-reader for plan release naming);
  `scripts/bug_hunt.py::_INIT_VERSION_PATTERN` + `_init_version` /
  `_package_release` (regex-reader for hunt release naming).
- **Oracles (independent: they spell the contract without deriving it):**
  `tests/base/test_init.py::test_version` (spells `"0.0.15"`; fails on a
  bump until deliberately updated);
  `::test_package_defines_exactly_one_version_declaration` (new in this
  change; see Findings).
- **Projections:** the root in-file comment ("no second version
  declaration exists anywhere in the repository"), the `pyproject.toml`
  comments (same claim, both halves), the `AGENTS.md` + `START.md`
  single-source statements, `CHANGELOG.md` `## [0.0.15] - Unreleased`
  section header (maintainer-owned; never edited here), `docs/GLOSSARY.md`
  `Current package version` line + `shipped (0.0.N)` markers, spec
  filenames carrying `0_0_15`, KANBAN card `TODO-ALPHA-05x-0.0.15` names,
  in-code `(0.0.15 hardening)` historical comments. A bump moves none of
  these as definitions: they are release-process or historical record.

Connected sources read for judgment: `django_strawberry_framework/__init__.py`
in full, `pyproject.toml` in full, `tests/base/test_init.py` in full,
`docs/dry/export_dry_review.py` `VERSION_PATTERN` + `_package_version`
region, `scripts/bug_hunt.py` `_INIT_VERSION_PATTERN` + `_init_version` /
`_package_release` region, `django_strawberry_framework/optimizer/__init__.py`
(mutant host), `django_strawberry_framework/filters/sets.py`
`__version__`-read region, `scripts/prove_failability.py` manifest schema +
pytest-invocation region, `uv.lock` root-package entry region.
Upstream: none; the rule is package-internal.

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Release metadata lives above the
   flavor layer: no subpackage (`filters/`, `orders/`, `mutations/`,
   `forms/`, `rest_framework/`, `types/`, `optimizer/`) owns version
   state, and the sweep finds no `__version__` binding outside the
   root. One rule, no second surface.
2. **Sync/async twins.** The version read is import-time binding plus
   build-time derivation; no await boundary, no colored pair.
3. **Derived rather than repeated knowledge.** Hatchling derives via
   `path` + `dynamic` (reads, never restates); the two script readers
   regex-read the same literal; `uv.lock` carries no root version;
   nothing concatenates or recomputes the release. Sealed by the new
   gate's pyproject half (no static `version =` under `[project]`,
   `dynamic` still carries `"version"`, hatch `path` still names the
   root init).
4. **Inverse / round-trip pairs.** None; no encode/decode of the
   version.
5. **Contracts restated in another medium.** Media: code (1 definition),
   packaging consumer (`pyproject.toml`), tool readers (2 scripts),
   oracles (value pin + new cardinality gate), projections (listed
   above). A bump moves once at the owner; the value oracle moves
   deliberately as the release-cut expectation; the rest follow by
   reference. Counts taken at the definition only, every finding.
6. **Enforcement by omission.** Deliberate and contract-sourced:
   `uv.lock` omits the root version (editable source; verified at the
   entry); no GraphQL field exposes `__version__` (stated in the
   `test_init.py` module docstring); `__version__` IS in root `__all__`
   (unlike `logger`), pinned by the star-hygiene oracle — owned by
   family `package-root-public-surface`, not this one. No member lacks
   a guard its contract requires.

### Enumeration

Instrument: subtree `__version__` greps over package, tests, examples,
scripts, and `docs/dry`; full-repo quoted-literal greps
(`"0.0.N"` / `'0.0.N'` over `.py` + `.toml`); `hatch.version` /
`importlib.metadata` / badge / install-pin greps; plus a read-only AST
`Assign`/`AnnAssign`-target census over the whole checkout (551 `.py`
files, environments and scratch pruned). Every hit is assigned in the
trace above: 1 definition, 3 derived consumers (hatchling + 2 script
readers), 2 upstream-attribute reads (excluded by subject: they are
`django_filters`' release, not this package's), fixture-string literals
in two tool-test modules (excluded by population: scratch packages,
never the released one), 0 second bindings, 0 static pyproject keys,
0 metadata-API reads, 0 badges/pins. The only `__version__ =` binding
in first-party source is the root literal.

### Challenges

Counts are authoritative definitions only; consumers, oracles,
projections listed, never counted.

| # | Change posited | Definitions forced |
|---|---|---|
| C1 | Cut release `0.0.16` (bump the version) | **1** (the root literal). Hatchling derives at build; the two script readers read at runtime; the `test_version` oracle moves deliberately as the release-cut expectation; CHANGELOG/GLOSSARY/spec-name projections move as release process, never as declarations. |
| C2 | Add a second place that needs the version (docs badge? lock file? install pin?) | **0 existing.** `uv.lock` carries no root version, `docs/README.md` installs unpinned, no badge spells a release. A future badge or pin would be a NEW derived-read consumer, not a move of this rule. This count-0 split is what proves today's count is 1. |
| C3 | A second declaration appears (static `version =` under `[project]`, or a second `__version__ =` binding) | **0 exist today;** each bypass now fails exactly the new gate's owning half (entry 1: binding copy; entry 2: static key) while `test_version` passes on both by construction. |

## Findings

### F1 — version single-sourcing (single-owned; gate-only cardinality + consumer-shape addition)

- **Contract + variation.** The release literal lives in exactly one
  source location (`django_strawberry_framework/__init__.py::__version__`);
  hatchling derives the packaging metadata from it via
  `[tool.hatch.version]`; no second version declaration exists.
  Variation axis is the release cut itself (one literal per release).
- **Sites + roles.** As inventoried above: 1 definition (root binding);
  3 derived consumers (hatchling `dynamic` + `path`, two script
  regex-readers); oracles and projections as listed.
- **Challenges.** C1 -> 1 definition; C2 -> 0 existing (proof of
  current count 1, not duplication); C3 -> 0 existing, both bypasses
  gated.
- **Owner + lifetime (principle 7).** The package root stands:
  hatchling's documented convention, and the only site every
  legitimate consumer (build backend, plan/hunt tooling, tests) can
  read without reversing a dependency. No narrower owner is possible
  for a release literal. Principle 4: the only stored derivation is
  the module binding itself (literal evaluated once at import,
  published as the module attribute, never mutated, never
  invalidated; validity = process lifetime). No owner-held cache, no
  invalidation protocol owed. Anti-duplication mandates no new shared
  state, and none is added.
- **Migration.** Production: none (already single; zero production
  hunks). Tests: one structural gate added (below). No oracle
  rewritten (the standing `test_version` is untouched; the new test
  scans source, it does not import the owner it checks).
- **Distinct behavior (stays separate, where recorded).**
  `__version__` stays IN root `__all__` while `logger` stays out (star
  hygiene; owned by `package-root-public-surface`). The upstream
  `django_filters.__version__` reads stay a different rule with a
  different subject (floor audit, not release). A future second place
  needing the version (badge, pin) is a derived-read consumer, not a
  member of this family (C2 trigger below).
- **Rejection carried by this finding.** The "second definition"
  candidate is rejected: the only other `__version__` code sites read
  `django_filters`' release (concrete contract difference: different
  package, different reason to change — a django-filter floor move
  never moves this release); the fixture strings write scratch
  packages (different population: never installed, never released).
  Reconsideration trigger: a second `__version__ =` binding appearing
  in first-party source (the new gate fails on exactly that), a static
  `version =` key under `[project]` (same), or a second place
  genuinely needing the release value as its own declaration (that
  need becomes its own family row; a derived read does not).
  Durable home: the root in-file comment plus the `pyproject.toml`
  comments (both already state the no-second-declaration rule; no
  prose edit owed).
- **Behavioral proof (`execution-verified`).** Disposable workspace copy
  of the live tree per [DRY.md][dry] "Tests" (docs/ excluded):
  `WS=/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/version-single-sourcing`.
  From inside `WS`, `import django_strawberry_framework` resolves to
  `.../dry-ws/version-single-sourcing/django_strawberry_framework/__init__.py`
  and settings `DATABASES.default.NAME` resolves to
  `.../dry-ws/version-single-sourcing/examples/fakeshop/db.sqlite3`
  (copy's own tree and database; never the shared tree). Baseline
  `tests/base/test_init.py` in `WS`: 13 passed, 0 pre-existing
  failures. Second-binding mutant (behavior-preserving
  `__version__ = "0.0.15"` hand copy appended to the optimizer leaf):
  exactly `test_package_defines_exactly_one_version_declaration`
  fails while all 12 other rows pass — confirming `test_version` is
  blind to the duplication (it imports the root binding) and the new
  gate is not. Static-version mutant (`version = "0.0.15"` under
  `[project]`): exactly the new gate fails
  (`AssertionError: ['version = "0.0.15"']`) while the other 12 pass,
  measured with the copy's own venv interpreter so the packaging
  rebuild does not interpose (below). Both restores proved by byte
  comparison plus SHA-256. Rejects the wrong results "pyproject
  restates the version", "a second binding diverges at runtime", "the
  value test gates cardinality".
- **Structural gate.** Two oracles, each with its failing mutant:
  (1) value pin `test_version` (fails a bump; *passes* both
  duplication mutants by construction, which is why (2) exists);
  (2) NEW declaration pin
  `tests/base/test_init.py::test_package_defines_exactly_one_version_declaration`
  (fails both mutants; entries 1 and 2 above). The new gate's
  binding population is independently enumerated (`os.walk` from the
  repo root derived from the imported package's own `__file__`, 551
  files in the shared tree, environments/cycle-scratch/regenerable
  `docs/shadow/` pruned by dirname); per-region identity (the one hit
  must be `django_strawberry_framework/__init__.py`) + cardinality
  (exactly one); rejected parse failures (`unparseable` must be
  empty — the prune list exists because `docs/shadow/` stripped
  mirrors are unparseable by design); AST-based so comments,
  docstrings, fixture strings, attribute reads, and regex patterns
  neither satisfy nor break it. The pyproject half pins the consumer
  shape the same run: no static `version =` in `[project]`,
  `dynamic` still carries `"version"`, hatch `path` still names the
  root init. Negative controls run via
  [`scripts/prove_failability.py`][prove-script] in `WS` with
  `--scratch-root` outside both trees (manifest at
  `/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/version-manifest.json`;
  full report pasted in `## Implementation (Worker 1)`). Both entries
  report `**WEAKLY PINNED**` because each fails exactly 1 row. That
  label is a builder floor for boundaries owed many rows; here each
  boundary is one literal owed one row (a binding; a key), and each
  mutant fails exactly its owning row with 0 errors and a green
  baseline, which is the exact pin, not a weak one. Recorded as
  judgment, not as a second run.
- **Coupling.** None. Production untouched; the one test addition scans
  source text and reaches no database, alias, or dialect decision
  (sharded/PG cells inapplicable by construction). No dependency on any
  other family or on the ledgered walker/D1 work.
- **Freshness.** Working-tree blob ids (`git hash-object`): root
  `0ef72601ecac300ac87ff993af1b04a4f1bc335a`, pyproject
  `9be864937662d3932c1ba754c9b40877e4da2103`, optimizer leaf
  `d400569adf8ba801ff2293b6abddfd414fa18858`, filters/sets
  `4a40e51b288cad04cce3124697874c399d33f0fc`,
  `tests/base/test_init.py`
  `baaa570a51ca806d98e3b1047d3c97c1de3229d1` (post-edit; pre-edit
  `c65cf892ed2d2c01e2a1a0d98c5c8ade98d33fdf`),
  `tests/test_export_dry_review.py`
  `e246128252d60f4d0d4085c0a9fc13d2df43785a`, `tests/test_bug_hunt.py`
  `7f794762bcf2ba8d1311634cf94201adb2b1c6bf`,
  `tests/filters/test_sets.py`
  `a624a78df64bd1234d0f14da9b0e360801629d9b`,
  `docs/dry/export_dry_review.py`
  `83e969d9c8e5d65deb088d59bd0b60960d3225c0`, `scripts/bug_hunt.py`
  `14e39585a2f6b84eddb0a22ced4c0587ab3b0fe2`,
  `scripts/prove_failability.py`
  `10543b743e9dc89bb62bbe751d17a7752dbd7a50`,
  `docs/dry/dry-file-__init__.md`
  `fd43ebff0825aea5e6ca8bf1af151e750055927d`,
  `docs/dry/dry-rule-logger-single-sourcing.md`
  `6d094274cd68ce29dc2494f121bb460ded4cb257`,
  `docs/dry/dry-0_0_15.md`
  `8b99ae1e45312440c10c1589881e8627549ec74d`, `CHANGELOG.md`
  `d4e1035554f14ccd6563f67198c4ef59cd705aa1`, `docs/GLOSSARY.md`
  `bc51debc54cf3ed142b45fa9feda1b99bce60c79`. Excluded modules: every
  remaining first-party `.py` excluded on the strength of the AST
  census (population 551 enumerated; the one hit named in full) plus
  the quoted-literal and metadata-API greps. Searched populations:
  package/tests/examples/scripts/docs-dry `__version__` sweeps;
  full-repo quoted-literal, hatch, metadata-API, badge, and
  install-pin sweeps; `uv.lock` root entry. Any fingerprint change
  reopens the finding.

No sub-rule decomposed: the hatchling derivation, the two script
readers, and the lock-file omission are consumer postures of the one
rule, not shared rules, so Worker 0 owes no new index row from this
family.

## Defects

None. Every docstring/comment claim re-checked held: root "no second
version declaration" (one `__version__` binding repo-wide, now
mechanically enforced), pyproject "no second version literal to keep
in lockstep" (`dynamic` + hatch `path` read, static key absent and now
gated), `bug_hunt.py` "no second declaration to compare against and no
mismatch state to police" (its reader consumes the same literal),
AGENTS.md/START.md single-source statements, `uv.lock` editable root
entry. No guard missing on any member: every consumer binds through a
read that fails loudly if the owner goes away. Nothing routed;
consolidation depends on no repair.

### D-W2-1 — new test breaks the ASCII-only source gate (Worker 2; blocking, in-item)

`tests/base/test_init.py` lines 84-85 (added by this item) carry two U+2014
em-dashes in comments. `python3 scripts/check_trailing_commas.py --check
tests/base/test_init.py` exits 1 on them, and `.github/workflows/django.yml`
runs that script with `--check` in CI, so the item as written fails the
source-layout gate (ruff is blind here: RUF001-003 are project-ignored).
Reproducible now, pre-existing tree clean (`HEAD` and `ITEM_BASELINE` copies
are ASCII-clean). Fix (Worker 1): replace both with ASCII `--`. Re-pass owed:
the `--check` command above exits 0 plus the focused gate re-run.
Owner: this family item.

### D-W2-2 — GLOSSARY "Joint version cut" quintet names version sites that no longer exist (Worker 2; non-blocking, out-of-item)

`docs/GLOSSARY.md` #"Moved only by the cut" still lists `[project].version`
in `pyproject.toml` and "the package's own `version` entry in `uv.lock`" as
cut-moved version state. Neither exists: `pyproject.toml` carries
`dynamic = ["version"]` with no static key (verified), and the `uv.lock`
root entry is `editable = "."` with no version field (verified). Same-class
staleness at `KANBAN.md` #"is the one remaining independent copy". Prose
projection, not a definition: counts and the finding stand. Fix outside this
item; Worker 0 homes it on a NAMED docs card at closeout. Owner: docs
maintainer (the maintainer).

## Pending execution

None for this item. Every executed proof is recorded above with its
workspace command and outcome (`execution-verified`); the one authorized
shared-tree focused run
(`uv run pytest tests/base/test_init.py::test_package_defines_exactly_one_version_declaration --no-cov -n0 -q`)
passed (1 passed). Full-suite green and sharded/PG cells belong
to the final gate item, not this family: the production diff here is
empty and the new test reaches no database.

## Judgment

Single-owned rule, no duplication to consolidate: 1 authoritative
definition across the three change axes (C1: 1; C2: 0 existing;
C3: 0 existing, both bypasses gated). The upstream-attribute reads
and fixture strings are rejected as second definitions with their
contract differences and trigger. The standing gate covered the value
but not the declaration count (proven: both hand copies pass it), so
the item lands a gate-only addition: one population-level declaration
pin (binding census + consumer-shape halves) with both negative
controls executed. Zero production edits; one test added at the
mandated tier. Standard mirrored from the sibling logger item with
this family's own proof, as dispatched.

## Implementation (Worker 1)

Tracked changes (item-scoped diff vs `ITEM_BASELINE`
`80a806035cac37a4b348e51fe02e7ca639d28b9f`; `HEAD` is `bfaee91d`):

- `tests/base/test_init.py` (+83 vs baseline, no deletions: +33
  ledgered logger gate + my +50): `test_package_defines_exactly_one_version_declaration`
  plus its two stdlib imports (`os`, `re`; `ast` + `pathlib.Path`
  already present from the ledgered row). Pre-edit path attribution:
  `git diff HEAD -- <path>` holds exactly the ledgered logger hunk
  (`## Owned changes`: walker D1-adjacent logger row names this path
  and symbol); both known paths (`django_strawberry_framework/__init__.py`,
  `pyproject.toml`) confirmed clean vs `HEAD`. Production targets
  untouched.
- New untracked artifact: this file
  (`docs/dry/dry-rule-version-single-sourcing.md`).

After the edit, per the [worker-1.md][worker-1] gate: `uv run ruff check --fix tests/base/test_init.py`
then `uv run ruff format tests/base/test_init.py` until
`ruff format --check` and `ruff check` both pass on the touched path.
One escaping repair inside the pass (doubled backslashes in a raw
regex, caught on read before any run). No `CHANGELOG.md` touch. No
commit. Concurrent dirt (10 package files, 8 test files, bug-hunt and
plan artifacts, untracked sibling `dry-file-*.md`) never edited,
reverted, or tidied; attributed by content as external where named.

Workspace failability report (run in `WS` via
`uv run --directory "$WS" python scripts/prove_failability.py
<manifest> --scratch-root <outside-both-trees>`; package `__file__`
and DB `NAME` verified as the copy's own before any verdict):

```text
[1/2] django_strawberry_framework/optimizer/__init__.py::__version__
      (second-binding negative control)
    -> **WEAKLY PINNED - revision-needed** (1 row)
[2/2] pyproject.toml [project] version (static-version negative control)
    -> runner count INVALID (see hand proof below)
| 1 | second-binding negative control | mutation: __version__ hand copy
  into leaf | **1** | 0 | scope: tests/base/test_init.py -n0 |
  restore: filecmp True; sha256 proved |
  failing: test_package_defines_exactly_one_version_declaration
  (baseline 13 passed, 0 pre-existing; other 12 pass on the mutant,
  test_version among them) |
| 2 | static-version negative control | runner: exit 1, 0 FAILED lines,
  0 errors, summary tail "environment." — pytest never ran: `uv run`
  re-syncs the edited tree first and hatchling refuses static +
  dynamic together ("listed in field project.dynamic ... problem with
  the package or the build environment"). The runner cannot exhibit a
  mutant that breaks its own launcher, so this entry is re-proved by
  hand below instead of trusted as a zero. |
```

Hand proof for entry 2 (same `WS`, pristine copy at
`.../version-failability-scratch/pristine-pyproject.toml`): mutant
applied, measured with the copy's own venv interpreter
(`.venv/bin/python -m pytest tests/base/test_init.py -n0 -q --no-cov
-p no:cacheprovider`), bypassing the sync: exactly
`test_package_defines_exactly_one_version_declaration` fails
(`AssertionError: ['version = "0.0.15"']` at the static-key assert)
while the other 12 pass. Restore by copy-back: `cmp` clean, SHA-256
`da9d034a...` identical to the pre-mutation hash, `grep -c "^version"`
back to 0.

Reading of the `WEAKLY PINNED` label: see Findings (one literal owed
one row; exact pin, judged by hand as the runner requires). Side
observation, not a finding: the static-key bypass is loud at build
time (packaging error on sync) AND pinned by the gate whenever the
suite runs — defense in depth, recorded here so no cycle re-litigates
which layer owns it.

Scratch paths (removal is Worker 0's, after `verified`, by explicit
path): `WS` tree
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/version-single-sourcing`
(includes its own `.venv`, created by the authorized run),
manifest
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/version-manifest.json`,
scratch-root
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/version-failability-scratch`
(includes `pristine-pyproject.toml`).

Worker 0 rows: tick Family `version-single-sourcing` (this artifact);
no new responsibility-index row (no sub-rule decomposed); append to
`## Owned changes`: `tests/base/test_init.py` — Family
`version-single-sourcing` —
`test_package_defines_exactly_one_version_declaration`
(gate-only declaration pin; production untouched).

## Independent verification (Worker 2)

Own trace, re-derived by independent grep/reads (package, tests, examples,
scripts, `docs/dry`, `.github`, `pyproject.toml`, `uv.lock` root entry;
`## Findings` read only after this trace was recorded):

- **Definition (1):** `django_strawberry_framework/__init__.py::__version__`
  (`__version__ = "0.0.15"`). Package-wide `.py` grep finds no other
  first-party binding: only the `__all__` membership string and the
  `filters/sets.py` `getattr(django_filters, "__version__", "")`
  upstream-floor read.
- **Derived consumers (3):** hatchling (`dynamic = ["version"]` +
  `[tool.hatch.version]` `path`; no static `version =` key anywhere in
  `pyproject.toml`); `docs/dry/export_dry_review.py::VERSION_PATTERN` +
  `_package_version`; `scripts/bug_hunt.py::_INIT_VERSION_PATTERN` +
  `_init_version` / `_package_release` (confirmed on read: it returns the
  init literal with no second declaration to compare — single-source by
  construction). All read, none restate.
- **Oracles (2):** `tests/base/test_init.py::test_version` (value pin,
  imports the binding); new
  `::test_package_defines_exactly_one_version_declaration` (AST
  `Assign`/`AnnAssign` census over the repo + pyproject text asserts;
  expected paths spelled literally, never derived from the owner).
- **Projections (0 counted):** root + pyproject comments, `AGENTS.md`
  single-source rule, `START.md` line, `CHANGELOG.md` `## [0.0.15]`
  header, `GLOSSARY.md` version line + `shipped (...)` markers, spec
  filenames, KANBAN card names, historical in-code comments, dry `Run:`
  lines.
- **Exclusions with reason:** `django_filters.__version__` reads (another
  package's release, different reason to change); fixture `__version__`
  strings in `tests/test_export_dry_review.py` + `tests/test_bug_hunt.py`
  (scratch packages under tmp dirs, never installed); `.github` (no
  own-version read — only strawberry's `importlib.metadata` print);
  `docs/README.md` unpinned install, no badge; `uv.lock` root entry
  (`editable = "."`, no version field); zero own-package
  `importlib.metadata` / `pkg_resources` reads.
- **Counts:** C1 bump → 1; C2 second place → 0 existing; C3 second
  declaration → 0 existing, both bypasses gated (re-proved below).
- **Owner I would choose:** the package root — hatchling's documented
  convention and the only site every consumer (build backend, plan/hunt
  tooling, tests) can read without reversing a dependency. Lifetime as
  W1 states: import-time binding, process lifetime, never mutated.

Reconciliation vs W1 (agree on every substantive claim): exactly-one
declaration; the three derived consumers; both oracles and their roles;
all exclusions; C1/C2/C3 counts; root owner; gate-only outcome with zero
production edits. Differences: (a) dispatch-line "module-docstring tweak"
does not exist — baseline docstring is byte-identical; `+116/-0` is vs
`HEAD` (both gates), `+83/-0` vs `ITEM_BASELINE` (this item only); not a
defect. (b) W1's "every docstring/comment claim held" overreaches: the
GLOSSARY quintet line is stale (D-W2-2). (c) W1's "ruff clean" is true but
insufficient: the ASCII rule lives in `scripts/check_trailing_commas.py`,
which fails on the new test (D-W2-1, the verdict driver).

Freshness re-hashed (`git hash-object`): root `0ef72601…`, pyproject
`9be86493…`, optimizer leaf `d400569a…`, `filters/sets.py` `4a40e51b…`,
`test_init.py` post-edit `baaa570a…` (pre-edit `c65cf892…`),
`test_export_dry_review.py` `e2461282…`, `test_bug_hunt.py`
`7f794762…`, `filters/test_sets.py` `a624a78d…`, `export_dry_review.py`
`83e969d9…`, `bug_hunt.py` `14e39585…`, `prove_failability.py`
`10543b74…`, `dry-file-__init__.md` `fd43ebff…`, logger rule
`6d094274…`, plan `8b99ae1e…`, `CHANGELOG.md` `d4e10355…`, GLOSSARY
`bc51debc…` — all match W1's record. Nothing reopened. Production paths
(`__init__.py`, `pyproject.toml`) clean vs `ITEM_BASELINE`
`7a99a3f5…`; item diff is `tests/base/test_init.py` only. Ledger check:
plan `## Owned changes` carries exactly the one `test_init.py` logger
row — confirmed.

Negative controls, re-run in a FRESH workspace copy taken after W1's
edits (`.../dry-ws/version-w2-recheck`, `docs/` excluded per recipe;
copy's own package `__file__` and DB `NAME`
(`.../version-w2-recheck/examples/fakeshop/db.sqlite3`) recorded from
inside via `uv run --directory`): baseline 13 passed, 0 pre-existing
failures. Second-binding mutant (optimizer-leaf hand copy): exactly the
new gate fails, 12 pass with `test_version` blind — restore proved by
SHA-256 plus `cmp` vs the shared tree, 13 passed again. Static-pyproject
mutant: W1's runner-limitation account is accurate (hatchling refuses
static+dynamic at `uv run` re-sync, so `prove_failability.py` cannot
exhibit it — honest INVALID, not a smuggled zero); re-proved by hand
with the copy's own venv interpreter: exactly the new gate fails
(`AssertionError: ['version = "0.0.15"']`), 12 pass — with one caution
from my own run: a first attempt from the shared cwd passed 13/13
against the wrong tree, which is exactly the cwd trap [DRY.md][dry]
warns about; the valid run holds cwd inside the copy. Restore proved by
SHA-256 (`da9d034a…`, matching W1's hash — no shared-tree drift),
`grep -c "^version"` back to 0, `cmp` clean, 13 passed. Adjudication:
valid evidence, doubly proved, not a gap.

`## Pending execution` empty — judged correct: the new test is pure AST
walk + TOML text read, reaches no database, alias, or dialect decision,
so sharded/PG cells are inapplicable by construction; full-suite green
belongs to the final gate.

AGENTS.md prose: `tests/base/` still holds exactly `test_init.py` +
`test_conf.py` (no new file) — authorized growth. Tier: construction-time
declaration proof over the whole repo, unreachable from any GraphQL
query — `tests/` is the correct tier (principle-9 `check` shape), the
live-tier rule does not apply. Citations are `path::Symbol` throughout;
no process provenance. `uv run ruff format --check` (already formatted)
+ `uv run ruff check` (all passed) on `tests/base/test_init.py` — but
ruff does not own ASCII here, and the owning gate fails (D-W2-1).

Verdict: `revision-needed`. Single named candidate: replace the two
U+2014 em-dashes in the new test's comments
(`tests/base/test_init.py` lines 84-85) with ASCII `--`. Re-pass owed:
`python3 scripts/check_trailing_commas.py --check tests/base/test_init.py`
exits 0 + the focused gate re-run. No other change owed; every
substantive claim verified.

Worker 0 rows: (1) leave Family `version-single-sourcing` UNTICKED
(revision-needed) — no ledger row yet; (2) on re-pass, tick + append
ledger row `tests/base/test_init.py` — Family `version-single-sourcing`
— `test_package_defines_exactly_one_version_declaration` (gate-only
declaration pin; production untouched); (3) at closeout, home D-W2-2 on
a NAMED docs card; (4) after `verified`, remove by explicit path the
fresh scratch `.../dry-ws/version-w2-recheck` (with its `.venv` and
`pristine-pyproject.toml`) plus W1's paths from `## Implementation
(Worker 1)`. Never recursively clear `docs/dry/`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry]: DRY.md
[dry-file-init]: dry-file-__init__.md
[dry-rule-logger]: dry-rule-logger-single-sourcing.md
[worker-1]: worker-1.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->
[prove-script]: ../../scripts/prove_failability.py

<!-- .venv/ -->

<!-- External -->

## Iterations

### Re-pass 1 (Worker 1) — D-W2-1 ASCII fix

Worker 2 verified every substantive claim and returned `revision-needed`
on one blocking defect only (D-W2-1); D-W2-2 is out of this item and
untouched here (no docs edits). Fix: the two U+2014 em-dashes in the new
test's comments (`tests/base/test_init.py` lines 84-85) replaced with
ASCII `--`. Nothing else changed — same gate body, same population,
same asserts; the finding record above stands verbatim.

Proof (all four, in the shared tree after the fix):

- `python3 scripts/check_trailing_commas.py --check tests/base/test_init.py`
  exits 0 (no output; the owning ASCII gate W2 named).
- `uv run ruff format --check tests/base/test_init.py` → `1 file already
  formatted`.
- `uv run ruff check tests/base/test_init.py` → `All checks passed!`
  (COM812 conflict warning only, pre-existing repo-wide).
- `uv run pytest tests/base/test_init.py::test_package_defines_exactly_one_version_declaration --no-cov -n0 -q`
  → `1 passed`.

Freshness: `tests/base/test_init.py` re-hashed post-fix to
`239648ed635fa67baa10bf5bd428cd127098088b` (was `baaa570a…`; delta is
exactly the two comment characters). All other fingerprints unchanged;
no finding reopens. Item-scoped diff vs `ITEM_BASELINE`
`7a99a3f5934615dd9eda52497caf50a8c8e53f3f`: `tests/base/test_init.py`
(+83, this item's gate incl. the 2-char fix) plus
`docs/bug_hunt/bug_hunt-0_0_15.md` hunt-progress hunks attributed by
content as external concurrent work (optimizer context verified,
extension hunting — left untouched); both known paths
(`django_strawberry_framework/__init__.py`, `pyproject.toml`) clean;
this artifact still untracked. No commit.
