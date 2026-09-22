# shared agent workspaces

one workflow for Codex and Claude, on macOS and Linux. core is the common source
of context. each task writes in its own worktree, starting from fetched upstream.

## install

```sh
./install-workspaces.sh --repo core="$HOME/core" --repo hangar="$HOME/hangar" --schedule
```

use actual paths from core's `system/hosts.yaml`. registration records the remote
default branch via `origin/HEAD`, discovering it from the remote if absent.
the installer preserves settings, personal instructions, and pre-existing Git
hooks. backups live under `~/.local/state/agent-workspace/install-backups/`.
installation does not change authentication, providers, models, or permissions.

`--legacy-root core=/old/core` recognizes an old checkout for startup guidance
without installing hooks or changing files in that checkout. it is transitional;
new worktrees are created from the registered reference, never from legacy HEAD.

## task lifecycle

Oliver starts a new Codex chat with `/goal tasks/TASK.md` (or the task filename).
the agent runs setup itself before reading task context. no terminal preparation
or user-chosen branch is required. global instructions carry this requirement;
SessionStart/UserPromptSubmit hooks reinforce it when trusted.

`agent-workspace task core TASK_FILE` derives a stable branch from the filename
and `CODEX_THREAD_ID`. separate chats get separate worktrees; a resumed chat
reuses its own. Claude can supply `--session` from hook context. agents explicitly
use the returned tool workdir; the app's registered cwd is not silently changed.
existing task worktrees are retained. the following commands are agent internals
or optional terminal conveniences, not steps Oliver must perform.

```sh
# prints one path, suitable for cd; works even if the old root is dirty or stale
cd "$(~/.local/bin/agent-workspace start core describe-the-task)"
# terminal launchers also set the process working directory
~/.local/bin/agent-workspace run core describe-the-task -- codex
~/.local/bin/agent-workspace run core describe-the-task -- "$HOME/.local/bin/claude-account"

# on resume: fetch and report, without changing files or rebasing
~/.local/bin/agent-workspace check /absolute/task/worktree
# after a reviewed commit, at phase boundaries / before publishing
~/.local/bin/agent-workspace update /absolute/task/worktree
# review and run affected checks after a rebase
# core only, where direct publication is authorized:
git push origin HEAD:main
# code repositories: push the task branch and use the repository's PR process
```

`start` reuses an existing worktree for the same task branch. it never silently
resets it. fetch failure aborts startup. new branches have no tracking upstream
until explicitly published, so plain `git push` cannot accidentally target main.
`update` refuses dirty trees and in-progress operations, disables automatic
stashing and rerere during its rebase, and leaves conflicts for review.
`git rebase --abort` returns to the pre-rebase task state when needed.
never rebase on a timer. no command here automatically commits, pushes, deletes
worktrees, resets files, or resolves conflicts.

## enforcement and its limits

- pre-commit rejects the registered shared root, detached HEAD, and main.
- pre-push fetches the remote default branch and rejects branch updates that do
  not contain it. a failed fetch also blocks the push. use an explicit lease if
  a reviewed feature-branch rebase requires rewriting your own published branch;
  never force-push shared main. ordinary main races are rejected by Git.
- existing pre-commit/pre-push hooks are chained with their arguments and stdin.
  the installer leaves `core.hooksPath` unchanged. relative custom hooks paths
  must be provisioned in each worktree by that repository's own setup process.
- Claude and Codex get shared global instructions and SessionStart guidance.
  supported file-edit hooks deny writes into registered reference roots.
- Codex requires reviewing and trusting non-managed hooks through `/hooks`.
  newly installed hooks remain inactive until trusted. Git hooks and the CLI
  work independently of that approval. existing sessions may need restart to
  load new instructions. no trust database is edited or bypassed.
- hooks are guardrails, not an OS write sandbox. arbitrary shell programs can
  still write files, and `--no-verify` bypasses Git hooks. scripts should always
  use the CLI; agents must follow the instructions for shell edits too.
- app-created worktrees are supported after naming the branch and checking
  freshness. the installer does not silently move an already-running app task.

## automatic reference updates

`agent-workspace sync core` fetches then fast-forwards only a clean reference on
its default branch with no local-only commits or Git operation. dirty files,
divergence, and non-main branches produce explicit blocked states. nothing is
stashed or overwritten. sync never rebases task worktrees. `sync all` also fetches
registered code repositories, whose reference files are left alone by default.

`agent-workspace status` reads timestamped results from
`~/.local/state/agent-workspace/*.json`. check `checked_at`, not just `current`:
an old success does not establish present freshness.

`--schedule` uses a five-minute LaunchAgent on the Mac and user systemd timers
where available. it disables the old Mac vault-sync LaunchAgent. on Together's
login container, where neither a user manager nor cron exists, a single small
Python process performs the same check every five minutes. its kernel lock
prevents duplicate processes per host; Fish login / `.profile` and
`agent-workspace ensure-daemon` restart it after container replacement. it is
not a system supervisor, so a fresh login is needed after a crash/replacement.
all task starts still fetch independently of the timer.

## human Obsidian edits and recovery

Oliver can edit the laptop vault as before. automatic pulls pause while notes
are dirty. the sync helper first snapshots changes, transfers/reviews the note
changes in a fresh worktree, and publishes them. restore the shared checkout
only after comparing the live file with the preserved copy and confirming it
has not changed. `.obsidian/app.json` and `appearance.json` stay local and ignored.
`AGENT_WORKSPACE_HUMAN=1` is an explicit escape hatch for a reviewed human sync;
agent launchers never set it.

`snapshot.py REPO...` saves Git history bundles, working and staged patches,
tracked/untracked files, hashes, and worktree inventories outside the repository.
it omits ignored files. snapshots are recovery evidence, not consistent live
filesystem snapshots: inspect the race flags before using them. never wholesale
restore stale task status over current upstream. existing active checkouts must
be reconciled after their owners finish, with semantic decisions surfaced.

## test and rollback

```sh
python3 -m unittest discover -s workspaces -p 'test_*.py'
```

tests use local bare remotes and temporary homes. they cover fresh starts,
resumes, dirty/divergent references, conflicts, unavailable remotes, locks,
existing hook chaining, app worktrees, and additive/idempotent installation.

for rollback, stop the LaunchAgent/user timer (or the recorded Together daemon
PID), restore settings from the installation backup, and replace only the
marked Git hook wrappers with their `.before-agent-workspace` originals.
do not remove original hooks or delete worktrees containing task work.

sources: [Codex hooks](https://learn.chatgpt.com/docs/hooks),
[Claude hooks](https://code.claude.com/docs/en/hooks).
