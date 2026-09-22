#!/usr/bin/env python3
"""Add Claude guidance and optional desktop SSH aliases without replacing settings."""

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
from datetime import datetime, timezone

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--desktop", action="store_true", help="add active cluster SSH aliases")
args = parser.parse_args()
home = Path.home()
claude = home / ".claude"
claude.mkdir(exist_ok=True, mode=0o700)
backup = home / ".dotfiles-backups" / datetime.now(timezone.utc).strftime("claude-%Y%m%dT%H%M%S%fZ")


def write(path, content, mode=0o600):
    if path.exists() and path.read_text() == content:
        return
    if path.is_symlink():
        raise SystemExit(f"Refusing to replace symlink: {path}")
    if path.exists():
        backup.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup / path.name)
    temp = path.with_name(path.name + ".dotfiles-tmp")
    with temp.open("x") as stream:
        os.chmod(temp, mode)
        stream.write(content)
    temp.replace(path)
    print(f"Configured {path}")


settings_path = claude / "settings.json"
settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
settings.setdefault("pluginConfigs", {}).setdefault("agents-md@builtin", {}).setdefault(
    "options", {}
)["instructionFiles"] = "claude-md-and-agents-md"
if args.desktop:
    connections = settings.setdefault("sshConfigs", [])
    for host in ("together", "cheetah", "thor", "loki"):
        if not any(item.get("sshHost") == host for item in connections):
            connections.append({"id": f"oliver-{host}", "name": host.title(), "sshHost": host})
write(settings_path, json.dumps(settings, indent=2) + "\n")

codex_guidance = home / ".codex" / "AGENTS.md"
if codex_guidance.exists() and codex_guidance.read_text().strip():
    instruction_import = "@~/.codex/AGENTS.md"
else:
    write(claude / "cluster-instructions.md", (Path(__file__).parent / "cluster-instructions.md").read_text())
    instruction_import = "@~/.claude/cluster-instructions.md"

start = "<!-- dotfiles:claude:start -->"
end = "<!-- dotfiles:claude:end -->"
block = f"""{start}
# shared working context

{instruction_import}

- core is Oliver's source of truth for approved work and current status.
- when working on a core task, read its home.md, system/operating-model.md,
  relevant task and project notes, and system/hosts.yaml before choosing a host.
- Together is the durable control host. Cheetah, Thor, and Loki are compute and
  direct-debug hosts. Eland is retired from new work.
- read the relevant AGENTS.md files before editing, including nested files.
  they are shared with Codex. do not assume a nested CLAUDE.md replaces them.
- use separate Git worktrees for concurrent Claude and Codex edits.
- keep durable findings in core. session transcripts are execution history.
{end}
"""
guidance_path = claude / "CLAUDE.md"
old = guidance_path.read_text() if guidance_path.exists() else ""
if start in old and end in old:
    before, rest = old.split(start, 1)
    _, after = rest.split(end, 1)
    content = before + block.rstrip("\n") + after
elif start in old or end in old:
    raise SystemExit(f"Incomplete managed block in {guidance_path}; inspect it before retrying")
else:
    content = old.rstrip() + ("\n\n" if old.strip() else "") + block
write(guidance_path, content)
bin_dir = home / ".local/bin"
bin_dir.mkdir(parents=True, exist_ok=True)
write(bin_dir / "claude-account", (Path(__file__).parent / "claude-account").read_text(), 0o700)
fish_functions = home / ".config/fish/functions"
fish_functions.mkdir(parents=True, exist_ok=True)
write(fish_functions / "claude.fish", (Path(__file__).parent / "claude.fish").read_text())
if sys.platform.startswith("linux") and str(home / ".local/bin") not in os.environ.get("PATH", "").split(":"):
    bashrc = home / ".bashrc"
    shell_config = bashrc.read_text() if bashrc.exists() else ""
    marker = "# Claude Code native CLI (non-interactive SSH too)"
    if marker not in shell_config:
        write(bashrc, marker + '\nexport PATH="$HOME/.local/bin:$PATH"\n\n' + shell_config)
if backup.exists():
    print(f"Backups: {backup}")
