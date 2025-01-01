import os
import re
from typing import Dict
from colorama import Fore, Style

_vars: Dict[str, str] = {}
_SET_RE = re.compile(r'^\$([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$')


def is_assignment(command: str) -> bool:
    return bool(_SET_RE.match(command.strip()))


def handle_assignment(command: str) -> bool:
    m = _SET_RE.match(command.strip())
    if not m:
        return False
    name, value = m.group(1), m.group(2).strip().strip('"').strip("'")
    _vars[name] = value
    os.environ[name] = value
    print(Fore.CYAN + f'[Aegis] ${name} = {value}' + Style.RESET_ALL)
    return True


def expand(command: str) -> str:
    def _replace(match):
        name = match.group(1)
        return _vars.get(name, os.environ.get(name, match.group(0)))
    return re.sub(r'\$([A-Za-z_][A-Za-z0-9_]*)', _replace, command)


def list_vars():
    if not _vars:
        print(Fore.YELLOW + '[Aegis] No session variables set.' + Style.RESET_ALL)
        return
    print(Fore.CYAN + '[Aegis] Session variables:' + Style.RESET_ALL)
    for k, v in _vars.items():
        print(f'  ${k} = {v}')


def unset(name: str):
    name = name.lstrip('$')
    _vars.pop(name, None)
    os.environ.pop(name, None)
    print(Fore.CYAN + f'[Aegis] ${name} unset.' + Style.RESET_ALL)
