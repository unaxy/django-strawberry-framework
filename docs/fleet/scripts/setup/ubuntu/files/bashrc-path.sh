# PATH for every shell, non-interactive ssh commands included (`ssh <host> codex ...`): this block
# sits above Ubuntu's interactive-only guard, so it must stay silent. Newest nvm node first.
for _d in "$HOME/.opencode/bin" "$HOME/.grok/bin" "$HOME/.local/bin" $(ls -d "$HOME"/.nvm/versions/node/v*/bin 2>/dev/null | sort -V | tail -1); do
  case ":$PATH:" in *":$_d:"*) ;; *) PATH="$_d:$PATH" ;; esac
done
unset _d; export PATH
