# Claude alongside Codex

run `bash ~/.dotfiles/install-claude.sh` on each active cluster. on the Mac,
add `--desktop` to register Together, Cheetah, Thor, and Loki in Claude Desktop.
connections use the existing SSH aliases, keys, and proxy routes.

the native CLI installs under `~/.local/bin` and updates itself. the setup merges
settings, backs up changed files, and leaves Codex configuration alone.
it imports the host's personal Codex guidance into Claude. if none exists,
it uses the cluster instruction snapshot captured from Together on 2026-09-22.
repository `AGENTS.md` and `CLAUDE.md` both load through Claude's built-in
`agents-md` plugin. the global instructions also request nested `AGENTS.md` reads
when that plugin is unavailable, such as the first session after installation.

## desktop

in Claude's Code tab, open the environment menu and select a cluster. choose the
repository folder on that host. Together is the default place for durable work;
the other hosts are for direct debugging. host paths live in core's
`system/hosts.yaml`. Eland is retired and is not registered.

## terminal

use `~/.local/bin/claude-account auth login` on the host, then run `claude` from
Fish in the repository. Fish's `claude` function invokes the account launcher.
from Bash or scripts, use `~/.local/bin/claude-account` explicitly.
the account launcher clears only `ANTHROPIC_BASE_URL`, `ANTHROPIC_API_KEY`, and
`ANTHROPIC_AUTH_TOKEN` for that process so old gateway exports cannot override
the chosen Claude/Flappy account route. other tools keep their existing gateway
environment. the installer does not copy authentication tokens.

Claude Desktop SSH and `claude remote-control` are separate features. Remote
Control requires an eligible claude.ai account, an admin-enabled feature on
Team/Enterprise, and the direct Anthropic endpoint. it does not support a custom
LLM gateway. desktop SSH uses the desktop app's authentication.

use separate worktrees when Claude and Codex edit the same repository at once.
keep task status and durable knowledge in core; neither app's session history is
the shared source of truth. app-specific plugins and credentials do not transfer.

## sources

- https://code.claude.com/docs/en/desktop#ssh-sessions
- https://code.claude.com/docs/en/setup
- https://code.claude.com/docs/en/memory#use-agentsmd
- https://code.claude.com/docs/en/remote-control
