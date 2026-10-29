# MACHINES.md: the maintainer's machine fleet

The machines an agent working on this repo may be asked to run on, and what to expect from each.
The maintainer adds a row here when a machine joins the fleet. How agents drive Muse Code on
any of them is in [MUSE.md][muse].

The goal is the same agent toolset on every machine (§2), so a flow can move to whichever machine
has the capacity, not whichever has the tool.

## 1. Machines

### Mac (MacBook Air)

| | |
| --- | --- |
| Role | The maintainer's own laptop and the home of their supervising sessions. Agents running here launch and watch work, here or on another machine. |
| Hardware | Apple M3, 8 cores, 16 GB RAM, small free disk. |
| OS | macOS. |
| Availability | Whenever the maintainer has it open; it sleeps and travels. |
| Reach it as | `rio-mac`, from the Linux desktop, only while the Mac is awake (a closed lid or idle sleep takes it offline). |
| Expect | Connecting in is for reading, git and handing work back, not for running work. Light work only: editing, git, single targeted tests, supervising. Never benchmark or stress it; several agents share it with the maintainer's own apps. Do not park large copies or caches on its disk. Some Linux-standard tools are missing (`timeout(1)`, `tmux`). |

### Linux desktop

| | |
| --- | --- |
| Role | The remote agent box: long and heavy runs (test suites, builds, multi-agent flows) go here. |
| Hardware | Intel i7-8700, 6 cores / 12 threads, 45 GiB RAM, roomy NVMe; AMD GPU with no CUDA/ROCm. |
| OS | Ubuntu Desktop 26.04 LTS, GNOME. |
| Availability | Usually on. It dual-boots Windows, and while booted there this machine is offline: if it does not answer, it is not broken; tell the maintainer and stop. |
| Reach it as | `rio-desktop`, from the Mac. |
| Expect | Read its house rules first: `~/MACHINE.md` on the machine. In short: check `pressure` before heavy work and run heavy work through `heavy` (at most 3 heavy jobs machine-wide); repos live in `~/projects/` and fast-forward from origin every few minutes while their tree is clean; no passwordless `sudo` (stop and hand root commands to the maintainer); rootless Docker; run long jobs in a `tmux` window, not under `nohup` or a bare `&`. The maintainer also sits at it: never close windows or kill GUI apps. |

Connection details (transport, addresses, credentials) are kept in each machine's private
configuration, never in this repo. If a "reach it as" name does not answer from where you are,
the machine is not set up for you or is offline: report it and stop, do not hunt for another route.

## 2. Agent toolset

Target: every row present on every machine. A gap is a setup task for the maintainer, not
something an agent installs on its own.

| Tool | Mac | Linux desktop |
| --- | --- | --- |
| Claude Code (CLI) | yes | yes |
| Claude Desktop | yes | yes |
| Codex CLI | bundled in the ChatGPT app, not on `PATH` | yes |
| ChatGPT / Codex desktop | yes | yes |
| Muse Code (`muse`) | yes | yes |
| OpenCode (CLI) | yes | yes |
| OpenCode Desktop | yes | yes |
| Cursor | yes | yes |
| Antigravity | yes | no |
| T3 Code | yes | yes |
| VS Code | yes | yes |
| Warp | yes | yes |

Versions drift per machine as each one updates; check with the tool's `--version` on the
machine itself rather than trusting a number written here.

## 3. Rules that hold on every machine

- A repo's own `AGENTS.md` beats a machine's house rules, and both beat habit. This repo forbids
  creating branches and agent commits unless the maintainer says so, on every machine.
- Checkouts live under `~/projects/<repo>`. Machines do not share a working tree: work done on
  one reaches another only through the remote, and only the maintainer commits.
- The full test suite runs in GitHub Actions (AGENTS.md); a machine runs targeted tests unless
  the maintainer asks for more.
- Before moving a long flow to another machine, check that machine's row in §2 has the tool the
  flow needs.

## 4. Adding a machine

Copy a §1 block and fill in role, hardware (cores, RAM, GPU), OS, availability, the name it is
reached as, and what to expect. Add a column to §2. Keep it public-safe: no addresses, account
names, keys, or how the connection is made.

<!-- LINK DEFINITIONS -->
<!-- Root -->
<!-- docs/ -->
[muse]: MUSE.md
<!-- docs/SPECS/ -->
<!-- docs/builder/ -->
<!-- django_strawberry_framework/ -->
<!-- tests/ -->
<!-- examples/ -->
<!-- scripts/ -->
<!-- .venv/ -->
<!-- External -->
