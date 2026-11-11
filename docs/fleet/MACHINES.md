# MACHINES.md: the maintainer's machine fleet

The machines an agent working on this repo may be asked to run on, and what to expect from each.
The maintainer adds a row here when a machine joins the fleet. How agents drive Muse Code on
any of them is in [MUSE.md][muse].

The goal is the same agent toolset on every machine (§2), so a flow can move to whichever machine
has the capacity, not whichever has the tool.

## 1. Machines

### MacBook Air (`rio-air`)

| | |
| --- | --- |
| Role | The maintainer's own laptop and the home of their supervising sessions. Agents running here launch and watch work, here or on another machine. |
| Hardware | Apple M3, 8 cores, 16 GB RAM, small free disk. |
| OS | macOS. |
| Availability | Whenever the maintainer has it open; it sleeps and travels. |
| Reach it as | `rio-air`, from the other fleet machines, only while the Air is awake (a closed lid or idle sleep takes it offline). |
| Expect | Connecting in is for reading, git and handing work back, not for running work. Light work only: editing, git, single targeted tests, supervising. Never benchmark or stress it; several agents share it with the maintainer's own apps. Do not park large copies or caches on its disk. Some Linux-standard tools are missing (`timeout(1)`, `tmux`). |

### Linux desktop (`rio-ubu`)

| | |
| --- | --- |
| Role | The remote agent box: long and heavy runs (test suites, builds, multi-agent flows) go here. |
| Hardware | Intel i7-8700, 6 cores / 12 threads, 45 GiB RAM, roomy NVMe; AMD GPU with no CUDA/ROCm. |
| OS | Ubuntu Desktop 26.04 LTS, GNOME. |
| Availability | Usually on. It dual-boots Windows, and while booted there this machine is offline: if it does not answer, it is not broken; tell the maintainer and stop. |
| Reach it as | `rio-ubu`, from the other fleet machines. |
| Expect | Read its house rules first: `~/MACHINE.md` on the machine. In short: check `pressure` before heavy work and run heavy work through `heavy` (at most 3 heavy jobs machine-wide); repos live in `~/projects/` and fast-forward from origin every few minutes while their tree is clean; no passwordless `sudo` (stop and hand root commands to the maintainer); rootless Docker; run long jobs in a `tmux` window, not under `nohup` or a bare `&`. The maintainer also sits at it: never close windows or kill GUI apps. |

### Mac mini (`rio-mini`)

| | |
| --- | --- |
| Role | A second Mac at the office: light and medium work, and the macOS half of anything that must run on both OSes. |
| Hardware | Apple M1, 8 cores (4 performance, 4 efficiency), 16 GB RAM, roomy free disk. |
| OS | macOS. |
| Availability | Not yet established; treat it as offline when it does not answer. |
| Reach it as | `rio-mini`, from the other fleet machines. |
| Expect | Set up like the others: the checkout under `~/projects/`, the same `uv`, Python, direnv, node and agent CLIs. Has a fan, so sustained runs do not throttle the way the MacBook Air does, but its 16 GB caps heavy runs below the Linux desktop's. |

### Linux mini PC (`rio-bee`)

| | |
| --- | --- |
| Role | A small always-on Linux box: light work (editing, git, single targeted tests, supervising) and a second Linux for anything that must run there. |
| Hardware | Intel Celeron J3455, 4 cores / 4 threads, 7 GiB RAM, 117 GB SSD; Intel HD Graphics 500. |
| OS | Ubuntu Desktop 26.04 LTS. |
| Availability | Not yet established; treat it as offline when it does not answer. |
| Reach it as | `rio-bee`, from the other three. |
| Expect | Light work only: four slow cores and 7 GiB cannot carry a full suite or a heavy flow (`load_balancing.py` weights it low). No passwordless `sudo` (stop and hand root commands to the maintainer). `/tmp` is a 3.6 GiB tmpfs that every reboot empties, so a `workspace.py` pool there is small and short-lived. It has none of `rio-ubu`'s house tools (`heavy`, `pressure`, `~/MACHINE.md`). Set up by [docs/fleet/scripts/fleet_setup.py][fleet-setup] ([SETUP.md][setup]). |

Connection details (transport, addresses, credentials) are kept in each machine's private
configuration, never in this repo. If a "reach it as" name does not answer from where you are,
the machine is not set up for you or is offline: report it and stop, do not hunt for another route.

## 2. Agent toolset

Target: every row present on every machine. A gap is a setup task for the maintainer, not
something an agent installs on its own.

| Tool | `rio-air` | `rio-ubu` | `rio-mini` | `rio-bee` |
| --- | --- | --- | --- | --- |
| Claude Code (CLI) | yes | yes | yes | yes |
| Claude Desktop | yes | yes | yes | no |
| Codex CLI | yes | yes (npm global under nvm) | yes | yes (npm global under nvm) |
| ChatGPT / Codex desktop | yes | yes | yes | no |
| Muse Code (`muse`) | yes | yes | yes | no |
| OpenCode (CLI) | yes | yes | no | no |
| OpenCode Desktop | yes | yes | yes | no |
| Cursor | yes | yes | no | no |
| Antigravity | yes | no | yes | no |
| T3 Code | yes | yes | yes | no |
| VS Code | yes | yes | yes | no |
| Warp | yes | yes | yes | no |
| `uv` (standalone, `~/.local/bin`) | yes | yes | yes | yes |
| CPython 3.10 to 3.14 via `uv python install`; 3.14 is `python3` (`--default`, which takes one version per call) | yes | yes | yes | yes |
| direnv, hooked into the login shell (zsh on the Macs, bash on the Linux machines) | yes | yes | yes | yes |
| node LTS via nvm | yes | yes | yes | yes |
| `pre-commit` as a `uv tool`, hook installed in the checkout | yes | yes | yes | yes |

Versions drift per machine as each one updates; check with the tool's `--version` on the
machine itself rather than trusting a number written here.

## 3. Rules that hold on every machine

- A repo's own `AGENTS.md` beats a machine's house rules, and both beat habit. This repo forbids
  creating branches and agent commits unless the maintainer says so, on every machine.
- Checkouts live under `~/projects/<repo>`; an agent's private copies live inside that checkout's
  git-ignored `.work/`, never as sibling folders under `~/projects/` (the desktop's autosync
  fast-forwards those). Machines do not share a working tree: work moves between them through
  the remote, or through a clone on the target machine whose `parent` remote is the source
  checkout over SSH (push disabled), its work handed back as a patch ([START.md][start] "Private
  working copies"). Only the maintainer commits.
- The full test suite runs in GitHub Actions (AGENTS.md); a machine runs targeted tests unless
  the maintainer asks for more.
- Before moving a long flow to another machine, check that machine's row in §2 has the tool the
  flow needs.

## 4. Adding a machine

[SETUP.md][setup] is the procedure, most of it one command ([docs/fleet/scripts/fleet_setup.py][fleet-setup]
`add <host>`). For the docs: copy a §1 block and fill in role, hardware (cores, RAM, GPU), OS, availability, the name it is
reached as, and what to expect. Add a column to §2. Keep it public-safe: no addresses, account
names, keys, or how the connection is made.

## 5. Picking a machine

New threads in shared projects start on the machine with the most free CPU and memory, weighted
by each machine's preference. [docs/fleet/scripts/load_balancing.py][load-balancing] answers it;
its module docstring holds the full rules. Run it from the checkout root.

```sh
uv run python docs/fleet/scripts/load_balancing.py           # ranked table, light work
uv run python docs/fleet/scripts/load_balancing.py --pick    # just the winning ssh host
uv run python docs/fleet/scripts/load_balancing.py --heavy   # heavy-work weights and floors
uv run python docs/fleet/scripts/load_balancing.py --json    # one document for agents
```

- The machine list is [machines.json][machines-json]: per machine its ssh host, OS
  (`linux`, `macos`, `windows`), checkout path, a preference weight per mode (`light`, `heavy`)
  and hard floors per mode, plus its `aliases`: other names the machine's stored records may
  carry, read only to resolve those records. The row's `name` is the machine's one name (its
  hostname, Tailscale name and ssh alias match it). A machine joining the fleet gets a row there
  as well as its §1 block. Weights and floors are finite numbers of at least 0; a list breaking
  that exits 2.
- Each machine is measured once per run, in parallel: the machine the script runs on directly,
  every other one in a single `ssh -o BatchMode=yes -o ConnectTimeout=5` call. The script runs
  on the machine `--here` names or whose `name` is this machine's (`$DSF_MACHINE_ID`, else the
  hostname); on an unlisted host every machine, its own included, is reached over ssh. Linux
  reads load, `MemAvailable`, PSI memory and the running `heavy` jobs; macOS reads `sysctl`;
  Windows reads `Get-CimInstance` through PowerShell; every OS reports free disk under the
  checkout.
- Score = weight x (free CPU share + free memory share) / 2. Any floor breach disqualifies:
  RAM available, free disk, PSI memory thrashing, all heavy slots taken, macOS memory pressure.
  An unreachable machine, or one whose probe reports an impossible value (NaN, negative, more
  memory available than installed), is listed with its reason, never an error.
- `--pick` exits 1 when no machine qualifies; then wait or ask the maintainer, never start the
  work on a disqualified machine.

## 6. Syncing copies across machines

[docs/fleet/scripts/fleet_sync.py][fleet-sync] keeps every online machine's private copies, pins,
evidence and main's commits in step (each copy edited on its home machine only; `handoff` moves it);
[START.md][start] "Syncing the fleet" has the rules.

<!-- LINK DEFINITIONS -->
<!-- Root -->
[start]: ../../START.md
<!-- docs/ -->
[fleet-setup]: scripts/fleet_setup.py
[fleet-sync]: scripts/fleet_sync.py
[load-balancing]: scripts/load_balancing.py
[machines-json]: machines.json
[muse]: MUSE.md
[setup]: SETUP.md
<!-- docs/SPECS/ -->
<!-- docs/builder/ -->
<!-- django_strawberry_framework/ -->
<!-- tests/ -->
<!-- examples/ -->
<!-- scripts/ -->
<!-- .venv/ -->
<!-- External -->
