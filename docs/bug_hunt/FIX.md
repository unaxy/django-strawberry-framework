# Fixing tracker items

How one open item in the current tracker ([bug_hunt-0_0_15_2.md][tracker]) goes from "To do" to landed.
Entry: `Execute docs/bug_hunt/FIX-PROMPT.md` ([FIX-PROMPT.md][fix-prompt]), which loops this process over every open item.

Each phase finishes completely (every agent it dispatched has reported) before the next phase starts. Each item lands
(or is parked) before the next item starts.

## Roles

| Role | Agent type | Job |
|---|---|---|
| Coordinator | the session running the loop | picks the item, writes briefs, decides, lands, commits; never implements |
| Fact finders | `sonnet-high` | reproduce, read history, read upstream; run probes and tests; report facts |
| Researcher | `opus-high` | reads the fact reports, looks upstream for a better fix, prototypes it, lists decisions |
| Implementer | `opus-medium` | builds the change from the brief in a private clone |
| Verifier | `opus-high`, or `sonnet-xhigh` for an easy item (phase 7) | attacks the change, expectation first; LAND / FIX / BLOCK |

## The phases (per item)

1. **Pick.** The first unchecked item in this order: "To do: found along the way", then "To do: holes found
   re-checking the fixes". Skip an item carrying a **SKIP** note, and skip "Waiting on you" and everything below it.
   Check `git status` (other sessions work in this tree concurrently) and note `HEAD`. Then gate the item on the
   AGENTS defect rule and GOAL "Trust boundary" before any agent runs: it must name the contract row it breaks, a
   feasible project shape under supported public API, and the wire or configuration input that reaches it. Feasible: a
   `StrEnum` or `TextChoices` member, a lazy translation string, `SimpleLazyObject`, a project `QuerySet` subclass.
   Not feasible unless a real library or Django feature produces it: a `str` subclass whose `__eq__` or `__hash__`
   lies or raises, a lying `__class__`, a container whose `__iter__` raises. An item that fails the gate goes
   straight to the phase 4 "not a defect" outcome.
2. **Fact finding.** Write a shared rules file (template below), then dispatch `sonnet-high` agents in parallel,
   usually three: **repro** (does it happen on main, how widely: a probe grid over every shape it can reach),
   **history** (which commit, spec, doc or test claims what; is a test pinning the current behaviour), **upstream**
   (what Django, strawberry-django, graphene-django, django-graphene-filters, DRF / django-filter do). Add a repro agent
   per sub-claim when one item bundles several. Wait for all of them. A repro grid holds only shapes that pass the
   phase 1 gate; an infeasible shape is never a row to fix.
3. **Research.** Hand every report to one `opus-high` agent: find the more elegant or more upstream-aligned fix
   nobody thought of, prototype it in its own clone, measure it against the repro grid, and list numbered
   decisions (D1, D2, ...) each with a recommendation. Its census of affected sites passes the same gate.
4. **Rules check.** The coordinator rereads [AGENTS.md][agents], [START.md][start] and [GOAL.md][goal] and answers
   every open decision the rules settle (the AGENTS defect rule / GOAL "Trust boundary" for "is it a defect", the
   north star and success criterion 7 for "which behaviour", the AGENTS root-cause rule for "same change or later",
   START for upstream audits, doc homes and test placement, [docs/TREE.md][tree] and START's check-public-types hook
   for exported surface).
   - Not a defect under the AGENTS defect rule: tick it in the tracker with the verdict and the evidence, no code. If
     it hides a real contract question, file that under "Waiting on you". When a docstring or spec promises to contain
     an infeasible shape, the fix is retracting that sentence, never hardening code. Next item.
   - A decision only the maintainer can make (the rules do not settle it and the choice changes a public contract): move the
     item under "Waiting on you" with the question and the evidence. Next item.
5. **Plan.** Write the plan to the scratchpad (`<id>-plan.md`) and print it in chat: the defect, the decisions with
   their final answers and the rule behind each, what is out of scope (filed as new tracker items), the docs that
   change.
6. **Implement.** Make a fresh clone at `HEAD` and write the implementer brief (template below), starting from the
   researcher's patch. Dispatch one `opus-medium` agent with test runs authorized. A STOP from the implementer (a
   decision proves wrong against the code) comes back to the coordinator, who decides from the rules and the
   evidence and sends the ruling to the same agent (`SendMessage`), never a new one.
7. **Verify.** Dispatch one `opus-high` verifier with its own brief (template below). An easy item may take a
   `sonnet-xhigh` verifier instead: every decision was settled by the rules (none parked or ruled on after a STOP),
   the change touches no public signature, export or settings key and moves no published wire shape, its production
   diff stays inside one module, and the repro grid is a handful of rows. When in doubt, it is not easy. Each round of
   one item keeps the verifier type it started with. On FIX, rule on each finding
   and send the list to the same implementer, then send the delta back to the same verifier. Repeat until LAND.
   A change that narrows what worked at the parent commit for a feasible shape is a FIX finding, never a LAND.
   A docs-only last fix may be checked by the coordinator instead of a new verifier round.
8. **Land.** Apply the clone's `git diff HEAD --binary` to the shared checkout; it must apply cleanly and every
   path it touches must have been clean. Edit the tracker in the same working tree: move the item to the end of
   "Done", ticked, with an outcome stating the new behaviour, the symbols it changed and the tests that pin it;
   update the Progress counts; add out-of-scope questions under "Waiting on you" (an out-of-scope finding becomes a
   new item only if it passes the phase 1 gate; otherwise it is a robustness row or a new card); new items and
   questions take the next number unused in both the tracker and [CHANGELOGTODO.md][changelogtodo]. When consumers
   can see the change, add a "CHANGELOG entry for item N" item under CHANGELOGTODO.md's "From bug_hunt-0_0_15_2" and
   update its Progress line. Then make ONE commit holding the fix and the tracker edits together (conventional
   subject, a body that states the new behaviour); never a separate tracker commit after the fix. When another
   session has the tree dirty, commit from a private index (START "Concurrent sessions") so only the item's bytes
   ride. The tick names no hash, because a commit cannot name itself: the commit that ticks an item
   is its fix (`git log -S '- [x] N.' -- docs/bug_hunt/` finds it). No push, no branches, no CHANGELOG edit.
9. **Close.** Ask the implementer for `<id>-impl-feedback.md` (helpful / misleading / missing about the brief and the
   standing docs). Delete the item's clones, grids and patches; keep the reports, briefs and feedback. Print three
   lines: what landed, what got filed, what is next.

## Standing rules for every agent

- Read AGENTS.md, START.md and GOAL.md first.
- Work only in a private clone under the coordinator's scratchpad (`S/<id>-<role>`, made with
  `git clone -q --no-local <repo> S/<id>-<role>` then `uv sync -q`; assert `django_strawberry_framework.__file__`
  lies inside it). The shared checkout is read-only to every agent; only the coordinator writes it, at landing.
- Never touch `~/.t3/` (read-only), any `hunt-ws/`, or `~/dst-handoff/`. Never mention feedback.md / feedback2.md.
- Pytest only `uv run pytest -q -p no:randomly --no-cov -n 2 <node ids or a narrow -k>`, one run at a time, in the
  foreground (never `run_in_background`), never the full suite and never a whole big live module such as
  `examples/fakeshop/test_query/test_library_api.py`; anything costlier is listed as unverified, since the full suite
  and coverage run in GitHub Actions after the commit. Targeted runs and basedpyright / `check_public_types` start
  without waiting for an idle machine.

- Downloads only PyPI wheels into a fresh empty dir; read them, never run them; Python reading them runs with `-I`.
- No commits, branches or stash in any clone. Delete only files you created.
- Reports are text in the final message: numbered FACTS with `path::Symbol` or command evidence and counts, then
  OPINIONS. The coordinator saves each report to `S/<id>-report-<role>.md`.

## Brief contents

- **Fact-finding rules file:** the item text verbatim, where its evidence may live (the t3 worktree, read-only),
  the doc and code paths to start from, why it matters under the AGENTS defect rule, "fact finding only, do not fix",
  the standing rules, the report format.
- **Implementer brief:** the clone path; the defects as facts with `path::Symbol`; the starting patch and what it
  is (unreviewed); the decisions as FINAL with their reasons; the STOP rule ("a decision proves wrong against the
  code, a pin moves, or a result that was correct at HEAD changes: stop that part and report with evidence");
  tests (live first, parametrized, exact query counts, package rows only for lines no live query reaches, real
  consumer shapes over monkeypatches); docs in the same change (README, GLOSSARY through the DB, specs, docstrings,
  test READMEs), no CHANGELOG; verification steps (ruff, trailing commas, citations, generators, pre-commit,
  each targeted test file alone, coverage of changed modules at 100%, the repro grid, `scripts/prove_failability.py`
  per fix, basedpyright main + floor, `check_public_types`, the Python 3.10 floor run last); the report format.
- **Verifier brief:** the clone is read-only (mutate a copy); write expectations from the implementer brief BEFORE
  reading the diff or the report; check every decision, try shapes the tests miss, rerun the grid, run the parent
  commit and the change side by side on the feasible shapes next to the change (`SimpleLazyObject`, `StrEnum`,
  project subclasses of `list` / `dict`), reproduce two mutations, judge every moved expectation, docs vs code,
  simplicity; verdict LAND / FIX / BLOCK with severity-ranked findings and minimal fixes.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[changelogtodo]: ../../CHANGELOGTODO.md
[goal]: ../../GOAL.md
[start]: ../../START.md

<!-- docs/ -->
[fix-prompt]: FIX-PROMPT.md
[tracker]: bug_hunt-0_0_15_2.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
