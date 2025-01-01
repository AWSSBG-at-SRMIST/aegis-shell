import atexit
import json
import time
from collections import Counter
from pathlib import Path
from colorama import Fore, Style

_STATS_FILE = Path.home() / '.aegis' / 'analytics.json'
_STATS_FILE.parent.mkdir(parents=True, exist_ok=True)

_pending: list = []


def _load() -> dict:
    data: dict = {'commands': []}
    if _STATS_FILE.exists():
        try:
            data = json.loads(_STATS_FILE.read_text())
        except Exception:
            pass
    # Merge in-memory entries not yet flushed to disk
    if _pending:
        data['commands'] = list(data.get('commands', [])) + list(_pending)
    return data


def _save(data: dict):
    _STATS_FILE.write_text(json.dumps(data))


def _flush():
    global _pending
    if not _pending:
        return
    data = _load()
    data.setdefault('commands', []).extend(_pending)
    data['commands'] = data['commands'][-5000:]
    _save(data)
    _pending = []


atexit.register(_flush)


def record(command: str, success: bool, duration: float):
    _pending.append({
        'cmd':  command.split()[0] if command.split() else command,
        'full': command,
        'ok':   success,
        'dur':  round(duration, 3),
        'hour': time.localtime().tm_hour,
    })
    if len(_pending) >= 10:
        _flush()


def _bar(value: int, max_val: int, width: int = 20) -> str:
    filled = int((value / max_val) * width) if max_val else 0
    return Fore.GREEN + '█' * filled + Fore.WHITE + '░' * (width - filled) + Style.RESET_ALL


def show_analytics():
    _flush()
    data = _load()
    cmds = data.get('commands', [])
    if not cmds:
        print(Fore.YELLOW + '[Aegis] No analytics data yet.' + Style.RESET_ALL)
        return

    total   = len(cmds)
    success = sum(1 for c in cmds if c['ok'])
    fail    = total - success
    rate    = (success / total * 100) if total else 0
    avg_dur = sum(c.get('dur', 0) for c in cmds) / total if total else 0

    print(Fore.CYAN + '\n[Aegis] Command Analytics' + Style.RESET_ALL)
    print('─' * 44)
    print(f'  Total commands  : {total}')
    print(f'  Success         : {Fore.GREEN}{success}{Style.RESET_ALL}')
    print(f'  Failed          : {Fore.RED}{fail}{Style.RESET_ALL}')
    print(f'  Success rate    : {rate:.1f}%')
    print(f'  Avg duration    : {avg_dur:.2f}s')

    counter = Counter(c['cmd'] for c in cmds)
    top = counter.most_common(8)
    if top:
        max_count = top[0][1]
        print(f'\n  {Fore.CYAN}Most used commands:{Style.RESET_ALL}')
        for cmd, count in top:
            print(f'  {cmd:<15} {_bar(count, max_count)} {count}')

    fails = Counter(c['cmd'] for c in cmds if not c['ok'])
    top_fails = fails.most_common(5)
    if top_fails:
        print(f'\n  {Fore.RED}Most failed:{Style.RESET_ALL}')
        for cmd, count in top_fails:
            print(f'  {cmd:<15} {Fore.RED}{count}{Style.RESET_ALL}')

    hour_counts = Counter(c['hour'] for c in cmds)
    if hour_counts:
        max_h = max(hour_counts.values())
        print(f'\n  {Fore.CYAN}Activity by hour:{Style.RESET_ALL}')
        for h in range(24):
            count = hour_counts.get(h, 0)
            if count:
                bar = _bar(count, max_h, width=12)
                print(f'  {h:02d}:00  {bar} {count}')
    print()
