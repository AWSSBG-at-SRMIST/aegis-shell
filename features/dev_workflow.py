import os
import re
import json
import subprocess
import platform
from pathlib import Path
from typing import Optional, Dict, List
from colorama import Fore, Style


# ── Auto .env loader ──────────────────────────────────────────────────────────

def load_dotenv(directory: str = '.') -> Dict[str, str]:
    env_file = Path(directory) / '.env'
    if not env_file.exists():
        return {}
    loaded = {}
    for line in env_file.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            key, _, val = line.partition('=')
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            os.environ[key] = val
            loaded[key] = val
    return loaded


# ── Auto virtualenv activation ────────────────────────────────────────────────

def detect_venv(directory: str = '.') -> Optional[str]:
    base = Path(directory)
    candidates = [
        base / 'venv' / ('Scripts' if platform.system() == 'Windows' else 'bin') / (
            'activate.bat' if platform.system() == 'Windows' else 'activate'
        ),
        base / '.venv' / ('Scripts' if platform.system() == 'Windows' else 'bin') / (
            'activate.bat' if platform.system() == 'Windows' else 'activate'
        ),
        base / 'env' / ('Scripts' if platform.system() == 'Windows' else 'bin') / (
            'activate.bat' if platform.system() == 'Windows' else 'activate'
        ),
    ]
    for c in candidates:
        if c.exists():
            return str(c.parent.parent)
    return None


def activate_venv(venv_path: str):
    if platform.system() == 'Windows':
        activate = str(Path(venv_path) / 'Scripts' / 'python.exe')
    else:
        activate = str(Path(venv_path) / 'bin' / 'python')
    os.environ['VIRTUAL_ENV'] = venv_path
    scripts = str(Path(venv_path) / ('Scripts' if platform.system() == 'Windows' else 'bin'))
    os.environ['PATH'] = scripts + os.pathsep + os.environ.get('PATH', '')
    print(Fore.GREEN + f'[Aegis] Activated venv: {venv_path}' + Style.RESET_ALL)


# ── Port Manager ──────────────────────────────────────────────────────────────

def list_ports():
    try:
        import psutil
        conns = psutil.net_connections(kind='inet')
        seen = {}
        for c in conns:
            if c.status == 'LISTEN' and c.laddr:
                port = c.laddr.port
                try:
                    proc = psutil.Process(c.pid) if c.pid else None
                    name = proc.name() if proc else '?'
                except Exception:
                    name = '?'
                seen[port] = name
        if not seen:
            print(Fore.YELLOW + '[Aegis] No listening ports found.' + Style.RESET_ALL)
            return
        print(Fore.CYAN + f'{"PORT":<8} {"PROCESS":<20}' + Style.RESET_ALL)
        print('─' * 30)
        for port in sorted(seen):
            print(f'{port:<8} {seen[port]:<20}')
    except ImportError:
        print(Fore.RED + '[Aegis] psutil not available.' + Style.RESET_ALL)


def kill_port(port: int) -> bool:
    try:
        import psutil
        killed = False
        for c in psutil.net_connections(kind='inet'):
            if c.laddr and c.laddr.port == port and c.pid:
                try:
                    proc = psutil.Process(c.pid)
                    proc.terminate()
                    print(Fore.GREEN + f'[Aegis] Killed PID {c.pid} ({proc.name()}) on port {port}' + Style.RESET_ALL)
                    killed = True
                except Exception as e:
                    print(Fore.RED + f'[Aegis] Could not kill PID {c.pid}: {e}' + Style.RESET_ALL)
        if not killed:
            print(Fore.YELLOW + f'[Aegis] Nothing listening on port {port}.' + Style.RESET_ALL)
        return killed
    except ImportError:
        print(Fore.RED + '[Aegis] psutil not available.' + Style.RESET_ALL)
        return False


# ── Test Runner ───────────────────────────────────────────────────────────────

def detect_and_run_tests(directory: str = '.') -> Optional[str]:
    base = Path(directory)
    if (base / 'pytest.ini').exists() or (base / 'setup.cfg').exists() or list(base.glob('test_*.py')) or list(base.glob('*_test.py')):
        return 'pytest'
    if (base / 'package.json').exists():
        try:
            pkg = json.loads((base / 'package.json').read_text())
            if 'test' in pkg.get('scripts', {}):
                return 'npm test'
        except Exception:
            return 'npm test'
    if (base / 'go.mod').exists():
        return 'go test ./...'
    if (base / 'pom.xml').exists():
        return 'mvn test'
    if (base / 'build.gradle').exists() or (base / 'build.gradle.kts').exists():
        return 'gradle test'
    if (base / 'Cargo.toml').exists():
        return 'cargo test'
    if list(base.glob('*.csproj')) or list(base.glob('*.sln')):
        return 'dotnet test'
    return None


# ── Project Templates ─────────────────────────────────────────────────────────

TEMPLATES = {
    'flask-app': {
        'desc': 'Flask web application',
        'files': {
            'app.py': (
                'from flask import Flask\n\napp = Flask(__name__)\n\n\n'
                '@app.route("/")\ndef index():\n    return "Hello from Aegis Flask!"\n\n\n'
                'if __name__ == "__main__":\n    app.run(debug=True)\n'
            ),
            'requirements.txt': 'flask>=3.0.0\n',
            '.env': 'FLASK_ENV=development\nFLASK_DEBUG=1\n',
        },
        'cmds': ['pip install flask'],
    },
    'fastapi-app': {
        'desc': 'FastAPI REST API',
        'files': {
            'main.py': (
                'from fastapi import FastAPI\n\napp = FastAPI()\n\n\n'
                '@app.get("/")\ndef root():\n    return {"message": "Hello from Aegis FastAPI!"}\n'
            ),
            'requirements.txt': 'fastapi>=0.110.0\nuvicorn>=0.27.0\n',
        },
        'cmds': ['pip install fastapi uvicorn'],
    },
    'react-app': {
        'desc': 'React frontend (via Vite)',
        'files': {},
        'cmds': ['npm create vite@latest {name} -- --template react', 'cd {name}', 'npm install'],
    },
    'node-api': {
        'desc': 'Node.js Express API',
        'files': {
            'index.js': (
                'const express = require("express");\nconst app = express();\n'
                'app.use(express.json());\n\napp.get("/", (req, res) => '
                'res.json({ message: "Hello from Aegis Node API!" }));\n\n'
                'app.listen(3000, () => console.log("Server on http://localhost:3000"));\n'
            ),
            'package.json': '{\n  "name": "{name}",\n  "main": "index.js",\n  "dependencies": {"express": "^4.18.0"}\n}\n',
        },
        'cmds': ['npm install'],
    },
    'python-cli': {
        'desc': 'Python CLI tool with argparse',
        'files': {
            'main.py': (
                'import argparse\n\ndef main():\n    parser = argparse.ArgumentParser(description="{name}")\n'
                '    parser.add_argument("--verbose", action="store_true")\n'
                '    args = parser.parse_args()\n    print("Running {name}...")\n\n'
                'if __name__ == "__main__":\n    main()\n'
            ),
            'requirements.txt': '',
        },
        'cmds': [],
    },
}


def create_project(template: str, name: str) -> bool:
    if template not in TEMPLATES:
        print(Fore.RED + f'[Aegis] Unknown template: {template}' + Style.RESET_ALL)
        print(Fore.CYAN + f'[Aegis] Available: {", ".join(TEMPLATES)}' + Style.RESET_ALL)
        return False

    t = TEMPLATES[template]
    base = Path(name)
    if base.exists():
        print(Fore.RED + f'[Aegis] Directory "{name}" already exists.' + Style.RESET_ALL)
        return False

    base.mkdir(parents=True)
    print(Fore.CYAN + f'[Aegis] Creating {t["desc"]} in ./{name}/' + Style.RESET_ALL)

    for fname, content in t['files'].items():
        (base / fname).write_text(content.replace('{name}', name), encoding='utf-8')
        print(Fore.GREEN + f'  + {fname}' + Style.RESET_ALL)

    for cmd in t['cmds']:
        real_cmd = cmd.replace('{name}', name)
        if not real_cmd.startswith('cd '):
            print(Fore.YELLOW + f'  $ {real_cmd}' + Style.RESET_ALL)
            subprocess.run(real_cmd, shell=True, cwd=str(base) if not real_cmd.startswith('npm create') else '.')

    print(Fore.GREEN + f'\n[Aegis] Project "{name}" created! cd {name} to get started.' + Style.RESET_ALL)
    return True


# ── SSH Profile Manager ───────────────────────────────────────────────────────

_SSH_FILE = Path.home() / '.aegis' / 'ssh_profiles.json'


def _load_ssh() -> Dict:
    if _SSH_FILE.exists():
        try:
            return json.loads(_SSH_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_ssh(profiles: Dict):
    _SSH_FILE.parent.mkdir(parents=True, exist_ok=True)
    _SSH_FILE.write_text(json.dumps(profiles, indent=2))


def ssh_add(name: str, host: str, user: str = '', port: int = 22, key: str = ''):
    profiles = _load_ssh()
    profiles[name] = {'host': host, 'user': user, 'port': port, 'key': key}
    _save_ssh(profiles)
    print(Fore.GREEN + f'[Aegis] SSH profile "{name}" saved.' + Style.RESET_ALL)


def ssh_connect(name: str) -> Optional[str]:
    profiles = _load_ssh()
    if name not in profiles:
        print(Fore.RED + f'[Aegis] No SSH profile "{name}".' + Style.RESET_ALL)
        return None
    p = profiles[name]
    parts = ['ssh']
    if p.get('key'):
        parts += ['-i', p['key']]
    if p.get('port', 22) != 22:
        parts += ['-p', str(p['port'])]
    target = f'{p["user"]}@{p["host"]}' if p.get('user') else p['host']
    parts.append(target)
    return ' '.join(parts)


def ssh_list():
    profiles = _load_ssh()
    if not profiles:
        print(Fore.YELLOW + '[Aegis] No SSH profiles saved.' + Style.RESET_ALL)
        return
    print(Fore.CYAN + '[Aegis] SSH Profiles:' + Style.RESET_ALL)
    for name, p in profiles.items():
        target = f'{p.get("user","?")}@{p["host"]}:{p.get("port",22)}'
        print(f'  {Fore.GREEN}{name:<15}{Style.RESET_ALL} {target}')


