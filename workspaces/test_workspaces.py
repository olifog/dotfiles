import contextlib
import fcntl
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SOURCE=Path(__file__).resolve().parent

class WorkspaceTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  self.home=self.root/'home';self.home.mkdir()
  self.env=dict(os.environ,HOME=str(self.home),GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_AUTHOR_NAME='Test',GIT_AUTHOR_EMAIL='test@example.com',GIT_COMMITTER_NAME='Test',GIT_COMMITTER_EMAIL='test@example.com')
  self.remote=self.root/'origin.git';self.repo=self.root/'core'
  self.cmd('git','init','--bare','--initial-branch=main',str(self.remote))
  self.cmd('git','clone',str(self.remote),str(self.repo))
  (self.repo/'note').write_text('initial\n');self.git(self.repo,'add','note');self.git(self.repo,'commit','-m','initial');self.git(self.repo,'push','origin','main');self.git(self.repo,'remote','set-head','origin','main')
  # Existing hooks and settings must survive installation and reinstallation.
  hook=self.repo/'.git/hooks/pre-commit';hook.write_text('#!/bin/sh\necho original-hook >&2\n');hook.chmod(0o755)
  hook=self.repo/'.git/hooks/pre-push';hook.write_text('#!/bin/sh\ncat > "$HOME/push-input"\n');hook.chmod(0o755)
  (self.home/'.claude').mkdir();(self.home/'.claude/settings.json').write_text(json.dumps({'env':{'KEEP':'yes'},'hooks':{'Stop':[{'hooks':[{'type':'command','command':'true'}]}]}}))
  self.install()
  self.exe=self.home/'.local/bin/agent-workspace'
 def tearDown(self):self.temp.cleanup()
 def cmd(self,*args,ok=True,env=None,data=None):
  p=subprocess.run(args,env=env or self.env,input=data,text=True,capture_output=True)
  if ok:self.assertEqual(p.returncode,0,p.stderr+'\n'+p.stdout)
  return p
 def git(self,p,*args,**kw):return self.cmd('git','-C',str(p),*args,**kw)
 def install(self):return self.cmd('python3',str(SOURCE/'install.py'),'--repo','core='+str(self.repo))
 def aw(self,*args,**kw):return self.cmd(str(self.exe),*map(str,args),**kw)
 def start(self,name='task'):return Path(self.aw('start','core',name).stdout.strip())
 def upstream_commit(self,name='upstream',text='new\n'):
  other=self.root/name;self.cmd('git','clone',str(self.remote),str(other));(other/name).write_text(text);self.git(other,'add',name);self.git(other,'commit','-m',name);self.git(other,'push','origin','main');return other
 def test_start_fresh_despite_dirty_root_and_resume_unchanged(self):
  (self.repo/'note').write_text('unpublished\n');self.upstream_commit()
  wt=self.start();self.assertTrue((wt/'upstream').exists());self.assertEqual((self.repo/'note').read_text(),'unpublished\n')
  (wt/'note').write_text('work\n');self.assertEqual(self.start(),wt);self.assertEqual((wt/'note').read_text(),'work\n')
  self.assertEqual(self.git(wt,'config','--get','branch.olifog/task.remote',ok=False).returncode,1)
 def test_sync_dirty_diverged_and_fast_forward(self):
  self.upstream_commit();(self.repo/'note').write_text('dirty\n')
  self.assertEqual(json.loads(self.aw('sync','core').stdout)['sync'],'blocked-dirty')
  self.git(self.repo,'restore','note');self.assertEqual(json.loads(self.aw('sync','core').stdout)['sync'],'current')
  (self.repo/'local').write_text('local');self.git(self.repo,'add','local');self.git(self.repo,'-c','core.hooksPath=/dev/null','commit','-m','local')
  self.upstream_commit('next');before=self.git(self.repo,'rev-parse','HEAD').stdout
  self.assertEqual(json.loads(self.aw('sync','core').stdout)['sync'],'blocked-diverged');self.assertEqual(self.git(self.repo,'rev-parse','HEAD').stdout,before)
 def test_commit_and_push_guards_preserve_existing_hooks(self):
  (self.repo/'note').write_text('root change');self.git(self.repo,'add','note')
  self.assertNotEqual(self.git(self.repo,'commit','-m','blocked',ok=False).returncode,0)
  wt=self.start();(wt/'taskfile').write_text('task');self.git(wt,'add','taskfile');self.assertIn('original-hook',self.git(wt,'commit','-m','task').stderr)
  self.upstream_commit();self.assertNotEqual(self.git(wt,'push','origin','HEAD:refs/heads/feature',ok=False).returncode,0)
  self.aw('update',wt);self.git(wt,'push','origin','HEAD:refs/heads/feature')
  self.assertIn('refs/heads/feature',(self.home/'push-input').read_text())
 def test_conflict_is_left_for_review_without_stash(self):
  wt=self.start();(wt/'note').write_text('task version\n');self.git(wt,'add','note');self.git(wt,'commit','-m','task')
  other=self.root/'other';self.cmd('git','clone',str(self.remote),str(other));(other/'note').write_text('upstream version\n');self.git(other,'add','note');self.git(other,'commit','-m','upstream');self.git(other,'push','origin','main')
  self.assertNotEqual(self.aw('update',wt,ok=False).returncode,0)
  self.assertIn('UU note',self.git(wt,'status','--porcelain').stdout)
  self.assertEqual(self.git(wt,'stash','list').stdout,'')
  self.assertNotEqual(self.aw('start','core','task',ok=False).returncode,0)
 def test_failed_fetch_lock_and_dirty_update_fail_closed(self):
  wt=self.start();(wt/'note').write_text('dirty');self.assertNotEqual(self.aw('update',wt,ok=False).returncode,0)
  with (self.repo/'.git/agent-workspace.lock').open('a') as f:
   fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);self.assertNotEqual(self.aw('start','core','locked',ok=False).returncode,0)
  self.git(self.repo,'remote','set-url','origin',str(self.root/'missing'))
  self.assertNotEqual(self.aw('start','core','offline',ok=False).returncode,0)
  self.assertNotEqual(self.aw('sync','core',ok=False).returncode,0)
 def test_install_idempotent_and_hook_denial(self):
  paths=[self.home/'.claude/settings.json',self.home/'.codex/hooks.json',self.home/'.codex/AGENTS.md',self.home/'.codex/config.toml',self.repo/'.git/hooks/pre-push']
  before=[p.read_bytes() for p in paths];self.install();self.assertEqual(before,[p.read_bytes() for p in paths])
  settings=json.loads(paths[0].read_text());self.assertEqual(settings['env']['KEEP'],'yes');self.assertIn('Stop',settings['hooks'])
  payload={'cwd':str(self.repo),'hook_event_name':'PreToolUse','tool_name':'apply_patch','tool_input':{'command':'*** Begin Patch\n*** Update File: note\n@@\n-x\n+y\n*** End Patch'}}
  self.assertEqual(json.loads(self.aw('hook',data=json.dumps(payload)).stdout)['hookSpecificOutput']['permissionDecision'],'deny')
  wt=self.start();payload['cwd']=str(wt);self.assertEqual(self.aw('hook',data=json.dumps(payload)).stdout,'')
 def test_named_app_worktree_works_but_detached_rejected(self):
  wt=self.root/'app';self.git(self.repo,'worktree','add','--detach',str(wt),'HEAD')
  self.assertNotEqual(self.aw('guard',wt,'pre-commit',ok=False).returncode,0)
  self.git(wt,'switch','-c','olifog/app');self.aw('guard',wt,'pre-commit')
 def test_legacy_app_worktree_checks_its_own_refs(self):
  legacy=self.root/'legacy';self.cmd('git','clone',str(self.remote),str(legacy))
  app=self.root/'legacy-app';self.git(legacy,'worktree','add','-b','olifog/old',str(app),'HEAD')
  self.cmd('python3',str(SOURCE/'install.py'),'--legacy-root','core='+str(legacy))
  self.upstream_commit()
  result=json.loads(self.aw('check',app).stdout);self.assertEqual(result['behind'],1)
  self.assertFalse((legacy/'.git/hooks/pre-commit').exists())
  new=Path(self.aw('start',legacy,'new-task').stdout.strip())
  self.assertEqual(self.git(new,'rev-parse','--path-format=absolute','--git-common-dir').stdout.strip(),str((self.repo/'.git').resolve()))
 def test_other_handler_in_managed_group_is_preserved(self):
  path=self.home/'.claude/settings.json';settings=json.loads(path.read_text())
  settings['hooks']['SessionStart'][0]['hooks'].append({'type':'command','command':'echo user-hook'})
  path.write_text(json.dumps(settings));self.install()
  groups=json.loads(path.read_text())['hooks']['SessionStart']
  self.assertEqual(sum(h['command']=='echo user-hook' for g in groups for h in g['hooks']),1)
 def test_missing_origin_head_is_discovered(self):
  self.git(self.repo,'symbolic-ref','--delete','refs/remotes/origin/HEAD')
  self.install()
  self.assertEqual(self.git(self.repo,'symbolic-ref','--short','refs/remotes/origin/HEAD').stdout.strip(),'origin/main')
 def test_custom_hooks_path_is_preserved(self):
  path=self.repo/'.hooks';path.mkdir();hook=path/'pre-commit';hook.write_text('#!/bin/sh\necho custom >&2\n');hook.chmod(0o755)
  self.git(self.repo,'config','core.hooksPath',str(path));self.install()
  wt=self.start();(wt/'file').write_text('x');self.git(wt,'add','file');self.assertIn('custom',self.git(wt,'commit','-m','x').stderr)
  self.assertEqual(self.git(self.repo,'config','core.hooksPath').stdout.strip(),str(path))

if __name__=='__main__':unittest.main(verbosity=2)
