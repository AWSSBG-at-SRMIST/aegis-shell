from typing import Callable, Dict, List

# Hook names: 'before_command', 'after_command', 'on_error', 'on_cd', 'on_startup', 'on_exit'

_hooks: Dict[str, List[Callable]] = {}


def register(event: str, fn: Callable):
    _hooks.setdefault(event, []).append(fn)


def fire(event: str, **kwargs):
    for fn in _hooks.get(event, []):
        try:
            fn(**kwargs)
        except Exception:
            pass


def clear(event: str = None):
    if event:
        _hooks.pop(event, None)
    else:
        _hooks.clear()
