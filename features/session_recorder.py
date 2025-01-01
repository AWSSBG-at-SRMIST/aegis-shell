import time
from pathlib import Path
from colorama import Fore, Style


class SessionRecorder:
    def __init__(self):
        self._recording = False
        self._file = None
        self._path = None

    def start(self, filename: str = None) -> str:
        if self._recording:
            return 'Already recording.'
        ts = time.strftime('%Y%m%d_%H%M%S')
        name = filename or f'session_{ts}.log'
        self._path = Path.home() / '.aegis' / 'recordings' / name
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._file = open(self._path, 'w', encoding='utf-8')
        self._file.write(f'# Aegis Session Recording — {time.strftime("%Y-%m-%d %H:%M:%S")}\n\n')
        self._recording = True
        return str(self._path)

    def record_input(self, user_input: str):
        if self._recording and self._file:
            ts = time.strftime('%H:%M:%S')
            self._file.write(f'[{ts}] $ {user_input}\n')
            self._file.flush()

    def record_output(self, output: str):
        if self._recording and self._file and output.strip():
            self._file.write(output + '\n')
            self._file.flush()

    def stop(self) -> str:
        if not self._recording:
            return 'Not recording.'
        self._file.write(f'\n# Recording ended — {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
        self._file.close()
        self._recording = False
        path = str(self._path)
        self._file = None
        self._path = None
        return path

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def current_file(self) -> str:
        return str(self._path) if self._path else ''

    def list_recordings(self):
        rec_dir = Path.home() / '.aegis' / 'recordings'
        if not rec_dir.exists():
            print(Fore.YELLOW + '[Aegis] No recordings yet.' + Style.RESET_ALL)
            return
        files = sorted(rec_dir.glob('*.log'), reverse=True)
        if not files:
            print(Fore.YELLOW + '[Aegis] No recordings yet.' + Style.RESET_ALL)
            return
        print(Fore.CYAN + '[Aegis] Saved recordings:' + Style.RESET_ALL)
        for f in files[:20]:
            size = f.stat().st_size
            print(f'  {f.name}  ({size} bytes)')
