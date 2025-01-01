import subprocess
import platform
import threading
from typing import Tuple
from colorama import Fore, Style

from utils.router import detect_dialect, build_subprocess_args, is_available, get_base
from utils.security_manager import SecurityManager
from utils.installers import install_package
from llm.llm_handler import handle_unknown_command


class CommandExecutor:
    def __init__(self):
        self.security_manager = SecurityManager()
        self.command_history = []
        self.success_count = 0
        self.total_count = 0

    def execute_command(self, command: str) -> Tuple[bool, str]:
        if not command.strip():
            return True, ""

        self.command_history.append(command)
        self.total_count += 1

        is_safe, reason = self.security_manager.validate_command(command)
        if not is_safe:
            return False, f"[Aegis] Blocked: {reason}"

        dialect = detect_dialect(command)
        base = get_base(command)

        # For dialects that are shell built-ins or PS cmdlets, no binary check needed
        needs_binary_check = dialect in ('direct', 'script', 'unknown')

        if needs_binary_check and not is_available(base):
            installed = self._auto_install(base)
            if not installed:
                return False, f"'{base}' not found and could not be installed."

        return self._run(command, dialect)

    def _run(self, command: str, dialect: str) -> Tuple[bool, str]:
        """Run the command, streaming stdout in real time. Ctrl+C or Escape stops it."""
        args = build_subprocess_args(command, dialect)

        try:
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
        except FileNotFoundError as e:
            return False, f"Executor not found: {e}"
        except Exception as e:
            return False, str(e)

        stop = threading.Event()
        stderr_lines: list = []

        def _stream_stdout():
            for line in process.stdout:
                print(line, end='', flush=True)

        def _stream_stderr():
            for line in process.stderr:
                stderr_lines.append(line)
                print(Fore.RED + line + Style.RESET_ALL, end='', flush=True)

        def _escape_watcher():
            """Watch for Escape keypress alongside a running subprocess."""
            try:
                if platform.system() == 'Windows':
                    import msvcrt
                    # Drain bytes left in the console buffer by prompt_toolkit's
                    # VT rendering (cursor moves etc. include \x1b) so we only
                    # react to keys the user presses AFTER the command started.
                    while msvcrt.kbhit():
                        msvcrt.getwch()
                    while not stop.is_set():
                        if msvcrt.kbhit():
                            ch = msvcrt.getwch()
                            if ch == '\x1b':
                                stop.set()
                                return
                        stop.wait(0.05)
                else:
                    import select
                    import sys
                    import tty
                    import termios
                    fd = sys.stdin.fileno()
                    old = termios.tcgetattr(fd)
                    try:
                        tty.setraw(fd)
                        while not stop.is_set():
                            r, _, _ = select.select([sys.stdin], [], [], 0.05)
                            if r:
                                ch = sys.stdin.read(1)
                                if ch == '\x1b':
                                    stop.set()
                                    return
                    finally:
                        termios.tcsetattr(fd, termios.TCSADRAIN, old)
            except Exception:
                pass

        reader  = threading.Thread(target=_stream_stdout, daemon=True)
        err_reader = threading.Thread(target=_stream_stderr, daemon=True)
        watcher = threading.Thread(target=_escape_watcher, daemon=True)
        reader.start()
        err_reader.start()
        watcher.start()

        # Poll reader.join with a short timeout so the main thread stays
        # interruptible by Ctrl+C (blocking C-level reads don't check signals).
        interrupted = False
        try:
            while reader.is_alive():
                if stop.is_set():
                    interrupted = True
                    break
                reader.join(timeout=0.1)
        except KeyboardInterrupt:
            interrupted = True
        finally:
            stop.set()  # always release watcher

        if interrupted and process.poll() is None:
            print()
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            print(Fore.YELLOW + '[Aegis] Stopped.' + Style.RESET_ALL)
            return False, ''

        process.wait()
        err_reader.join()
        stderr_out = ''.join(stderr_lines)

        if process.returncode == 0:
            self.success_count += 1
            return True, ''

        not_found_hints = (
            'is not recognized', 'not found', 'cannot find',
            'no such file', 'command not found'
        )
        # Only auto-install when the binary itself could be missing (direct/unknown dialects).
        # For cmd/powershell/unix_on_windows the wrapper always exists — a "not found" in stderr
        # means a bad flag or missing sub-tool, not a missing binary.
        if dialect in ('direct', 'unknown') and any(h in stderr_out.lower() for h in not_found_hints):
            base = get_base(command)
            if not is_available(base):
                installed = self._auto_install(base)
                if installed:
                    return self._run(command, dialect)

        # stderr already printed live by _stream_stderr thread
        return False, stderr_out

    def _auto_install(self, base_command: str) -> bool:
        """Ask LLM for the install command, confirm with user, then install."""
        explanation, install_cmd = handle_unknown_command(base_command)

        if not install_cmd:
            return False

        if explanation:
            print(Fore.CYAN + f"[Aegis] {explanation}" + Style.RESET_ALL)
        print(Fore.CYAN + f"[Aegis] Suggested install: {install_cmd}" + Style.RESET_ALL)

        confirm = input(Fore.YELLOW + "[Aegis] Install now? (y/n): " + Style.RESET_ALL).strip().lower()
        if confirm != 'y':
            return False

        parts = install_cmd.split()
        if len(parts) >= 2:
            installer = parts[0]
            # Skip trailing flags (e.g. --silent, -g) to find the actual package name
            package = next((p for p in reversed(parts[1:]) if not p.startswith('-')), None)
            if package:
                return install_package(package, installer)

        return False

    def get_success_rate(self) -> float:
        if self.total_count == 0:
            return 0.0
        return (self.success_count / self.total_count) * 100
