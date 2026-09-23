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

## phone and browser Remote Control

open the Claude mobile app's **Code** tab using Oliver's Flappy account. the
cluster entry sessions are **Together core**, **Cheetah core**, **Thor core**, and
**Loki core**. paste a core task-note link to start a worker. the same sessions
are at https://claude.ai/code. a new device may require another SSO sign-in.

for a new cluster, after the Claude and workspace installers, run:

```sh
python3 ~/.dotfiles/claude/claude-rc install --host together
# Use the registered core path printed by the installer:
cd /path/printed/by/installer
~/.local/bin/claude-account
# Complete terminal onboarding and workspace trust, then exit Claude.
~/.local/bin/claude-account remote-control
# Accept its one-time RC confirmation. Once connected, Ctrl+C and wait for exit.
~/.local/bin/claude-rc start
~/.local/bin/claude-rc status
```

agents handle these commands; Oliver does not need to run them for normal work.
substitute the host alias on each cluster. installation merges settings and backs
up changed files. it does not copy tokens or write internal trust records.

Cheetah, Thor and Loki use a user systemd service with restart-on-failure.
user lingering is required to start at boot without an SSH login; it is enabled
on these three hosts. repeated rapid failures stop the service after five starts
in ten minutes: inspect `journalctl --user -u claude-rc.service`, fix the cause,
then `systemctl --user reset-failed claude-rc.service` and `claude-rc start`.
Together has no user service manager. it uses a dedicated tmux server with a
supervisor and retry backoff up to five minutes. it survives SSH disconnects and
laptop sleep. after a login-container restart, the next interactive Fish or
profile login starts it again; it cannot run while the container is down.

`claude-rc start`, `stop`, and `status` manage only this dedicated server. stop
also disables its automatic startup. `start` is idempotent and does not restart
active sessions. after updating the launcher, deliberately stop/start only when
its sessions are idle. Together's terminal is available with
`tmux -L claude-rc attach -t core`; detach with Ctrl+B then D.

servers use account auth, manual tool approvals, and `--spawn worktree`, with
capacity four (two on Loki). the initial entry session stays in the registered
core reference; task hooks/guidance direct writes into a fresh session-specific
`agent-workspace` worktree. on-demand sessions receive Claude worktrees too.
Together uses the fresh independent core clone, leaving legacy writers alone.
no timed pull/rebase is added by RC. the existing reference sync and task
freshness checks remain responsible for Git state.

remote hosts also set `remoteControlAtStartup: true`, so future interactive
Claude sessions can appear on the phone. existing running sessions are not
restarted. these extra entries are individual sessions; Desktop SSH connections
and RC entry sessions are separate. the installer does not enable this on Mac.

RC resumes its previous sessions after a short restart, currently within about
four hours. longer outages can produce a new entry session. RC status output
proves server registration, not that a particular phone has connected. the UI
must show **Connected via Remote Control** to verify the device connection.

## sources

- https://code.claude.com/docs/en/desktop#ssh-sessions
- https://code.claude.com/docs/en/setup
- https://code.claude.com/docs/en/memory#use-agentsmd
- https://code.claude.com/docs/en/remote-control
