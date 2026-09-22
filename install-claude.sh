#!/usr/bin/env bash
set -euo pipefail
dotfiles_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -x "$HOME/.local/bin/claude" ]] && ! command -v claude >/dev/null 2>&1; then
    installer="$(mktemp)"
    trap 'rm -f "$installer"' EXIT
    curl -fsSL https://claude.ai/install.sh -o "$installer"
    bash "$installer"
fi
python3 "$dotfiles_dir/claude/configure.py" "$@"
echo 'Claude configuration ready. Sign in with: ~/.local/bin/claude-account auth login'
