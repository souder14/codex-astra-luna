"""Windows-first, backup-gated configuration merger. Does not run model tasks."""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, queue, shutil, subprocess, threading
import tomllib
import tomlkit

REPO = pathlib.Path(__file__).resolve().parents[1]
NAMES = {'config.toml', 'AGENTS.md', 'AGENTS.override.md', 'agents/luna-worker.toml',
         'skills/astra-luna/SKILL.md', 'skills/astra-luna/agents/openai.yaml'}
BEGIN = '<!-- BEGIN ASTRA-LUNA ORCHESTRATION POLICY -->'
END = '<!-- END ASTRA-LUNA ORCHESTRATION POLICY -->'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

def safe_path(root, name):
    if name not in NAMES:
        raise ValueError(f'Unexpected manifest path: {name}')
    root = root.resolve()
    path = root / name
    if not path.resolve().is_relative_to(root):
        raise ValueError(f'Path escapes root: {name}')
    for part in [path, *path.parents]:
        if part == root: break
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise ValueError(f'Linked path is not supported: {part}')
    return path

def verify_snapshot(backup, home, snapshot):
    if {f['name'] for f in snapshot['files']} != NAMES or len(snapshot['files']) != len(NAMES):
        raise ValueError('Snapshot must cover exactly all potentially modified files')
    for f in snapshot['files']:
        src = safe_path(home, f['name'])
        if f['existed']:
            saved = safe_path(backup, f['name'])
            if digest(saved) != f['sha256'] or digest(src) != f['sha256']:
                raise ValueError(f'Backup/live checksum mismatch: {f["name"]}')
        elif src.exists():
            raise ValueError(f'Originally absent path now exists: {f["name"]}')
    if not (backup/'restore.ps1').is_file():
        raise ValueError('Standalone restore.ps1 missing')

def merge(document, patch):
    """Preserve unknown keys/comments; convert feature booleans into tables."""
    for key, value in patch.items():
        if isinstance(value, dict):
            existing = document.get(key)
            if isinstance(existing, bool) and key in ('multi_agent_v2', 'context_management'):
                document[key] = tomlkit.table()
            elif existing is None:
                document[key] = tomlkit.table()
            elif not hasattr(existing, 'items'):
                raise ValueError(f'Cannot safely merge non-table {key}')
            merge(document[key], value)
        else:
            document[key] = value
    return document

def merge_policy(original, policy):
    if BEGIN in original or END in original:
        if original.count(BEGIN) != 1 or original.count(END) != 1:
            raise ValueError('Ambiguous managed policy markers')
        start, end = original.index(BEGIN), original.index(END)
        if end < start: raise ValueError('Reversed policy markers')
        return original[:start] + policy.strip() + original[end+len(END):]
    return original.rstrip() + '\n\n' + policy.strip() + '\n'

def render(home):
    desired = tomllib.loads((REPO/'templates/config.toml').read_text(encoding='utf-8'))
    config = home/'config.toml'
    document = tomlkit.parse(config.read_text(encoding='utf-8-sig') if config.exists() else '')
    existing_v2 = document.get('features', {}).get('multi_agent_v2', {})
    if hasattr(existing_v2, 'get'):
        for key in ['root_agent_usage_hint_text', 'subagent_developer_instructions']:
            old = existing_v2.get(key)
            new = desired['features']['multi_agent_v2'][key]
            if old and new.strip() not in str(old):
                desired['features']['multi_agent_v2'][key] = str(old).rstrip() + '\n\n' + new
            elif old:
                desired['features']['multi_agent_v2'][key] = str(old)
    output = {'config.toml': tomlkit.dumps(merge(document, desired))}
    instruction = 'AGENTS.override.md' if (home/'AGENTS.override.md').exists() else 'AGENTS.md'
    path = home/instruction
    original = path.read_text(encoding='utf-8-sig') if path.exists() else ''
    output[instruction] = merge_policy(original, (REPO/'templates/policy.md').read_text(encoding='utf-8'))
    role_path = home/'agents/luna-worker.toml'
    if role_path.exists():
        role = tomlkit.parse(role_path.read_text(encoding='utf-8-sig'))
        role['model'] = 'gpt-6-luna'; role['model_reasoning_effort'] = 'high'
        output['agents/luna-worker.toml'] = tomlkit.dumps(role)
    else:
        output['agents/luna-worker.toml'] = (REPO/'templates/luna-worker.toml').read_text(encoding='utf-8')
    for name in ['skills/astra-luna/SKILL.md', 'skills/astra-luna/agents/openai.yaml']:
        path = home/name
        if path.exists() and path.read_text(encoding='utf-8') != (REPO/name).read_text(encoding='utf-8'):
            raise ValueError(f'Existing skill differs: {name}; review and merge manually after backup')
        output[name] = (REPO/name).read_text(encoding='utf-8')
    for name, text in output.items():
        if name.endswith('.toml'): tomllib.loads(text)
    return output, desired

def flatten(values, prefix=''):
    for key, value in values.items():
        path = f'{prefix}.{key}' if prefix else key
        if isinstance(value, dict): yield from flatten(value, path)
        else: yield path, value

def assert_effective(config, desired):
    for path, expected in flatten(desired):
        actual = config
        for key in path.split('.'): actual = actual[key]
        if isinstance(expected, str) and isinstance(actual, str):
            expected, actual = expected.replace('\r\n','\n'), actual.replace('\r\n','\n')
        if actual != expected: raise ValueError(f'Effective configuration mismatch: {path}')

def inspect_client(exe, home, cwd, backup, desired, overrides=False):
    env = dict(os.environ, CODEX_HOME=str(home))
    extra=[]
    if overrides:
        for path, value in flatten(desired):
            literal=tomlkit.dumps({'value':value}).split('=',1)[1].strip()
            extra += ['-c',f'{path}={literal}']
    label='probe' if overrides else 'installed'
    with (backup/f'{label}.stderr').open('w',encoding='utf-8') as err:
        proc=subprocess.Popen([str(exe),'app-server','--stdio','--strict-config',*extra],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,encoding='utf-8',env=env)
        mailbox=queue.Queue()
        def reader():
            for line in proc.stdout:
                try: mailbox.put(json.loads(line))
                except ValueError: pass
            mailbox.put({'terminated':True})
        threading.Thread(target=reader,daemon=True).start()
        def request(i,method,params):
            proc.stdin.write(json.dumps(dict(id=i,method=method,params=params))+'\n'); proc.stdin.flush()
            while True:
                msg=mailbox.get(timeout=60)
                if msg.get('terminated'): raise RuntimeError(f'Client stopped; inspect {label}.stderr')
                if msg.get('id')==i:
                    if 'error' in msg: raise RuntimeError(msg['error'])
                    return msg['result']
        try:
            request(1,'initialize',{'clientInfo':{'name':'astra_luna_setup','version':'1.0'},'capabilities':{'experimentalApi':True}})
            result=request(2,'config/read',{'includeLayers':True,'cwd':str(cwd)})
            requirements=request(3,'configRequirements/read',{})
            (backup/f'{label}-effective.json').write_text(json.dumps({'config':result,'requirements':requirements},indent=2),encoding='utf-8')
            assert_effective(result['config'],desired)
        finally:
            proc.terminate()
            try: proc.wait(timeout=10)
            except subprocess.TimeoutExpired: proc.kill(); proc.wait()

def check_models(exe, home):
    result=subprocess.run([str(exe),'debug','models'],env=dict(os.environ,CODEX_HOME=str(home)),
                          capture_output=True,text=True,encoding='utf-8',timeout=60,check=True)
    catalog=json.loads(result.stdout)
    models=catalog if isinstance(catalog,list) else catalog['models']
    for slug, effort in [('gpt-6-astra','medium'),('gpt-6-luna','high')]:
        model=next((m for m in models if m.get('slug')==slug),None)
        if not model or effort not in [r['effort'] for r in model.get('supported_reasoning_levels',[])]:
            raise ValueError(f'Client catalog does not confirm {slug} / {effort}; stop, do not substitute')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backup',type=pathlib.Path,required=True)
    parser.add_argument('--codex',type=pathlib.Path,required=True,help='Native Codex executable, not a .cmd/.ps1 wrapper')
    parser.add_argument('--cwd',type=pathlib.Path,default=pathlib.Path.cwd())
    parser.add_argument('--apply',action='store_true',help='Without this, only stage a plan and probe compatibility')
    args=parser.parse_args()
    if os.name!='nt': parser.error('Automated rollback currently requires Windows; follow SETUP.md on other platforms')
    if not args.codex.is_file() or args.codex.suffix.lower()!='.exe': parser.error('Provide the installed native codex.exe')
    backup=args.backup.resolve();snapshot=json.loads((backup/'snapshot.json').read_text(encoding='utf-8-sig'))
    if snapshot.get('phase')!='before': raise ValueError('Use a before snapshot')
    home=pathlib.Path(snapshot['codexHome']).resolve()
    verify_snapshot(backup,home,snapshot)
    output,desired=render(home)
    check_models(args.codex,home)
    inspect_client(args.codex,home,args.cwd,backup,desired,overrides=True)
    for name,text in output.items():
        staged=backup/'planned'/name;staged.parent.mkdir(parents=True,exist_ok=True);staged.write_text(text,encoding='utf-8')
    print('Compatibility probe passed. Review the staged files privately at:',backup/'planned')
    if not args.apply: return
    verify_snapshot(backup,home,snapshot)  # Detect changes while probing; never overwrite concurrent edits.
    for f in snapshot['files']:
        f['introduced']=not f['existed'] and f['name'] in output
    (backup/'snapshot.json').write_text(json.dumps(snapshot,indent=2),encoding='utf-8')
    try:
        for name,text in output.items():
            path=safe_path(home,name);path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(text,encoding='utf-8')
        inspect_client(args.codex,home,args.cwd,backup,desired,overrides=False)
    except BaseException:
        restored=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(backup/'restore.ps1'),'-Force'])
        if restored.returncode: raise RuntimeError(f'Automatic restoration failed; run {backup / "restore.ps1"} immediately')
        raise
    print('Configuration applied and strict-client validated. Runtime smoke tests and AFTER snapshot remain required; see SETUP.md.')
    print('Rollback script:',backup/'restore.ps1')

if __name__=='__main__': main()
