import json
import os
import re
import shlex
from pathlib import Path
from cryptography.fernet import Fernet
from colorama import Fore, Style

_STORE_FILE = Path.home() / '.aegis' / 'credentials.json'
_KEY_FILE   = Path.home() / '.aegis' / '.key'
_SECRET_RE  = re.compile(r'\$SECRET:([A-Za-z_][A-Za-z0-9_]*)')


def _get_fernet() -> Fernet:
    if _KEY_FILE.exists():
        return Fernet(_KEY_FILE.read_bytes())
    key = Fernet.generate_key()
    _KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    _KEY_FILE.write_bytes(key)
    try:
        os.chmod(_KEY_FILE, 0o600)
    except Exception:
        pass  # Windows does not support chmod; key is protected by user-profile ACLs
    return Fernet(key)


def _load() -> dict:
    if _STORE_FILE.exists():
        try:
            return json.loads(_STORE_FILE.read_text())
        except Exception:
            pass
    return {}


def _save(data: dict):
    _STORE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _STORE_FILE.write_text(json.dumps(data))


def secret_set(name: str, value: str):
    f = _get_fernet()
    data = _load()
    data[name] = f.encrypt(value.encode()).decode()
    _save(data)
    print(Fore.GREEN + f'[Aegis] Secret "{name}" stored.' + Style.RESET_ALL)


def secret_get(name: str) -> str:
    f = _get_fernet()
    data = _load()
    if name not in data:
        return ''
    try:
        return f.decrypt(data[name].encode()).decode()
    except Exception:
        return ''


def secret_delete(name: str):
    data = _load()
    if name in data:
        del data[name]
        _save(data)
        print(Fore.GREEN + f'[Aegis] Secret "{name}" deleted.' + Style.RESET_ALL)
    else:
        print(Fore.YELLOW + f'[Aegis] No secret "{name}".' + Style.RESET_ALL)


def secret_list():
    data = _load()
    if not data:
        print(Fore.YELLOW + '[Aegis] No secrets stored.' + Style.RESET_ALL)
        return
    print(Fore.CYAN + '[Aegis] Stored secrets:' + Style.RESET_ALL)
    for name in data:
        print(f'  {Fore.GREEN}{name}{Style.RESET_ALL}')


def expand_secrets(command: str) -> str:
    def _replace(m):
        name = m.group(1)
        val = secret_get(name)
        if not val:
            print(Fore.YELLOW + f'[Aegis] Warning: $SECRET:{name} not found.' + Style.RESET_ALL)
            return m.group(0)
        # Shell-quote so metacharacters and spaces in the secret value cannot inject commands
        return shlex.quote(val)
    return _SECRET_RE.sub(_replace, command)
