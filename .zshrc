export PATH=$HOME/bin:$HOME/.local/bin:/usr/local/bin:$PATH

# Path to your Oh My Zsh installation.
export ZSH="$HOME/.oh-my-zsh"

ZSH_THEME="robbyrussell"

HYPHEN_INSENSITIVE="true"

HIST_STAMPS="dd/mm/yyyy"

plugins=(git ssh-agent nvm pip starship)

source $ZSH/oh-my-zsh.sh

# User configuration

# Preferred editor for local and remote sessions
if [[ -n $SSH_CONNECTION ]]; then
  export EDITOR='vim'
else
  export EDITOR='nvim'
fi

alias cfg='/usr/bin/git --git-dir=$HOME/.cfg --work-tree=$HOME'
alias ezla='eza -la'

export FPATH="/home/olifog/.config/eza/completions/zsh:$FPATH"
