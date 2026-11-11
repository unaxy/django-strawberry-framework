# FLEET.md: the workspace North Star

## North Star

A scalable workspace where tens of agents, from any provider, on any fleet machine (rio-air, rio-ubu, rio-mini, rio-bee), with no prior context, work at the same time, each only through a synced private copy that lands cleanly, so the shared checkout changes only by `land` plus the maintainer's commit, and every machine sees every copy.

## Checks

Each check is a target with its measure; the status is what the last audit showed (Sol final review, 2026-11-11).

- **Shared checkout untouched.** Measure: every agent transcript since the last commit shows no write or pytest run whose path or cwd is a shared checkout outside `.work/`, and its `git status` holds only landed paths. Status: holds for that review; unmeasured fleet-wide (no transcript audit yet).
- **Every copy everywhere.** Measure: a `work.py save` on any machine `load_balancing.py` qualifies shows on every other qualified machine within 5 minutes, with no command run. Status: fails; a save stayed absent from the other machines after 5 minutes with no command run. `fleet_sync.py fetch-pins` brings one copy's saves in 5 to 23 seconds, by hand.
- **No hand steps.** Measure: from `work.py new` to `land`, an agent runs only `work.py` and `fleet_sync.py`: no hand database carve, no `--discard` habit, no manual `-r2`, no git plumbing. Status: fails; a database change still needs a hand carve until the row-merge `land` ships. Restoring a save and fetching its pins no longer need hand steps.
- **No prior context.** Measure: a model given only the first line of AGENTS.md and this file reaches a first passing `work.py run` on a remote machine without asking. Status: unmeasured since 2026-11-10, when it failed (it needed a brief, START.md and script docstrings).
- **Provider-neutral.** Measure: Claude, Codex and a plain shell each meet the same refusal for an edit or a pytest run in a shared checkout. Status: fails for edits (the hook binds Claude only); the pytest guard holds for all three.
- **Tens at once.** Measure: 20 agents across the fleet, each looping edit and targeted test, see a 95th-percentile queue wait under 2 minutes, with no machine past its `load_balancing.py` limits. Status: unmeasured; pytest queues by design, one run per checkout.

## References

- rule `AGENTS.md` (first line) copies `START.md` "Private working copies" sync `START.md` "Syncing the fleet" machines `docs/fleet/MACHINES.md` `docs/fleet/machines.json` setup `docs/fleet/SETUP.md` muse `docs/fleet/MUSE.md`
- work `scripts/work.py` sync `scripts/fleet_sync.py` stop `scripts/fleet_stop.py` setup `scripts/fleet_setup.py` registry `scripts/fleet.py` picker `scripts/load_balancing.py` locks `scripts/_locks.py` flows `scripts/workspace.py`
- guard `scripts/shared_checkout_guard.py` edit hook `.claude/settings.json` pytest guard `conftest.py`

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
