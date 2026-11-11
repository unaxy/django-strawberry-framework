# SETUP.md: adding a machine to the fleet

The procedure for a new machine, from a bare Ubuntu install to a fleet member that
[docs/fleet/scripts/fleet_sync.py][fleet-sync], [docs/fleet/scripts/fleet_stop.py][fleet-stop] and
[docs/fleet/scripts/load_balancing.py][load-balancing] reach. [docs/fleet/scripts/fleet_setup.py][fleet-setup] does
every step it can; its module docstring is the full rule. What it cannot do (sudo's password,
logins, the timer) is the maintainer's, marked **by hand** below. The machines themselves are
in [MACHINES.md][machines]; the North Star in [FLEET.md][fleet].

`<host>` is the new machine's one name: its hostname, its Tailscale name, its ssh alias and its
[machines.json][machines-json] row's `name` are all this one word (`docs/fleet/scripts/fleet.py`
"Identity"). Run every fleet-side command from `~/projects/django-strawberry-framework` on a
machine already in the fleet.

## 1. Before the script (by hand)

On the new machine, at its own keyboard:

```sh
sudo hostnamectl set-hostname <host>
sudo apt install -y openssh-server
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

Ubuntu Desktop ships no ssh server. Tailscale's install script adds Tailscale's apt
repository. Give the machine the same `<host>` name in the Tailscale admin console if it
differs.

On the fleet machine you will run the script from, give it an ssh alias and its key. The
accounts differ per machine and the registry records none, so each machine's own
`~/.ssh/config` names them:

```sh
printf 'Host <host>\n  User <account on the new machine>\n' >> ~/.ssh/config
ssh-copy-id <host>              # the new machine's password, once
ssh -o BatchMode=yes <host> true  # must exit 0
```

## 2. Install everything: `fleet_setup.py add`

```sh
python3 docs/fleet/scripts/fleet_setup.py add <host> --check   # read-only: what <host> lacks
python3 docs/fleet/scripts/fleet_setup.py add <host>           # install it; sudo asks once
```

`add` checks that `<host>` answers batch-mode ssh and is Ubuntu, copies the script to
`~/.cache/dsf-fleet-setup/` there, and runs its `box install` over `ssh -t`. Every step checks
first and runs only when its check fails, so a rerun after a failure resumes and a finished
machine reruns as a no-op. In order:

| Step | Kind | What |
| --- | --- | --- |
| `packages` | sudo | `git rsync curl direnv tmux ripgrep` from apt (a fresh Ubuntu Desktop lacks git) |
| `linger` | sudo | `loginctl enable-linger`: the save-sync timer is a systemd user timer, which stops at logout without it |
| `uv` | user | uv's installer into `~/.local/bin` |
| `pythons` | user | CPython 3.10 to 3.13, then 3.14 with `--default` (one version per `--default` call) |
| `direnv-hook` | user | `eval "$(direnv hook bash)"` in `~/.bashrc` |
| `node` | user | nvm (pinned release), node LTS as its default |
| `codex` | user | `npm install -g @openai/codex` under nvm |
| `claude` | user | Claude Code's native installer into `~/.local/bin` |
| `pre-commit` | user | `uv tool install pre-commit` (a stable interpreter for the git hook, START.md "Toolchain") |
| `ssh-key` | keys | `~/.ssh/id_ed25519` with no passphrase (fleet ssh is batch mode) |
| `checkout` | user | `git clone` of the public https URL to `~/projects/django-strawberry-framework` (no GitHub key needed; pushes stay the maintainer's) |
| `python-version` | user | `.python-version` (git-ignored, so a clone lacks it), copied from the machine running `add` |
| `venv` | user | `uv sync --frozen` |
| `hook` | user | `pre-commit install` |
| `direnv-allow` | user | `direnv allow` on the checkout |
| `logins` | by hand | reported only, below |
| `timer` | by hand | reported only, below |

`--skip sudo,keys` runs only what needs no password and writes no key (how an agent tests
the script); `box check` / `box install --only <step>,...` on the machine itself run part of
the list.

## 3. ssh between every pair: `fleet_setup.py mesh`

`fleet_sync.py` and `fleet_stop.py` run plain batch-mode ssh in both directions, so every
ordered pair of machines must reach the other by name.

```sh
python3 docs/fleet/scripts/fleet_setup.py mesh --check --add <host>   # the matrix, read-only
python3 docs/fleet/scripts/fleet_setup.py mesh --add <host>           # fix every missing pair (by hand: it writes keys and ssh config)
```

For each missing pair it creates the source's key if absent, adds a `Host` block with the
target's account to the source's `~/.ssh/config`, appends the source's public key to the
target's `authorized_keys`, and accepts the target's host key on first use. A machine that
is offline is skipped; rerun `mesh` once it is back. `--add` is needed only until the row
below is in `machines.json`.

## 4. Register the machine

```sh
python3 docs/fleet/scripts/fleet_setup.py row <host>
```

prints a `machines.json` row from the machine's cores and memory (weights relative to a
6-core machine with 16 GiB for light work and 32 GiB for heavy work, floors lowered under
16 GiB). Paste it into [machines.json][machines-json], tune the weights if the machine's role
calls for it, and add its block to [MACHINES.md][machines] section 1 and its column to
section 2 (no addresses or account names). The new machine's own checkout has the row only
once main carries it there (a push and its pull, or a fleet sync of main).

## 5. By hand on the new machine

```sh
claude          # log in once, then /exit
codex login
```

`box check` reports each as `missing hand logins` until its credential file exists (only its
existence is checked; the file is never read).

The save-sync timer comes last, once sync testing on the machine has passed:

```sh
cd ~/projects/django-strawberry-framework && uv run python docs/fleet/scripts/fleet_sync.py schedule --install
```

## 5a. Personalize (optional): `setup/ubuntu/personal.py`

The core above makes a fleet member. [personal.py][personal] adds the layer `rio-ubu` carries,
CLI only (no GUI application, no desktop setting):

```sh
python3 docs/fleet/scripts/setup/ubuntu/personal.py apply <host> --check   # what <host> lacks
python3 docs/fleet/scripts/setup/ubuntu/personal.py apply <host>           # install it; sudo asks once
```

It copies its folder to `~/.cache/dsf-fleet-setup/setup/ubuntu/` on the target and runs the same
checked, resumable steps: apt CLIs (build-essential, fd, btop, stress-ng, lm-sensors, `gh` from
GitHub's apt repository), `tailscale set --operator`, a silent `PATH` block at the top of
`~/.bashrc` (so `ssh <host> codex ...` finds the agent CLIs), tmux auto-attach and the shared-box
banner for interactive logins, `~/.tmux.conf`, git's `init.defaultBranch` and the identity of the
machine running `apply`, the house tools `heavy` / `pressure` / `agent-status` / `git-autosync`
(rendered for the target's threads and RAM; `git-autosync` takes `.work/land.lock` across its
fast-forward) with its 3-minute timer, OpenCode, Muse, grok, Antigravity (`agy`) and osv-scanner,
and the agent rules file `~/MACHINE.md` rendered from the target's measured facts. The logins
(`gh auth login`, `opencode auth login`, then `muse`, `grok` and `agy` once each) stay by hand.
Rootless Docker is left out.

## 6. Verify

```sh
python3 docs/fleet/scripts/fleet_setup.py add <host> --check   # every step ok but the hand ones
python3 docs/fleet/scripts/fleet_setup.py mesh --check         # every pair ok
python3 docs/fleet/scripts/fleet_setup.py verify <host>        # fleet_sync.py status here and there, fleet_stop.py status
```

`verify` is read-only: nothing is synced and no flag is written.

## macOS

`fleet_setup.py box` supports Ubuntu only. A Mac follows the same list by hand: section 1
with System Settings' Remote Login in place of openssh-server, Homebrew's `direnv` and
`rsync` in place of apt, the direnv hook in `~/.zshrc`, and `launchd` instead of lingering
(no step). Steps 3 to 6 are the same.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[fleet]: FLEET.md
[fleet-setup]: scripts/fleet_setup.py
[fleet-stop]: scripts/fleet_stop.py
[fleet-sync]: scripts/fleet_sync.py
[load-balancing]: scripts/load_balancing.py
[machines]: MACHINES.md
[machines-json]: machines.json
[personal]: scripts/setup/ubuntu/personal.py

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
