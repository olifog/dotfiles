#!/usr/bin/env python3
import pathlib, subprocess, datetime, json, tarfile, hashlib, os, sys
h=pathlib.Path.home(); stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
base=h/'.local/state/agent-workspace/recovery'/stamp;base.mkdir(parents=True,mode=0o700)
if len(sys.argv)<2:raise SystemExit('usage: snapshot.py REPO...')
for arg in sys.argv[1:]:
 p=pathlib.Path(arg).expanduser().resolve(); name=p.name.lstrip('.')
 if not p.exists():continue
 d=base/name;d.mkdir()
 def git(*args):return subprocess.check_output(['git','-C',str(p),*args])
 (d/'status.txt').write_bytes(git('status','--porcelain=v1','-uall'))
 (d/'worktrees.txt').write_bytes(git('worktree','list','--porcelain'))
 (d/'working.patch').write_bytes(git('diff','--binary','HEAD'))
 (d/'index.patch').write_bytes(git('diff','--cached','--binary'))
 (d/'head.txt').write_bytes(git('rev-parse','HEAD'))
 git('bundle','create',str(d/'history.bundle'),'--all')
 files=set(git('ls-files','-z').split(b'\0')+git('ls-files','--others','--exclude-standard','-z').split(b'\0'))-{b''}
 manifest={}
 with tarfile.open(d/'files.tar.gz','w:gz',dereference=False) as t:
  for raw in sorted(files):
   f=os.fsdecode(raw);q=p/f
   if q.is_file() or q.is_symlink():
    before=q.lstat();t.add(q,arcname=f,recursive=False);after=q.lstat()
    manifest[f]={'sha256':hashlib.sha256(q.read_bytes()).hexdigest() if not q.is_symlink() else None,'changed_during_copy':(before.st_mtime_ns,before.st_size)!=(after.st_mtime_ns,after.st_size)}
 (d/'manifest.json').write_text(json.dumps(manifest,indent=2))
 print(json.dumps({'repo':name,'snapshot':str(d),'files':len(manifest),'raced':sum(x['changed_during_copy'] for x in manifest.values())}))
