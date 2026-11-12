# SETUP.md: adding a machine to the fleet

The procedure for a new machine, from a bare Ubuntu install to a fleet member that
[docs/fleet/scripts/fleet_sync.py][fleet-sync], [docs/fleet/scripts/fleet_stop.py][fleet-stop] and
[docs/fleet/scripts/load_balancing.py][load-balancing] reach. [docs/fleet/scripts/fleet_setup.py][fleet-setup] does
every step it can; its module docstring is the full rule. What it cannot do (sudo's password,
logins, the timers, the sudoers rule) is the maintainer's, marked **by hand** below. The machines themselves are
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

`add` checks that `<host>` answers batch-mode ssh and is Ubuntu or macOS (see [macOS](#macos)),
copies the script, the shared PATH block (`setup/files/path.sh`) and the pins
(`setup/versions.json`, section 7) to `~/.cache/dsf-fleet-setup/` there, and runs its `box install` over `ssh -t`. Every step checks
first and runs only when its check fails, so a rerun after a failure resumes and a finished
machine reruns as a no-op. In order:

| Step | Kind | What |
| --- | --- | --- |
| `packages` | sudo | `git rsync curl direnv tmux ripgrep` from apt (a fresh Ubuntu Desktop lacks git) |
| `linger` | sudo | `loginctl enable-linger`: the save-sync timer is a systemd user timer, which stops at logout without it |
| `uv` | user | uv's installer for the pinned release into `~/.local/bin` |
| `pythons` | user | CPython 3.10 to 3.13, then 3.14 with `--default` (one version per `--default` call) |
| `direnv-hook` | user | `eval "$(direnv hook bash)"` in `~/.bashrc` |
| `node` | user | nvm and node at their pins, node as nvm's default |
| `codex` | user | `npm install -g @openai/codex@<pin>` under nvm's default node |
| `claude` | user | Claude Code's native installer for the pinned release into `~/.local/bin` |
| `pre-commit` | user | `uv tool install pre-commit==<pin>` (a stable interpreter for the git hook, START.md "Toolchain") |
| `path-block` | user | the one PATH block of every fleet machine, `setup/files/path.sh`, first in the file the shell reads for a non-interactive `ssh <host> <command>`: `~/.bashrc` on Linux (above Ubuntu's interactive guard), `~/.zshenv` on macOS; a changed file is kept as `<name>.bak-<seconds>` |
| `ssh-key` | keys | `~/.ssh/id_ed25519` with no passphrase (fleet ssh is batch mode) |
| `checkout` | user | `git clone` of the public https URL to `~/projects/django-strawberry-framework` (no GitHub key needed; pushes stay the maintainer's) |
| `python-version` | user | `.python-version` (git-ignored, so a clone lacks it), copied from the machine running `add` |
| `venv` | user | `uv sync --frozen` |
| `hook` | user | `pre-commit install` |
| `direnv-allow` | user | `direnv allow` on the checkout |
| `strawberry-django` | user | the reference source `~/projects/strawberry-django-main`: GitHub's tarball of strawberry-graphql-django's pinned tag, unpacked as a plain tree (section 2a) |
| `django-graphene-filters` | user | the reference clone `~/projects/django-graphene-filters`: an https clone of `riodw/django-graphene-filters` detached at the pinned tag (section 2a) |
| `graphene-django` | user | `uv sync --frozen` in that clone, so its `.venv` holds the pinned graphene-django (section 2a) |
| `logins` | by hand | reported only, below |
| `timer` | by hand | reported only, below |

`--skip sudo,keys` runs only what needs no password and writes no key (how an agent tests
the script); `box check` / `box install --only <step>,...` on the machine itself run part of
the list.

## 2a. The reference sources

AGENTS.md sends agents to two upstream trees, at the same paths on every machine, macOS and Linux
alike: `~/projects/strawberry-django-main/strawberry_django` and `graphene_django` inside
`~/projects/django-graphene-filters/.venv`. The three steps above put them there at the versions
[setup/versions.json][versions] pins (`strawberry-django`: the upstream tag, which has no `v`;
`django-graphene-filters`: the tag of the clone; `graphene-django`: the version its `.venv`
must hold). `fleet_update.py check` reports each against its pin and `apply` brings a machine to
it with the same lines (section 7). Each step is idempotent and never overwrites what differs:

- **strawberry-django** is read by the `version` its `pyproject.toml` names. A tree at another
  version is replaced (new tree unpacked first, then swapped in) only when it equals its own
  version's tarball (`diff -r`, `__pycache__` and `.DS_Store` aside); a tree that differs, or names
  no version, is left as it is and the step fails naming it.
- **django-graphene-filters** is `ok` at the tag, `ahead` past it (a working checkout carrying the
  tag's history: present, never moved, so rio-air's own repository checks as present) and
  `behind` short of it. A clone is moved forward only when it is clean, detached, from that
  origin and behind the tag; one on a branch, with local changes, from another origin or diverged
  is never changed. `check` reads with `--no-optional-locks`, so it never rewrites that
  checkout's index.
- **graphene-django**: `uv sync --frozen --python <newest>` runs only in a clean clone from that
  origin.

A pin bump is the same one-line edit as a tool's (section 7).

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
CLI tools, dotfiles, GNOME settings, Toshy and the GNOME Shell extensions; no desktop GUI
application. Run `apply` from a real terminal: sudo asks once, and Toshy's installer asks its own
questions:

```sh
python3 docs/fleet/scripts/setup/ubuntu/personal.py apply <host> --check   # what <host> lacks
python3 docs/fleet/scripts/setup/ubuntu/personal.py apply <host>           # install it
```

It copies its folder to `~/.cache/dsf-fleet-setup/setup/ubuntu/` on the target and runs the same
checked, resumable steps: apt CLIs (build-essential, fd, btop, stress-ng, lm-sensors, `gh` from
GitHub's apt repository), `tailscale set --operator`, the core `path-block` step again (the same
check, writer and block file, carried in its bundle), tmux auto-attach and the shared-box
banner for interactive logins, `~/.tmux.conf`, git's `init.defaultBranch` and the identity of the
machine running `apply`, the house tools `heavy` / `pressure` / `agent-status`
(rendered for the target's threads and RAM), OpenCode 2 at its pin (`https://opencode.ai/v2/install`;
`https://opencode.ai/install` installs only OpenCode 1), Muse, grok, Antigravity (`agy`) and
osv-scanner, the agent rules file `~/MACHINE.md` rendered from the target's measured facts, and `rio-ubu`'s
GNOME settings (`files/desktop/dconf.ini`: fonts, clock, input, window buttons and keybindings,
Nautilus and file-chooser views, Ptyxis and Text Editor, the dock on the left at 40 px, no sleep on
AC, location off) plus the Files sidebar's `~/projects`, four New Document templates and the
"Copy Path" script; the dock keeps only the favourites the target has installed. Before the
desktop settings come Toshy (release `Toshy_v26.11.0`, through its own `setup_toshy.py install`;
it adds the user to `input`) with `rio-ubu`'s keyboard-type slice and preferences, and the GNOME
Shell extensions `rio-ubu` runs, pinned to its versions (Vitals, Executor, Clipboard Indicator,
Focused Window D-Bus, Move Clock, Pinned Apps in AppGrid, Workspace Islands, plus apt's
`gnome-shell-extensions` set). Toshy's installer stops once to show that Focused Window D-Bus is
installed but not running and asks for the code it prints: type it. Log out and back in after
the run: new extensions, Toshy's keymapper and the `input` group start only with a new login.
Each step is checked again right before its turn, so a step an earlier one disturbed (Toshy's
installer rewrites the Overview shortcut) is put back in the same run. The logins
(`gh auth login`, `opencode auth login`, then `muse`, `grok` and `agy` once each) stay by hand.
Desktop GUI applications and rootless Docker are left out.

## 6. Verify

```sh
python3 docs/fleet/scripts/fleet_setup.py add <host> --check   # every step ok but the hand ones
python3 docs/fleet/scripts/fleet_setup.py mesh --check         # every pair ok
python3 docs/fleet/scripts/fleet_setup.py verify <host>        # fleet_sync.py status here and there, fleet_stop.py status, version drift, strays, the tools
```

`verify` runs the box's own `fleet_update.py check` (section 7; exit 1 on version drift), the
box's own stray check (`fleet_setup.py box strays` in its checkout, section 7) and `ssh <host>
'command -v uv git python3 node claude codex gh'` (plain, non-interactive ssh, as `fleet_sync.py`
and agents call it), failing naming each tool it does not find. It is read-only: nothing is
synced, installed or deleted and no flag is written.

## 7. Keep every machine updated: `fleet_update.py`

[fleet_update.py][fleet-update] brings each machine to the versions pinned in
[setup/versions.json][versions] (nvm, node, npm, Codex, Claude Code, uv, pre-commit, osv-scanner,
OpenCode through OpenCode 2's installer `https://opencode.ai/v2/install` given `VERSION=<pin>`;
Muse, grok and Antigravity read `latest`: their installers take no version; the reference
sources, section 2a) and updates the OS packages. Its module docstring is the full rule.

```sh
uv run python docs/fleet/scripts/fleet_update.py check --all   # read-only: one table, every machine; exit 1 on drift
uv run python docs/fleet/scripts/fleet_update.py apply         # this machine, one line per step
uv run python docs/fleet/scripts/fleet_update.py apply --all   # every machine at once
```

`check` shows pinned against installed per tool, a `shadowed` row for a file that runs instead of
the managed tool (with the command that removes it; nothing is deleted; the `PATH` searched is the
fleet's own, the PATH block read afresh behind nvm's default node, whoever runs `check`), the apt
and snap updates pending on Linux, and `brew outdated --greedy` plus `softwareupdate -l` on macOS.
It also runs the stray check (`fleet_setup.py`'s `strays`, the one `verify` runs): a `stray
<path>` row, and exit 1, for every git repository, worktree or bare clone of this repo under `~`
other than the checkout and its `.work/` copies (found by its `origin` or its root commit; the
walk skips `~/Library`, `~/.nvm`, the trash folders, `~/snap`, `~/.npm`, uv caches and
`node_modules`), and for every `~/projects/` entry other than the checkout, the two reference
folders, `AGENTS.md`, `AGENTS_READ_THIS_FIRST.md` and Finder's `.DS_Store`. A machine whose
[machines.json][machines-json] row sets `"other_projects": true` (rio-air only) may hold other
`~/projects/` entries; clones of this repo are still named there. Nothing is deleted: remove a
stray by hand once its work is saved.
`apply` never downgrades Claude Code past its pin (it updates itself: `ahead`), installs npm and
Codex after switching to nvm's default node (`nvm use default`, whatever node its own `PATH`
holds), runs a `latest` tool's installer every time, runs `brew update` and `brew upgrade
--greedy` on macOS but never a macOS system update, holds `.work/update.lock` and stops at the
fleet stop flag.

**Bump a version**: edit its one line in `setup/versions.json` (the current release: `npm view <package>
version`, the project's GitHub releases), run `fleet_update.py check` to see the drift, commit on
main. The save-sync timers fast-forward every machine's main and each machine's next daily
`apply` installs it.

**By hand, once per Linux machine**: the sudoers rule letting `apply` run exactly
`/usr/bin/apt-get update`, `/usr/bin/apt-get upgrade -y` and `/usr/bin/snap refresh` without a
password ([setup/files/sudoers-fleet-update][sudoers]). Print it, then paste the command it prints
(it validates with `visudo -cf` before the rule goes live):

```sh
python3 docs/fleet/scripts/fleet_update.py sudoers
```

Without it `apply` reports a `refused` row and prompts for nothing.

**By hand, once per machine**: the daily timer (launchd agent on macOS, systemd user timer on
Linux; 04:30 local plus up to 30 minutes of jitter, a 90-minute limit, logging to
`.work/fleet-update.log`). `schedule` alone prints what it would install:

```sh
cd ~/projects/django-strawberry-framework && uv run python docs/fleet/scripts/fleet_update.py schedule --install
```

**By hand, once per Mac**: Codex is npm under nvm's default node everywhere. A Mac's older Codex
(rio-air: npm with prefix `~/.local`; rio-mini: a standalone binary in `~/.local/bin`) shows as a
`codex shadow` row naming the file and the command that removes it; run that command after `apply`
has installed the pinned Codex under nvm.

## macOS

On a Mac, `fleet_setup.py box` runs `path-block`, which writes the shared PATH block to
`~/.zshenv` (zsh reads it for every shell, a non-interactive ssh command's included), and the
three reference-source steps (section 2a), on the stock `/usr/bin/python3`:

```sh
python3 docs/fleet/scripts/fleet_setup.py add <mac> --check   # read-only: the block first in ~/.zshenv, the reference sources
python3 docs/fleet/scripts/fleet_setup.py add <mac>           # write it, fetch them
```

The rest of the list stays by hand: section 1 with System Settings' Remote Login in place of
openssh-server, Homebrew's `direnv`, `rsync` and `gh` in place of apt, uv, nvm's node, Codex
and Claude Code from the same installers, the direnv hook in `~/.zshrc`, and `launchd`
instead of lingering (no step). Steps 3 to 6 are the same; `verify` checks that the tools the
block puts on `PATH` are found over plain ssh.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[fleet]: FLEET.md
[fleet-setup]: scripts/fleet_setup.py
[fleet-stop]: scripts/fleet_stop.py
[fleet-sync]: scripts/fleet_sync.py
[fleet-update]: scripts/fleet_update.py
[load-balancing]: scripts/load_balancing.py
[machines]: MACHINES.md
[machines-json]: machines.json
[personal]: scripts/setup/ubuntu/personal.py
[sudoers]: scripts/setup/files/sudoers-fleet-update
[versions]: scripts/setup/versions.json

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
