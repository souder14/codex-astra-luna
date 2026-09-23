import hashlib, importlib.util, json, os, pathlib, shutil, subprocess, tempfile, unittest
import tomllib
from unittest import mock

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('configure',ROOT/'scripts/configure.py')
setup=importlib.util.module_from_spec(spec);spec.loader.exec_module(setup)

class MergeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.home=pathlib.Path(self.tmp.name)
        (self.home/'config.toml').write_text('# keep this comment\nmodel="old"\n[features]\nremote_control=true\nmulti_agent_v2=false\n[mcp_servers.local]\ncommand="example"\n',encoding='utf-8')

    def test_merge_preserves_unrelated_and_is_idempotent(self):
        (self.home/'AGENTS.md').write_text('Preserve this user instruction.\n')
        output,desired=setup.render(self.home)
        parsed=tomllib.loads(output['config.toml'])
        self.assertEqual(parsed['mcp_servers']['local']['command'],'example')
        self.assertTrue(parsed['features']['remote_control'])
        self.assertIn('# keep this comment',output['config.toml'])
        self.assertEqual(parsed['features']['multi_agent_v2']['max_concurrent_threads_per_session'],6)
        self.assertTrue(output['AGENTS.md'].startswith('Preserve this user instruction.'))
        for name,text in output.items():
            p=self.home/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8')
        again,_=setup.render(self.home)
        self.assertEqual(output,again)

    def test_override_and_role_instructions_preserved(self):
        (self.home/'AGENTS.md').write_text('Untouched base')
        (self.home/'AGENTS.override.md').write_text('Effective user policy')
        p=self.home/'agents/luna-worker.toml';p.parent.mkdir();p.write_text('model="gpt-5.6-luna"\nmodel_reasoning_effort="max"\ndeveloper_instructions="custom instruction"\n')
        output,_=setup.render(self.home)
        self.assertNotIn('AGENTS.md',output)
        self.assertIn('Effective user policy',output['AGENTS.override.md'])
        role=tomllib.loads(output['agents/luna-worker.toml'])
        self.assertEqual(role['developer_instructions'],'custom instruction')
        self.assertEqual(role['model'],'gpt-6-luna')

    def test_custom_hints_preserved(self):
        (self.home/'config.toml').write_text('[features.multi_agent_v2]\nroot_agent_usage_hint_text="Keep this custom hint"\n')
        output,_=setup.render(self.home)
        self.assertIn('Keep this custom hint',tomllib.loads(output['config.toml'])['features']['multi_agent_v2']['root_agent_usage_hint_text'])

    def test_conflicting_skill_requires_review(self):
        p=self.home/'skills/astra-luna/SKILL.md';p.parent.mkdir(parents=True);p.write_text('Custom skill')
        with self.assertRaisesRegex(ValueError,'Existing skill differs'): setup.render(self.home)

    def test_duplicate_toml_rejected(self):
        (self.home/'config.toml').write_text('model="a"\nmodel="b"\n')
        with self.assertRaises(Exception): setup.render(self.home)

    def test_unsafe_path_and_policy_markers_rejected(self):
        with self.assertRaises(ValueError): setup.safe_path(self.home,'../outside')
        with self.assertRaises(ValueError): setup.merge_policy(setup.BEGIN+'\n'+setup.BEGIN+'\n'+setup.END,'x')

    def test_backup_change_detection(self):
        backup=self.home/'backup';backup.mkdir();(backup/'restore.ps1').write_text('fixture')
        entries=[]
        for name in setup.NAMES:
            p=self.home/name;entry={'name':name,'existed':p.exists()}
            if p.exists():
                q=backup/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
                entry['sha256']=setup.digest(p)
            entries.append(entry)
        snap={'files':entries};setup.verify_snapshot(backup,self.home,snap)
        (self.home/'config.toml').write_text('changed concurrently')
        with self.assertRaisesRegex(ValueError,'mismatch'):setup.verify_snapshot(backup,self.home,snap)

    def test_effective_override_mismatch_detected(self):
        with self.assertRaisesRegex(ValueError,'mismatch'):
            setup.assert_effective({'model':'other'},{'model':'gpt-6-astra'})

@unittest.skipUnless(os.name=='nt','Windows ACL/PowerShell integration')
class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.home=pathlib.Path(self.tmp.name)/'home';self.home.mkdir()
        self.original=b'# original\r\nmodel = "original"\r\n'
        (self.home/'config.toml').write_bytes(self.original)
        # Mock version/help only. No model calls, auth or live config access.
        bindir=pathlib.Path(self.tmp.name)/'bin';bindir.mkdir()
        (bindir/'codex.cmd').write_text('@echo off\necho codex-cli-test\nexit /b 0\n')
        self.env=dict(os.environ,PATH=str(bindir)+os.pathsep+os.environ['PATH'])
        result=self.run_ps(ROOT/'scripts/backup.ps1','-CodexHome',str(self.home),'-Timestamp','20260101-010101')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.backup=self.home/'backups/astra-luna-before-20260101-010101'

    def run_ps(self,script,*args):
        return subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script),*args],capture_output=True,text=True,env=self.env,timeout=60)

    def test_roundtrip_removes_only_introduced_files(self):
        manifest=json.loads((self.backup/'snapshot.json').read_text(encoding='utf-8-sig'))
        for f in manifest['files']:
            if f['name']=='skills/astra-luna/SKILL.md':f['introduced']=True
        (self.backup/'snapshot.json').write_text(json.dumps(manifest),encoding='utf-8')
        (self.home/'config.toml').write_text('new contents')
        p=self.home/'skills/astra-luna/SKILL.md';p.parent.mkdir(parents=True);p.write_text('introduced')
        other=self.home/'AGENTS.override.md';other.write_text('unrelated later file')
        result=self.run_ps(self.backup/'restore.ps1','-Force')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual((self.home/'config.toml').read_bytes(),self.original)
        self.assertFalse(p.exists());self.assertTrue(other.exists())
        self.assertTrue((self.backup/'config.toml').exists())

    def test_corruption_stops_before_any_live_write(self):
        (self.backup/'config.toml').write_text('corrupt')
        (self.home/'config.toml').write_text('keep live')
        result=self.run_ps(self.backup/'restore.ps1','-Force')
        self.assertNotEqual(result.returncode,0)
        self.assertEqual((self.home/'config.toml').read_text(),'keep live')

    def test_verify_and_whatif_do_not_change_live_files(self):
        (self.home/'config.toml').write_text('keep live')
        for flag in ['-VerifyOnly','-WhatIf']:
            result=self.run_ps(self.backup/'restore.ps1',flag)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertEqual((self.home/'config.toml').read_text(),'keep live')

    def test_apply_validation_failure_automatically_restores(self):
        exe=pathlib.Path(self.tmp.name)/'codex.exe';exe.write_bytes(b'fixture')
        argv=['configure.py','--backup',str(self.backup),'--codex',str(exe),'--cwd',str(self.home),'--apply']
        with mock.patch('sys.argv',argv), mock.patch.object(setup,'check_models'), mock.patch.object(setup,'inspect_client',side_effect=[None,RuntimeError('simulated validation failure')]):
            with self.assertRaisesRegex(RuntimeError,'simulated validation failure'):setup.main()
        self.assertEqual((self.home/'config.toml').read_bytes(),self.original)
        self.assertFalse((self.home/'AGENTS.md').exists())
        self.assertFalse((self.home/'agents/luna-worker.toml').exists())
        self.assertFalse((self.home/'skills/astra-luna/SKILL.md').exists())

if __name__=='__main__':unittest.main()
