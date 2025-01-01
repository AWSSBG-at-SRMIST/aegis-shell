import sys
import json
import platform
import subprocess
from typing import Optional
from colorama import Fore, Style
import requests


# ── HTTP Client ───────────────────────────────────────────────────────────────

_HTTP_METHODS = {'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'}


def is_http_command(cmd: str) -> bool:
    parts = cmd.split()
    return len(parts) >= 2 and parts[0].upper() in _HTTP_METHODS and parts[1].startswith('http')


def run_http_command(cmd: str):
    parts = cmd.split()
    method = parts[0].upper()
    url    = parts[1]
    headers = {}
    body = None

    i = 2
    while i < len(parts):
        if parts[i].startswith('-H') and i + 1 < len(parts):
            k, _, v = parts[i + 1].partition(':')
            headers[k.strip()] = v.strip()
            i += 2
        elif parts[i] == '-d' and i + 1 < len(parts):
            body = parts[i + 1]
            i += 2
        else:
            i += 1

    try:
        r = requests.request(method, url, headers=headers, data=body, timeout=15)
        status_color = Fore.GREEN if r.status_code < 400 else Fore.RED
        print(status_color + f'HTTP {r.status_code} {r.reason}' + Style.RESET_ALL)
        for k, v in r.headers.items():
            if k.lower() in ('content-type', 'content-length', 'x-request-id'):
                print(Fore.CYAN + f'{k}: {v}' + Style.RESET_ALL)
        print()
        ct = r.headers.get('content-type', '')
        if 'json' in ct:
            try:
                print(json.dumps(r.json(), indent=2))
            except Exception:
                print(r.text)
        else:
            print(r.text[:2000])
    except Exception as e:
        print(Fore.RED + f'[Aegis] HTTP error: {e}' + Style.RESET_ALL)


# ── Clipboard ─────────────────────────────────────────────────────────────────

def copy_to_clipboard(text: str) -> bool:
    system = platform.system().lower()
    try:
        if system == 'windows':
            subprocess.run('clip', input=text.encode('utf-8'), check=True)
        elif system == 'darwin':
            subprocess.run('pbcopy', input=text.encode('utf-8'), check=True)
        else:
            subprocess.run(['xclip', '-selection', 'clipboard'],
                           input=text.encode('utf-8'), check=True)
        print(Fore.GREEN + '[Aegis] Copied to clipboard.' + Style.RESET_ALL)
        return True
    except Exception as e:
        print(Fore.RED + f'[Aegis] Clipboard error: {e}' + Style.RESET_ALL)
        return False


def paste_from_clipboard() -> Optional[str]:
    system = platform.system().lower()
    try:
        if system == 'windows':
            result = subprocess.check_output('powershell -command Get-Clipboard', shell=True, text=True)
        elif system == 'darwin':
            result = subprocess.check_output('pbpaste', text=True)
        else:
            result = subprocess.check_output(['xclip', '-selection', 'clipboard', '-o'], text=True)
        return result.strip()
    except Exception:
        return None


def expand_all_aliases(cmd: str) -> Optional[str]:
    return None
