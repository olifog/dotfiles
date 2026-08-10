#!/usr/bin/env bash
set -euo pipefail

dotfiles_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
brew_bin="/opt/homebrew/bin/brew"
install_packages=true
[[ "${1:-}" == "--links-only" ]] && install_packages=false

backup_root="$HOME/.dotfiles-backups/$(date +%Y%m%d-%H%M%S)"
managed_paths=(
  ".gitconfig"
  ".config/fish/config.fish"
  ".config/ghostty"
  ".config/mise"
  ".config/nvim"
  ".config/starship.toml"
  ".config/zellij"
)

for relative_path in "${managed_paths[@]}"; do
  source_path="$dotfiles_dir/$relative_path"
  target_path="$HOME/$relative_path"

  # Older versions linked the whole Fish directory. Convert that symlink to a
  # real directory so host-specific conf.d snippets can coexist with config.fish.
  if [[ "$relative_path" == ".config/fish/config.fish" ]] && [[ -L "$HOME/.config/fish" ]]; then
    if [[ "$(readlink "$HOME/.config/fish")" == "$dotfiles_dir/.config/fish" ]]; then
      unlink "$HOME/.config/fish"
      mkdir -p "$HOME/.config/fish"
    fi
  fi

  if [[ -L "$target_path" ]] && [[ "$(readlink "$target_path")" == "$source_path" ]]; then
    continue
  fi

  if [[ -e "$target_path" || -L "$target_path" ]]; then
    mkdir -p "$backup_root/$(dirname "$relative_path")"
    mv "$target_path" "$backup_root/$relative_path"
    echo "Backed up $target_path"
  fi

  mkdir -p "$(dirname "$target_path")"
  ln -s "$source_path" "$target_path"
  echo "Linked $target_path"
done

if $install_packages; then
  case "$(uname -s)" in
    Darwin)
      if [[ ! -x "$brew_bin" ]]; then
        echo "Homebrew was not found at $brew_bin" >&2
        exit 1
      fi
      "$brew_bin" bundle --file "$dotfiles_dir/Brewfile"
      ;;
    Linux)
      if [[ ! -x "$HOME/.local/bin/mise" ]]; then
        curl -fsSL https://mise.run | sh
      fi
      "$HOME/.local/bin/mise" install --yes

      bash_marker="# >>> dotfiles Fish launcher >>>"
      if ! grep -qF "$bash_marker" "$HOME/.bashrc" 2>/dev/null; then
        mkdir -p "$backup_root"
        [[ -e "$HOME/.bashrc" ]] && cp -p "$HOME/.bashrc" "$backup_root/.bashrc"
        {
          printf '\n%s\n' "$bash_marker"
          printf '%s\n' "if [[ \$- == *i* ]] && [[ -n \${SSH_TTY:-} ]] && [[ -z \${NO_FISH:-} ]] && [[ -x \"\$HOME/.local/bin/mise\" ]]; then"
          printf '%s\n' "    exec \"\$HOME/.local/bin/mise\" exec -- fish"
          printf '%s\n' 'fi' '# <<< dotfiles Fish launcher <<<'
        } >> "$HOME/.bashrc"
        echo "Configured interactive SSH sessions to launch Fish"
      fi
      ;;
    *)
      echo "Package installation is not supported on $(uname -s); links are installed." >&2
      ;;
  esac
fi

if [[ -d "$backup_root" ]]; then
  echo "Backups: $backup_root"
fi
