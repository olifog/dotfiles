# Paths and environment used by both interactive and non-interactive Fish.
fish_add_path --global /opt/homebrew/bin /opt/homebrew/sbin $HOME/.local/bin $HOME/bin

set -gx EDITOR nvim
set -gx VISUAL nvim
set -gx PAGER less
set -gx HOMEBREW_NO_ANALYTICS 1

if not status is-interactive
    return
end

set -g fish_greeting

# Fish abbreviations expand at the prompt, so scripts still see the real tools.
abbr --add c clear
abbr --add g git
abbr --add ga 'git add'
abbr --add gc 'git commit'
abbr --add gd 'git diff'
abbr --add gl 'git log --oneline --decorate --graph'
abbr --add gs 'git status --short --branch'
abbr --add lg lazygit
abbr --add l 'eza --icons=auto --group-directories-first'
abbr --add ll 'eza --icons=auto --group-directories-first --long --all --git'
abbr --add lt 'eza --icons=auto --group-directories-first --tree --level=2'
abbr --add cat 'bat --paging=never'
abbr --add top btop
abbr --add vim nvim
abbr --add zj zellij

command -q mise; and mise activate fish | source
command -q direnv; and direnv hook fish | source
command -q fzf; and fzf --fish | source
command -q zoxide; and zoxide init fish | source
command -q starship; and starship init fish | source

# Every new Ghostty window gets a fresh Zellij session. Set NO_ZELLIJ=1 to opt out.
if set -q TERM_PROGRAM
    and test "$TERM_PROGRAM" = ghostty
    and not set -q ZELLIJ
    and not set -q NO_ZELLIJ
    and not set -q SSH_CONNECTION
    and command -q zellij
    exec zellij
end
