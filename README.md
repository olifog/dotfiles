# Oliver's dotfiles

A small, Fish-first setup for macOS and Linux clusters. It installs the
command-line toolchain and links the configuration into `~/.config`.

## Included

- Fish with native abbreviations and completions
- Starship prompt and Zoxide directory jumping
- Zellij, started automatically inside Ghostty (set `NO_ZELLIJ=1` to opt out)
- Ghostty with an adaptive Catppuccin theme
- Minimal, plugin-free Neovim configuration
- A `cursor .` shim that opens local paths directly and emits a safe,
  Cmd-clickable Cursor Remote SSH link when run on a cluster
- Modern CLI tools including eza, bat, btop, fd, ripgrep, fzf, delta,
  lazygit, yazi, dust, procs, sd, tealdeer, direnv, and mise

## Install

```sh
./install.sh
```

The installer is idempotent. Existing managed files are moved to a timestamped
directory below `~/.dotfiles-backups` before symlinks are created. macOS uses
Homebrew; Linux installs Mise and prebuilt tools entirely below your home
directory, without requiring root access.

To install only the symlinks and skip Homebrew packages:

```sh
./install.sh --links-only
```

Afterward, make Fish the login shell:

```sh
fish_path="$(brew --prefix)/bin/fish"
grep -qxF "$fish_path" /etc/shells || echo "$fish_path" | sudo tee -a /etc/shells
chsh -s "$fish_path"
```

On Linux clusters, the installer deliberately leaves Bash as the account login
shell for compatibility with environment modules and schedulers. Interactive
SSH sessions enter Fish from `.bashrc`; use `NO_FISH=1 ssh host` to opt out.
Host-specific files in `~/.config/fish/conf.d` are preserved.

For the remote Cursor link, set `DOTFILES_HOST` in a host-specific `conf.d`
file to the matching alias from the Mac's `~/.ssh/config`. Remote terminals
cannot launch local GUI processes directly, so the generated link requires a
Cmd-click in Ghostty.

Reload Ghostty's config with <kbd>Cmd</kbd>+<kbd>Shift</kbd>+<kbd>,</kbd>, or
fully quit and reopen Ghostty after changing the login shell.
