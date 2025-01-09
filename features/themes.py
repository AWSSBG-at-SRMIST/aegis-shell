import json
from pathlib import Path
from colorama import Fore, Back, Style

THEMES = {
    'default': {
        'prompt':    '\033[32m',   # green
        'info':      '\033[36m',   # cyan
        'success':   '\033[32m',   # green
        'warning':   '\033[33m',   # yellow
        'error':     '\033[31m',   # red
        'muted':     '\033[90m',   # dark gray
        'highlight': '\033[96m',   # bright cyan
        'reset':     '\033[0m',
    },
    'dark': {
        'prompt':    '\033[94m',   # bright blue
        'info':      '\033[96m',   # bright cyan
        'success':   '\033[92m',   # bright green
        'warning':   '\033[93m',   # bright yellow
        'error':     '\033[91m',   # bright red
        'muted':     '\033[90m',
        'highlight': '\033[95m',   # bright magenta
        'reset':     '\033[0m',
    },
    'light': {
        'prompt':    '\033[34m',   # blue
        'info':      '\033[35m',   # magenta
        'success':   '\033[32m',
        'warning':   '\033[33m',
        'error':     '\033[31m',
        'muted':     '\033[37m',   # white
        'highlight': '\033[34m',
        'reset':     '\033[0m',
    },
    'hacker': {
        'prompt':    '\033[92m',   # bright green
        'info':      '\033[92m',
        'success':   '\033[92m',
        'warning':   '\033[93m',
        'error':     '\033[91m',
        'muted':     '\033[32m',   # dim green
        'highlight': '\033[97m',   # white
        'reset':     '\033[0m',
    },
    'minimal': {
        'prompt':    '\033[0m',    # no color
        'info':      '\033[0m',
        'success':   '\033[0m',
        'warning':   '\033[0m',
        'error':     '\033[0m',
        'muted':     '\033[0m',
        'highlight': '\033[0m',
        'reset':     '\033[0m',
    },
}

_CONFIG_FILE = Path.home() / '.aegis' / 'theme.json'
_active = 'default'


def load_theme():
    global _active
    if _CONFIG_FILE.exists():
        try:
            data = json.loads(_CONFIG_FILE.read_text())
            name = data.get('theme', 'default')
            if name in THEMES:
                _active = name
        except Exception:
            pass


def save_theme(name: str):
    _CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    _CONFIG_FILE.write_text(json.dumps({'theme': name}))


def set_theme(name: str) -> bool:
    global _active
    if name not in THEMES:
        return False
    _active = name
    save_theme(name)
    return True


def c(key: str) -> str:
    return THEMES.get(_active, THEMES['default']).get(key, '\033[0m')


def list_themes() -> list:
    return list(THEMES.keys())


def current_theme() -> str:
    return _active
