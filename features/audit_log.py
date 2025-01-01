import json
import time
from pathlib import Path


_LOG_FILE = Path.home() / '.aegis' / 'audit.log'
_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def log_command(command: str, success: bool, duration: float = 0.0):
    entry = {
        't': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'cmd': command,
        'ok': success,
        'dur': round(duration, 3),
    }
    with open(_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')


def read_log(limit: int = 50) -> list:
    if not _LOG_FILE.exists():
        return []
    lines = _LOG_FILE.read_text(encoding='utf-8').strip().splitlines()
    entries = []
    for line in lines[-limit:]:
        try:
            entries.append(json.loads(line))
        except Exception:
            pass
    return entries
