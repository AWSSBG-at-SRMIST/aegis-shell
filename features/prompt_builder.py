import subprocess
import os
import time
import platform
from pathlib import Path


def _git_branch() -> str:
    try:
        branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stderr=subprocess.DEVNULL, text=True
        ).strip()
        dirty = subprocess.call(
            ['git', 'diff', '--quiet'],
            stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL
        )
        return f'\033[35m({branch}{"*" if dirty else ""})\033[0m '
    except Exception:
        return ''


def _active_venv() -> str:
    venv = os.environ.get('VIRTUAL_ENV')
    if venv:
        name = Path(venv).name
        return f'\033[33m[{name}]\033[0m '
    return ''


def _cwd_short() -> str:
    try:
        cwd = Path.cwd()
        home = Path.home()
        if cwd == home:
            return '~'
        try:
            rel = cwd.relative_to(home)
            return '~/' + str(rel).replace('\\', '/')
        except ValueError:
            return str(cwd).replace('\\', '/')
    except Exception:
        return '?'


def build_prompt(last_exit: int = 0, theme_prompt_color: str = '\033[32m') -> str:
    git   = _git_branch()
    venv  = _active_venv()
    cwd   = _cwd_short()
    ts    = time.strftime('%H:%M:%S')
    ec    = f'\033[31m✗\033[0m ' if last_exit != 0 else ''

    return (
        f'\033[90m[{ts}]\033[0m '    # dim gray timestamp
        f'{venv}'                      # virtualenv if active
        f'\033[36m{cwd}\033[0m '      # cyan cwd
        f'{git}'                       # git branch if in repo
        f'{ec}'                        # red ✗ on last failure
        f'{theme_prompt_color}aegis>\033[0m '
    )
