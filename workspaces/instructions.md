## shared Git workspaces

- Oliver normally starts a task by pasting its filename in a new Codex chat
  with `/goal`. that is sufficient. YOU handle workspace setup automatically;
  never ask Oliver to run a command, name a branch, or choose a worktree.
- for a new task-file request, before reading the task context, run
  `~/.local/bin/agent-workspace task core TASK_FILE` yourself. it fetches upstream
  and derives a task branch from the filename and `CODEX_THREAD_ID`, which Codex
  supplies. another chat for the same task gets its own branch. if that variable
  is absent (e.g. Claude), pass `--session` with your current session/chat ID
  from hook context. do not invent a different ID on resume.
- use the returned path for every read, edit, test, and Git command. shell cd
  does not change the app's registered cwd: set workdir or absolute paths on
  subsequent tools. read the current task file there, even if the attachment
  or saved project points at an older checkout. follow its approved scope.
- if this task already has a worktree, retain it and check freshness there;
  do not migrate ongoing work or create another branch on every prompt.
- for work without a task filename, choose a descriptive task slug yourself
  and use `~/.local/bin/agent-workspace start REPO TASK`.
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
