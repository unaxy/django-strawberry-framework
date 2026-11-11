# Interactive ssh logins attach to tmux session `main` (login shells only, never `bash -c`/`-ic cmd`;
# detach with Ctrl-b d; skip with `NO_TMUX=1 ssh ...`).
if [[ $- == *i* && -n "$SSH_CONNECTION" && -z "$TMUX" && -z "$NO_TMUX" && -z "$BASH_EXECUTION_STRING" ]] && shopt -q login_shell && command -v tmux >/dev/null; then
  tmux new-session -A -s main
fi
# Shared-box banner on interactive ssh/tmux shells (agents and humans).
if [[ $- == *i* && ( -n "$SSH_CONNECTION" || -n "$TMUX" ) && -z "$BASH_EXECUTION_STRING" ]] && [ -x "$HOME/.local/bin/pressure" ]; then
  printf '\033[1;33m>> %s is a SHARED box. Read ~/AGENTS_READ_THIS_FIRST.md. Run `pressure` before heavy work; wrap it with `heavy <cmd>`.\033[0m\n' "$(hostname)"
  "$HOME/.local/bin/pressure" --short
fi
