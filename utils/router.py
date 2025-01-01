import re
import shutil
import platform

# PowerShell cmdlet pattern: Verb-Noun (e.g. Get-Process, Set-Item, New-Item)
_PS_CMDLET = re.compile(r'^[A-Z][a-z]+-[A-Z][a-zA-Z]+')

# PowerShell-specific keywords that appear mid-command
_PS_KEYWORDS = {
    'Select-Object', 'Where-Object', 'ForEach-Object', 'Out-File',
    'Out-Null', 'Out-String', 'Write-Host', 'Write-Output', 'Write-Error',
    'Invoke-Expression', 'Invoke-Command', 'Import-Module', 'Export-Csv',
    'ConvertTo-Json', 'ConvertFrom-Json', 'Start-Process', 'Stop-Process',
    'Get-Content', 'Set-Content', 'Add-Content', 'Clear-Content',
    'Test-Path', 'Split-Path', 'Join-Path', 'Resolve-Path',
}

# Commands that are CMD built-ins (not executables — they only exist inside cmd.exe)
_CMD_BUILTINS = {
    'dir', 'cls', 'md', 'rd', 'del', 'copy', 'move', 'ren', 'rename',
    'type', 'tree', 'fc', 'comp', 'color', 'prompt', 'title', 'mode',
    'assoc', 'ftype', 'call', 'goto', 'pause', 'rem', 'setlocal',
    'endlocal', 'pushd', 'popd', 'verify', 'vol', 'label',
    'echo', 'set', 'path', 'ver', 'date', 'time', 'if', 'for',
}

# Unix commands and their nearest Windows CMD equivalents
_UNIX_TO_CMD = {
    'ls':    'dir',
    'cat':   'type',
    'rm':    'del',
    'cp':    'copy',
    'mv':    'move',
    'mkdir': 'md',
    'rmdir': 'rd /s /q',
    'clear': 'cls',
    'pwd':   'cd',
    'touch': 'type nul >',
    'which': 'where',
    'man':   'help',
    'grep':  'findstr',
    'head':  'more',
    'diff':  'fc',
    'open':  'start',
    'kill':  'taskkill /PID',
}

# Script extensions → interpreter
_SCRIPT_INTERPRETERS = {
    '.py':  ['python'],
    '.js':  ['node'],
    '.ts':  ['npx', 'ts-node'],
    '.sh':  ['bash', '-c'],
    '.ps1': ['powershell', '-File'],
    '.bat': ['cmd', '/c'],
    '.cmd': ['cmd', '/c'],
    '.rb':  ['ruby'],
    '.php': ['php'],
}

# Package managers — run directly as subprocess, no shell wrapper needed
_PACKAGE_MANAGERS = {
    'pip', 'pip3', 'npm', 'yarn', 'npx', 'pnpm',
    'winget', 'choco', 'scoop',
    'apt', 'apt-get', 'brew',
    'gem', 'cargo', 'go', 'composer', 'nuget', 'dotnet',
}


def detect_dialect(command: str) -> str:
    """
    Returns one of: 'powershell', 'cmd', 'unix_on_windows', 'direct', 'script', 'unknown'
    """
    stripped = command.strip()
    if not stripped:
        return 'unknown'

    parts = stripped.split()
    base = parts[0]
    base_lower = base.lower()

    # .ps1 / .bat / .cmd / .py etc. — script file
    for ext in _SCRIPT_INTERPRETERS:
        if base_lower.endswith(ext):
            return 'script'

    # PowerShell: Verb-Noun cmdlet
    if _PS_CMDLET.match(base):
        return 'powershell'

    # PowerShell: variable ($var) or pipeline with PS-specific commands
    if base.startswith('$') or any(kw in stripped for kw in _PS_KEYWORDS):
        return 'powershell'

    # Package manager — run directly
    if base_lower in _PACKAGE_MANAGERS:
        return 'direct'

    # CMD built-in
    if base_lower in _CMD_BUILTINS:
        return 'cmd'

    # Unix command on Windows
    if platform.system().lower() == 'windows' and base_lower in _UNIX_TO_CMD:
        return 'unix_on_windows'

    return 'unknown'


def build_subprocess_args(command: str, dialect: str) -> list:
    """
    Build the list of args to pass to subprocess for the given command + dialect.
    """
    parts = command.strip().split()
    base_lower = parts[0].lower()
    system = platform.system().lower()

    if dialect == 'powershell':
        return ['powershell', '-NoProfile', '-Command', command]

    if dialect == 'cmd':
        return ['cmd', '/c', command]

    if dialect == 'direct':
        # On Windows some tools ship as .cmd scripts (npm.cmd, npx.cmd, yarn.cmd, etc.)
        if system == 'windows':
            cmd_name = base_lower + '.cmd'
            if shutil.which(cmd_name):
                return [cmd_name] + parts[1:]
        return parts

    if dialect == 'script':
        for ext, interpreter in _SCRIPT_INTERPRETERS.items():
            if base_lower.endswith(ext):
                return interpreter + parts
        return parts

    if dialect == 'unix_on_windows' and system == 'windows':
        translated_base = _UNIX_TO_CMD[base_lower]
        rest = ' '.join(parts[1:])
        translated = f"{translated_base} {rest}".strip()
        return ['cmd', '/c', translated]

    # Unknown: on Windows default to PowerShell (superset of CMD for most things).
    # Exception: commands that use && are CMD-style chaining — PS 5.x doesn't support &&.
    if system == 'windows':
        if '&&' in command:
            return ['cmd', '/c', command]
        return ['powershell', '-NoProfile', '-Command', command]

    # On Unix default to bash
    return ['bash', '-c', command]


def is_available(command: str) -> bool:
    """Check if the base command binary exists on PATH."""
    base = command.strip().split()[0]
    return shutil.which(base) is not None


def get_base(command: str) -> str:
    return command.strip().split()[0].lower()
