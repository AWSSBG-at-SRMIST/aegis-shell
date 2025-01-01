"""
Aegis Shell — offline installer
Run directly:  python installer.py
"""
import os
import sys
import json
import shutil
import platform
import subprocess
from pathlib import Path

try:
    from colorama import init, Fore, Style
    init()
    _HAS_COLOR = True
except ImportError:
    _HAS_COLOR = False
    class _Noop:
        def __getattr__(self, _): return ''
    Fore = Style = _Noop()

# ── Helpers ───────────────────────────────────────────────────────────────────

def _c(code, text):
    return f"{code}{text}{Style.RESET_ALL}" if _HAS_COLOR else text

def banner():
    print()
    print(_c(Fore.CYAN, "  ╔════════════════════════════════════════════════╗"))
    print(_c(Fore.CYAN, "  ║                                                ║"))
    print("  " + _c(Fore.CYAN, "║   ") + _c(Fore.WHITE, "⚔   A E G I S   S H E L L   ⚔") + _c(Fore.CYAN, "            ║"))
    print(_c(Fore.CYAN, "  ║                                                ║"))
    print(_c(Fore.CYAN, "  ║   AI-powered terminal. Run anything.           ║"))
    print(_c(Fore.CYAN, "  ║   Tanish · Nidhi · Nishant  ·  SRMIST         ║"))
    print(_c(Fore.CYAN, "  ║                                                ║"))
    print(_c(Fore.CYAN, "  ╚════════════════════════════════════════════════╝"))
    print()

TOTAL = 4
_step = 0

def step(msg):
    global _step
    _step += 1
    print(f"  {_c(Fore.CYAN, f'[{_step}/{TOTAL}]')}  {msg}")

def ok(msg):   print(f"  {_c(Fore.GREEN, '✓')}  {msg}")
def warn(msg): print(f"  {_c(Fore.YELLOW, '!')}  {msg}")
def fail(msg): print(f"  {_c(Fore.RED, '✗')}  {msg}")

def die(msg):
    fail(msg)
    print()
    sys.exit(1)

def hr():
    print(_c(Fore.CYAN, "  ────────────────────────────────────────────────"))

# ── Config ────────────────────────────────────────────────────────────────────

def _default_install_dir():
    return Path.home() / '.aegis-shell'

def _default_bin_dir():
    system = platform.system()
    if system == 'Windows':
        return Path.home() / '.local' / 'bin'
    for d in [Path('/usr/local/bin'), Path.home() / '.local' / 'bin', Path.home() / 'bin']:
        if os.access(d, os.W_OK) or not d.exists():
            return d
    return Path.home() / '.local' / 'bin'

# ── Steps ─────────────────────────────────────────────────────────────────────

def check_python():
    print(f"  {_c(Fore.WHITE, 'Checking requirements...')}")
    print()
    vi = sys.version_info
    if vi < (3, 9):
        die(f"Python {vi.major}.{vi.minor} found — 3.9+ required. https://python.org/downloads")
    ok(f"Python {vi.major}.{vi.minor}.{vi.micro}")


def install_deps(source_dir: Path):
    step("Installing dependencies...")
    req = source_dir / 'requirements.txt'
    if not req.exists():
        warn("requirements.txt not found — skipping")
        return
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '--quiet', '--upgrade', 'pip'],
        capture_output=True
    )
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '--quiet', '-r', str(req)],
        capture_output=True
    )
    if result.returncode != 0:
        die("Dependency install failed:\n" + result.stderr.decode())
    ok("Dependencies installed")


def copy_files(source_dir: Path, install_dir: Path):
    step("Copying files...")
    SKIP = {'installer.py', 'build_installer.py', 'build', 'dist',
            '__pycache__', '.git', 'release', '.DS_Store'}
    try:
        install_dir.mkdir(parents=True, exist_ok=True)
        for item in source_dir.iterdir():
            if item.name in SKIP or item.name.startswith('.'):
                continue
            dest = install_dir / item.name
            if item.is_file():
                shutil.copy2(item, dest)
            elif item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
        ok(f"Installed to {install_dir}")
    except Exception as e:
        die(f"Failed to copy files: {e}")


def create_launcher(install_dir: Path, bin_dir: Path):
    step("Creating launcher...")
    try:
        bin_dir.mkdir(parents=True, exist_ok=True)
        system = platform.system()

        if system == 'Windows':
            launcher = bin_dir / 'aegis.bat'
            script   = install_dir / 'aegis_shell.py'
            launcher.write_text(
                f'@echo off\n"{sys.executable}" "{script}" %*\n',
                encoding='ascii'
            )
        else:
            launcher = bin_dir / 'aegis'
            script   = install_dir / 'aegis_shell.py'
            launcher.write_text(
                f'#!/usr/bin/env bash\nexec "{sys.executable}" "{script}" "$@"\n'
            )
            os.chmod(launcher, 0o755)

        ok(f"Launcher → {launcher}")
        _ensure_on_path(bin_dir, system)
    except Exception as e:
        die(f"Failed to create launcher: {e}")


def _ensure_on_path(bin_dir: Path, system: str):
    bin_str = str(bin_dir)

    if system == 'Windows':
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment',
                                0, winreg.KEY_ALL_ACCESS) as key:
                current, _ = winreg.QueryValueEx(key, 'Path')
                if bin_str not in current:
                    winreg.SetValueEx(key, 'Path', 0, winreg.REG_EXPAND_SZ,
                                      f"{bin_str};{current}")
                    ok(f"Added {bin_dir} to user PATH")
        except Exception:
            warn(f"Could not update PATH — add {bin_dir} manually")
    else:
        for rc in [Path.home() / f for f in ('.zshrc', '.bashrc', '.bash_profile', '.profile')]:
            if rc.exists():
                content = rc.read_text()
                if bin_str not in content:
                    rc.write_text(content + f'\nexport PATH="{bin_str}:$PATH"\n')
                    ok(f"Added {bin_dir} to PATH in {rc.name}")
                break


def verify(install_dir: Path):
    step("Verifying install...")
    try:
        result = subprocess.run(
            [sys.executable, '-c',
             f"import sys; sys.path.insert(0, {str(install_dir)!r}); import aegis_shell"],
            capture_output=True, timeout=10
        )
        if result.returncode == 0:
            ok("Aegis Shell is working")
        else:
            warn("Verification inconclusive — run 'aegis' in a new terminal to check")
    except Exception:
        warn("Verification inconclusive — run 'aegis' in a new terminal to check")


def print_done(bin_dir: Path):
    print()
    hr()
    print()
    print(f"  {_c(Fore.GREEN, '✓  Aegis Shell installed successfully!')}")
    print()
    if platform.system() == 'Windows':
        print("  Open a new terminal (or restart this one) and run:")
    else:
        print("  Open a new terminal and run:")
    print()
    print(f"      {_c(Fore.CYAN, 'aegis')}")
    print()
    hr()
    print(f"  Docs     {_c(Fore.CYAN, 'github.com/tanishpoddar/aegis-shell')}")
    print(f"  Issues   {_c(Fore.CYAN, 'github.com/tanishpoddar/aegis-shell/issues')}")
    print(f"  Update   {_c(Fore.CYAN, 'aegis update')}")
    hr()
    print()

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Ensure UTF-8 output on Windows (box-drawing characters)
    if platform.system() == 'Windows':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    source_dir  = Path(__file__).resolve().parent
    install_dir = _default_install_dir()
    bin_dir     = _default_bin_dir()

    banner()
    check_python()
    print()
    print(f"  {_c(Fore.WHITE, 'Installing Aegis Shell...')}")
    print()

    # If running from the source dir, copy → install_dir; otherwise install in-place
    if source_dir == install_dir:
        install_deps(install_dir)
        _step_dummy = 1  # copy step skipped
        create_launcher(install_dir, bin_dir)
        verify(install_dir)
    else:
        install_deps(source_dir)
        copy_files(source_dir, install_dir)
        create_launcher(install_dir, bin_dir)
        verify(install_dir)

    print_done(bin_dir)


if __name__ == '__main__':
    main()
