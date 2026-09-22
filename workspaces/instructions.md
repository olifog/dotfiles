## shared Git workspaces

- before reading task context or editing a registered repo, use
  `~/.local/bin/agent-workspace start REPO TASK` for a new task. it fetches the
  remote default branch and creates `olifog/TASK` in a separate worktree. use
  that returned path for every read, edit, test, and Git command.
- resume the same task in its existing worktree. run
  `~/.local/bin/agent-workspace check /absolute/worktree` to fetch and compare.
  never interpret a failed fetch as proof that a checkout is current.
- Codex app worktrees are fine, but check freshness and use a named task branch
  before editing. do not assume the app's initial HEAD is current upstream.
- shared root checkouts are references. agents must not write or commit there.
  existing dirty roots are recovery material, not a source to copy over current
  task status. read the current notes in your fresh task worktree.
- commit small, reviewed changes. at a phase boundary or before publishing, run
  `~/.local/bin/agent-workspace update /absolute/worktree`. it requires a clean
  worktree, fetches, and rebases. review the result and rerun affected checks.
  never schedule rebases, autostash another task's work, or force-push main.
- surface conflicts about meaning or status. resolve only mechanical conflicts.
  do not automatically publish a partially resolved rebase.
- core: publish reviewed notes with `git push origin HEAD:main`; code repos:
  push a task branch and follow the repository's PR process. push guards require
  the pushed branch to contain the freshly fetched remote default branch.
- run `~/.local/bin/agent-workspace status` for last reference-sync results.
  blocked-dirty/diverged is visible debt, not a successful update.
- Oliver may keep editing the laptop vault through Obsidian. isolate and review
  those changes before publishing; preserve host-local Obsidian settings.
