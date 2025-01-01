import time
import platform
import shutil
from colorama import Fore, Style

try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False


def _bar(pct: float, width: int = 20) -> str:
    filled = int(pct / 100 * width)
    color = Fore.GREEN if pct < 60 else (Fore.YELLOW if pct < 85 else Fore.RED)
    return color + '█' * filled + Fore.WHITE + '░' * (width - filled) + Style.RESET_ALL


def _bytes(n: int) -> str:
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if n < 1024:
            return f'{n:.1f}{unit}'
        n /= 1024
    return f'{n:.1f}PB'


def show_dashboard(duration: int = 5, interval: float = 1.0):
    if not _PSUTIL:
        print(Fore.RED + '[Aegis] psutil not available.' + Style.RESET_ALL)
        return

    import os
    is_windows = platform.system().lower() == 'windows'

    try:
        for tick in range(int(duration / interval)):
            os.system('cls' if is_windows else 'clear')

            cpu   = psutil.cpu_percent(interval=None)
            mem   = psutil.virtual_memory()
            disk  = psutil.disk_usage('/')
            try:
                net   = psutil.net_io_counters()
                net_s = f'↑{_bytes(net.bytes_sent)}  ↓{_bytes(net.bytes_recv)}'
            except Exception:
                net_s = 'N/A'

            term_w = shutil.get_terminal_size((80, 24)).columns
            title  = ' AEGIS SYSTEM DASHBOARD '
            pad    = (term_w - len(title)) // 2
            print(Fore.CYAN + '─' * pad + title + '─' * pad + Style.RESET_ALL)
            print()

            print(f'  CPU      {_bar(cpu)}  {cpu:5.1f}%')
            print(f'  RAM      {_bar(mem.percent)}  {mem.percent:5.1f}%  '
                  f'({_bytes(mem.used)} / {_bytes(mem.total)})')
            print(f'  Disk     {_bar(disk.percent)}  {disk.percent:5.1f}%  '
                  f'({_bytes(disk.used)} / {_bytes(disk.total)})')
            print(f'  Network  {net_s}')
            print()

            # Top 8 processes by CPU
            procs = sorted(
                [p.info for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent'])
                 if p.info['cpu_percent'] is not None],
                key=lambda x: x['cpu_percent'], reverse=True
            )[:8]

            print(Fore.CYAN + f'  {"PID":<8} {"NAME":<22} {"CPU%":>6} {"MEM%":>6}' + Style.RESET_ALL)
            print('  ' + '─' * 46)
            for p in procs:
                cpu_c = Fore.RED if p['cpu_percent'] > 50 else Fore.GREEN
                print(f'  {p["pid"]:<8} {(p["name"] or "?")[:22]:<22} '
                      f'{cpu_c}{p["cpu_percent"]:>6.1f}{Style.RESET_ALL} '
                      f'{p["memory_percent"]:>6.1f}')

            uptime_s = time.time() - psutil.boot_time()
            h, rem = divmod(int(uptime_s), 3600)
            m, s   = divmod(rem, 60)
            print()
            print(Fore.WHITE + f'  Uptime: {h}h {m}m {s}s   '
                  f'CPU cores: {psutil.cpu_count()}   '
                  f'Refresh: {interval}s   Press Ctrl+C to exit' + Style.RESET_ALL)

            time.sleep(interval)

    except KeyboardInterrupt:
        pass

    os.system('cls' if is_windows else 'clear')
    print(Fore.CYAN + '[Aegis] Dashboard closed.' + Style.RESET_ALL)
