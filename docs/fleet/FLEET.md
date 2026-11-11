# FLEET.md: the workspace North Star

## North Star

A scalable workspace where tens of agents, from any provider, on any fleet machine (rio-air, rio-ubu, rio-mini), with no prior context, work at the same time, each only through a synced private copy that lands cleanly, so the shared checkout changes only by `land` plus the maintainer's commit, and every machine sees every copy.

## Checks

- Zero direct edits or tests in the shared checkout, proven by re-audit.
- Every copy visible on every machine within minutes, with no manual sync.
- The right path needs no hand steps: no hand database carves, no `--discard` habit, no manual `-r2`.
- A new model follows it from the first line of AGENTS.md plus this file.
- Enforcement is provider-neutral.
- Tens of concurrent agents run without queueing or resource exhaustion.

## References

- rule `AGENTS.md` (first line) copies `START.md` "Private working copies" sync `START.md` "Syncing the fleet" machines `docs/fleet/MACHINES.md` `docs/fleet/machines.json` muse `docs/fleet/MUSE.md`
- work `scripts/work.py` sync `scripts/fleet_sync.py` registry `scripts/fleet.py` picker `scripts/load_balancing.py` locks `scripts/_locks.py` flows `scripts/workspace.py`
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
