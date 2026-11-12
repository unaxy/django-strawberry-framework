# PATH for every shell, non-interactive ssh commands included (`ssh <host> codex ...`); the same block
# on every fleet machine: macOS in ~/.zshenv (zsh reads it for every shell), Linux at the top of
# ~/.bashrc (above Ubuntu's interactive-only guard). It must stay silent. Only folders that exist
# are added; the newest nvm node comes first.
for _d in /opt/homebrew/bin "$HOME/.opencode/bin" "$HOME/.grok/bin" "$HOME/.local/bin" $(find "$HOME/.nvm/versions/node" -mindepth 2 -maxdepth 2 -name bin -type d 2>/dev/null | sort -V | tail -1); do
  [ -d "$_d" ] || continue
  case ":$PATH:" in *":$_d:"*) ;; *) PATH="$_d:$PATH" ;; esac
done
unset _d; export PATH
