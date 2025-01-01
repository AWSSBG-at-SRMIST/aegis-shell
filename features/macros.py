import json
from pathlib import Path
from colorama import Fore, Style


_MACRO_FILE = Path.home() / '.aegis' / 'macros.json'


def _load() -> dict:
    if _MACRO_FILE.exists():
        try:
            return json.loads(_MACRO_FILE.read_text())
        except Exception:
            pass
    return {}


def _save(macros: dict):
    _MACRO_FILE.parent.mkdir(parents=True, exist_ok=True)
    _MACRO_FILE.write_text(json.dumps(macros, indent=2))


class MacroRecorder:
    def __init__(self):
        self._recording = False
        self._name = None
        self._steps = []

    def start(self, name: str):
        if self._recording:
            print(Fore.YELLOW + f'[Aegis] Already recording macro "{self._name}".' + Style.RESET_ALL)
            return
        self._name = name
        self._steps = []
        self._recording = True
        print(Fore.CYAN + f'[Aegis] Recording macro "{name}". Type commands. "macro stop" to finish.' + Style.RESET_ALL)

    def record(self, command: str):
        if self._recording:
            self._steps.append(command)

    def stop(self):
        if not self._recording:
            print(Fore.YELLOW + '[Aegis] Not recording.' + Style.RESET_ALL)
            return
        macros = _load()
        macros[self._name] = self._steps
        _save(macros)
        print(Fore.GREEN + f'[Aegis] Macro "{self._name}" saved ({len(self._steps)} steps).' + Style.RESET_ALL)
        self._recording = False
        self._name = None
        self._steps = []

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def current_name(self) -> str:
        return self._name or ''


def run_macro(name: str, executor) -> bool:
    macros = _load()
    if name not in macros:
        print(Fore.RED + f'[Aegis] No macro named "{name}".' + Style.RESET_ALL)
        return False
    steps = macros[name]
    print(Fore.CYAN + f'[Aegis] Running macro "{name}" ({len(steps)} steps)...' + Style.RESET_ALL)
    for i, cmd in enumerate(steps, 1):
        print(Fore.YELLOW + f'[{i}/{len(steps)}] {cmd}' + Style.RESET_ALL)
        executor.execute_command(cmd)
    return True


def list_macros():
    macros = _load()
    if not macros:
        print(Fore.YELLOW + '[Aegis] No macros saved.' + Style.RESET_ALL)
        return
    print(Fore.CYAN + '[Aegis] Saved macros:' + Style.RESET_ALL)
    for name, steps in macros.items():
        print(f'  {Fore.GREEN}{name:<20}{Style.RESET_ALL} ({len(steps)} steps)')


def delete_macro(name: str) -> bool:
    macros = _load()
    if name not in macros:
        print(Fore.RED + f'[Aegis] No macro "{name}".' + Style.RESET_ALL)
        return False
    del macros[name]
    _save(macros)
    print(Fore.GREEN + f'[Aegis] Macro "{name}" deleted.' + Style.RESET_ALL)
    return True
