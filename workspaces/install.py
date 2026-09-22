#!/usr/bin/env python3
"""Additive installation; no shell settings, credentials or existing Git hooks are discarded."""
import argparse, datetime, json, os, pathlib, plistlib, re, shlex, shutil, subprocess, sys
P=pathlib.Path
HOME=P.home();SOURCE=P(__file__).resolve().parent
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
backup=HOME/'.local/state/agent-workspace/install-backups'/stamp

def write(path,text,mode=None):
 path=P(path);path.parent.mkdir(parents=True,exist_ok=True)
 data=text.encode() if isinstance(text,str) else text
 if path.exists() and path.read_bytes()==data:
  if mode is not None:path.chmod(mode)
  return
 if path.exists() or path.is_symlink():
  dest=backup/str(path).lstrip('/');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest,follow_symlinks=True)
 if path.is_symlink():raise RuntimeError('Refusing to replace symlink '+str(path))
 tmp=path.with_name(path.name+'.agent-workspace-new');tmp.write_bytes(data)
 tmp.chmod(mode if mode is not None else (path.stat().st_mode & 0o777 if path.exists() else 0o600))
 os.replace(tmp,path)

def command(*args):return subprocess.check_output(args,text=True,timeout=45,env=dict(os.environ,GIT_TERMINAL_PROMPT='0',GIT_SSH_COMMAND='ssh -o BatchMode=yes -o ConnectTimeout=10')).strip()
def block(path,text):
 start='<!-- agent-workspace:start -->';end='<!-- agent-workspace:end -->'
 old=path.read_text() if path.exists() else ''
 part=start+'\n'+text.strip()+'\n'+end
 if start in old:
  old=re.sub(re.escape(start)+'.*?'+re.escape(end),lambda m:part,old,flags=re.S)
 else:old=old.rstrip()+'\n\n'+part+'\n'
 write(path,old)

def install_hooks(repo):
 for event in ['pre-commit','pre-push']:
  path=P(command('git','-C',str(repo),'rev-parse','--path-format=absolute','--git-path','hooks/'+event))
  path.parent.mkdir(parents=True,exist_ok=True)
  original=path.with_name(path.name+'.before-agent-workspace')
  marker='# agent-workspace hook v1'
  if path.exists() and marker not in path.read_text(errors='replace'):
   if original.exists():raise RuntimeError('Hook backup already exists; inspect '+str(original))
   # Rename preserves executable mode, symlinks and exact pre-existing behavior.
   path.rename(original)
  prefix='#!/bin/sh\n'+marker+'\n'
  guard=shlex.quote(str(HOME/'.local/bin/agent-workspace'))+' guard "$PWD" '+event
  if event=='pre-push':
   script=prefix+'input=$(mktemp) || exit 1\ntrap \'rm -f "$input"\' EXIT HUP INT TERM\ncat > "$input"\n'+guard+' < "$input" || exit $?\n'
   script+='if [ -x '+shlex.quote(str(original))+' ]; then '+shlex.quote(str(original))+' "$@" < "$input"; exit $?; fi\n'
  else:
   script=prefix+guard+' || exit $?\nif [ -x '+shlex.quote(str(original))+' ]; then exec '+shlex.quote(str(original))+' "$@"; fi\n'
  write(path,script,0o755)

def schedule():
 exe=str(HOME/'.local/bin/agent-workspace')
 if sys.platform=='darwin':
  log=HOME/'Library/Logs/agent-workspace.log';log.parent.mkdir(parents=True,exist_ok=True)
  path=HOME/'Library/LaunchAgents/com.olifog.agent-workspace.plist'
  uid=str(os.getuid())
  old=HOME/'Library/LaunchAgents/com.olifog.vault-sync.plist'
  if old.exists():
   subprocess.run(['launchctl','bootout','gui/'+uid,str(old)],capture_output=True)
   old.rename(old.with_suffix('.plist.disabled-agent-workspace'))
  write(path,plistlib.dumps(dict(Label='com.olifog.agent-workspace',ProgramArguments=[exe,'sync','core'],RunAtLoad=True,StartInterval=300,StandardOutPath=str(log),StandardErrorPath=str(log),EnvironmentVariables={'PATH':'/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin'})))
  subprocess.run(['launchctl','bootout','gui/'+uid,str(path)],capture_output=True)
  subprocess.run(['launchctl','bootstrap','gui/'+uid,str(path)],check=True)
 else:
  available=subprocess.run(['systemctl','--user','show-environment'],capture_output=True).returncode==0 if shutil.which('systemctl') else False
  if available:
   directory=HOME/'.config/systemd/user'
   # systemd percent escaping is separate from shell quoting.
   escaped=exe.replace('%','%%').replace('"','\\"')
   write(directory/'agent-workspace-sync.service','[Unit]\nDescription=Fetch and safely fast-forward the core reference\n\n[Service]\nType=oneshot\nExecStart="'+escaped+'" sync core\n')
   write(directory/'agent-workspace-sync.timer','[Unit]\nDescription=Check core freshness every five minutes\n\n[Timer]\nOnBootSec=1min\nOnUnitActiveSec=5min\nPersistent=true\n\n[Install]\nWantedBy=timers.target\n')
   subprocess.run(['systemctl','--user','daemon-reload'],check=True)
   subprocess.run(['systemctl','--user','enable','--now','agent-workspace-sync.timer'],check=True)
  else:
   # Unprivileged login containers have no systemd/cron. One small process per host,
   # protected by a kernel lock; restarted by the user's shell after container restart.
   write(HOME/'.config/fish/conf.d/agent-workspace.fish','if status is-interactive\n    '+shlex.quote(exe)+' ensure-daemon >/dev/null 2>&1\nend\n')
   profile=HOME/'.profile';old=profile.read_text() if profile.exists() else ''
   line=shlex.quote(exe)+' ensure-daemon >/dev/null 2>&1 # agent-workspace-daemon'
   if line not in old:write(profile,old.rstrip()+'\n'+line+'\n')
   subprocess.run([exe,'ensure-daemon'],check=True)

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo',action='append',default=[],metavar='NAME=PATH')
parser.add_argument('--schedule',action='store_true')
parser.add_argument('--legacy-root',action='append',default=[],metavar='NAME=PATH')
a=parser.parse_args()
for name in ['agent-workspace']:
 write(HOME/'.local/bin'/name,(SOURCE/name).read_bytes(),0o755)
registry=HOME/'.config/agent-workspace/repos.json'
data=json.loads(registry.read_text()) if registry.exists() else {'repos':{}}
for spec in a.repo:
 name,path=spec.split('=',1)
 if not re.fullmatch('[a-z0-9][a-z0-9_-]*',name):raise RuntimeError('Invalid repo name')
 path=P(command('git','-C',str(P(path).expanduser()),'rev-parse','--show-toplevel')).resolve()
 result=subprocess.run(['git','-C',str(path),'symbolic-ref','--short','refs/remotes/origin/HEAD'],text=True,capture_output=True,timeout=15)
 if result.returncode==0:branch=result.stdout.strip().removeprefix('origin/')
 else:
  refs=command('git','-C',str(path),'ls-remote','--symref','origin','HEAD')
  match=re.search(r'^ref: refs/heads/(.+)\s+HEAD$',refs,re.M)
  if not match:raise RuntimeError('Cannot determine the remote default branch for '+str(path))
  branch=match.group(1).strip()
  command('git','-C',str(path),'fetch','--quiet','origin','+refs/heads/'+branch+':refs/remotes/origin/'+branch)
  command('git','-C',str(path),'symbolic-ref','refs/remotes/origin/HEAD','refs/remotes/origin/'+branch)
 data['repos'][name]=dict(data['repos'].get(name,{}),path=str(path),branch=branch,autosync=name=='core')
for spec in a.legacy_root:
 name,path=spec.split('=',1)
 roots=data['repos'][name].setdefault('legacy_roots',[])
 root=str(P(path).expanduser().resolve())
 if root not in roots:roots.append(root)
write(registry,json.dumps(data,indent=2)+'\n')
for entry in data['repos'].values():install_hooks(entry['path'])
policy=(SOURCE/'instructions.md').read_text()
block(HOME/'.codex/AGENTS.md',policy)
block(HOME/'.claude/CLAUDE.md',policy)
for path in [HOME/'.codex/hooks.json',HOME/'.claude/settings.json']:
 settings=json.loads(path.read_text()) if path.exists() else {}
 for event in ['SessionStart','PreToolUse']:
  groups=settings.setdefault('hooks',{}).setdefault(event,[])
  hook={'hooks':[{'type':'command','command':shlex.quote(str(HOME/'.local/bin/agent-workspace'))+' hook','timeout':15}]}
  if event=='PreToolUse':hook['matcher']='Edit|Write|MultiEdit|NotebookEdit|apply_patch'
  # Replace only our exact managed handler, preserving unrelated hooks.
  managed_command=hook['hooks'][0]['command']
  retained=[]
  for group in groups:
   handlers=[h for h in group.get('hooks',[]) if h.get('command')!=managed_command]
   if handlers:retained.append(dict(group,hooks=handlers))
  groups[:]=retained+[hook]
 write(path,json.dumps(settings,indent=2)+'\n')
path=HOME/'.codex/config.toml';old=path.read_text() if path.exists() else ''
match=re.search(r'^\[features\]\s*$',old,re.M)
if match:
 end=re.search(r'^\[',old[match.end():],re.M)
 stop=match.end()+end.start() if end else len(old)
 section=old[match.end():stop]
 if re.search(r'^hooks\s*=',section,re.M):section=re.sub(r'^hooks\s*=.*$', 'hooks = true',section,flags=re.M)
 else:section='\nhooks = true\n'+section
 old=old[:match.end()]+section+old[stop:]
else:old+='\n[features]\nhooks = true\n'
write(path,old)
if a.schedule:schedule()
print(json.dumps({'registered':list(data['repos']),'backups':str(backup),'codex_hooks':'review/trust with /hooks in new Codex sessions; Git guards work independently'}))
