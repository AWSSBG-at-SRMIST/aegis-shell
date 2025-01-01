import re
import subprocess
import platform
from typing import List, Optional, Tuple
from colorama import Fore, Style

from llm.llm_handler import _load_config, GROQ_API_URL
import requests

# Patterns that suggest sensitive data in a command
_SENSITIVE_PATTERNS = [
    (re.compile(r'(?i)(password|passwd|pwd)\s*[=:]\s*\S+'),   'password'),
    (re.compile(r'(?i)(api[_-]?key|apikey)\s*[=:]\s*\S+'),    'API key'),
    (re.compile(r'(?i)(secret[_-]?key?)\s*[=:]\s*\S+'),       'secret key'),
    (re.compile(r'(?i)(token)\s*[=:]\s*\S+'),                  'token'),
    (re.compile(r'(?i)(aws[_-]?access[_-]?key)\s*[=:]\s*\S+'),'AWS key'),
    (re.compile(r'(?i)(private[_-]?key)\s*[=:]\s*\S+'),       'private key'),
    (re.compile(r'gsk_[A-Za-z0-9]{20,}'),                      'Groq API key'),
    (re.compile(r'sk-[A-Za-z0-9]{20,}'),                       'OpenAI key'),
    (re.compile(r'ghp_[A-Za-z0-9]{20,}'),                      'GitHub token'),
    (re.compile(r'(?i)bearer\s+[A-Za-z0-9._\-]{10,}'),        'Bearer token'),
]


def _call_groq(system: str, user: str, max_tokens: int = 512) -> Optional[str]:
    api_key, model = _load_config()
    if not api_key:
        return None
    try:
        r = requests.post(
            GROQ_API_URL,
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={
                'model': model,
                'messages': [
                    {'role': 'system', 'content': system},
                    {'role': 'user',   'content': user},
                ],
                'max_tokens': max_tokens,
                'temperature': 0.3,
            },
            timeout=15,
        )
        if r.status_code == 200:
            return r.json()['choices'][0]['message']['content'].strip()
    except Exception:
        pass
    return None


# ── Command Explainer ─────────────────────────────────────────────────────────

def explain_command(command: str) -> Optional[str]:
    os_name = platform.system()
    return _call_groq(
        f"You are a shell expert on {os_name}. Explain the given shell command in plain English. "
        "Be concise: 2-4 sentences max. Break down each flag/argument. No markdown headers.",
        f"Explain this command: {command}",
        max_tokens=256,
    )


# ── Error Diagnosis ───────────────────────────────────────────────────────────

def _subcmds(command: str) -> List[str]:
    """Split a compound command (;  &&  ||) into individual sub-commands."""
    return [p.strip() for p in re.split(r';|&&|\|\|', command) if p.strip()]


def _gather_system_context(command: str, stderr: str) -> str:
    """Query the live system for context relevant to the failed command."""
    ctx: List[str] = []

    for sub in _subcmds(command):
        parts = sub.split()
        if not parts:
            continue
        base = parts[0].lower()

        # net start/stop/query <name> → look up real service names
        if base == 'net' and len(parts) >= 3 and parts[1].lower() in ('start', 'stop', 'query'):
            # Strip any trailing punctuation the compound-split may have left
            hint = re.sub(r'\W+$', '', parts[2])
            if not hint:
                continue
            try:
                r = subprocess.run(
                    ['powershell', '-NoProfile', '-Command',
                     f"Get-Service *{hint}* | Select-Object Name,DisplayName,Status | Format-Table -AutoSize"],
                    capture_output=True, text=True, timeout=5,
                )
                if r.stdout.strip():
                    ctx.append(f"Services matching '{hint}' on this system:\n{r.stdout.strip()}")
            except Exception:
                pass

        # pip/python failures → include version
        if base in ('pip', 'pip3', 'python', 'python3'):
            try:
                r = subprocess.run([base, '--version'], capture_output=True, text=True, timeout=5)
                if r.stdout.strip():
                    ctx.append(r.stdout.strip())
            except Exception:
                pass

    # Port already in use → show what owns it
    port_match = re.search(r'\b(\d{2,5})\b', stderr + ' ' + command)
    if port_match and any(w in (stderr + command).lower() for w in ('port', 'address already', 'bind')):
        port = port_match.group(1)
        try:
            r = subprocess.run(
                ['powershell', '-NoProfile', '-Command',
                 f"Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue"
                 " | Select-Object State,OwningProcess | Format-Table -AutoSize"],
                capture_output=True, text=True, timeout=5,
            )
            if r.stdout.strip():
                ctx.append(f"Port {port} usage:\n{r.stdout.strip()}")
        except Exception:
            pass

    return '\n'.join(ctx)


def diagnose_error(command: str, stderr: str, returncode: int) -> Optional[str]:
    os_name = platform.system()
    shell_hint = (
        " Write FIX commands for Windows PowerShell 5.1: use ';' not '&&' to chain commands."
        if os_name == 'Windows' else ""
    )

    sys_ctx = _gather_system_context(command, stderr)
    ctx_section = f"\nSystem context:\n{sys_ctx}" if sys_ctx else ""

    return _call_groq(
        f"You are a shell expert on {os_name}.{shell_hint} A command failed. Give a short diagnosis and "
        "the exact fix command(s) on the next line prefixed with FIX: — nothing else.",
        f"Command: {command}\nExit code: {returncode}\nError output:\n{stderr[:800]}{ctx_section}",
        max_tokens=200,
    )


# ── Multi-step Task Planner ───────────────────────────────────────────────────

def plan_task(description: str) -> List[str]:
    import json, re as _re
    os_name = platform.system()
    result = _call_groq(
        f"You are a shell assistant on {os_name}. The user wants to accomplish a task. "
        "Return ONLY a JSON array of shell commands to run in order — no explanation, no markdown:\n"
        '["cmd1", "cmd2", ...]',
        description,
        max_tokens=400,
    )
    if not result:
        return []
    # Strip markdown fences
    result = _re.sub(r'^```(?:json)?\s*', '', result)
    result = _re.sub(r'\s*```$', '', result)
    try:
        cmds = json.loads(result.strip())
        return [c for c in cmds if isinstance(c, str)]
    except Exception:
        return []


def run_task_plan(description: str, executor) -> None:
    print(Fore.CYAN + '[Aegis] Planning task...' + Style.RESET_ALL)
    steps = plan_task(description)
    if not steps:
        print(Fore.RED + '[Aegis] Could not generate a plan.' + Style.RESET_ALL)
        return

    print(Fore.CYAN + f'\n[Aegis] Plan ({len(steps)} steps):' + Style.RESET_ALL)
    for i, step in enumerate(steps, 1):
        print(f'  {i}. {Fore.YELLOW}{step}{Style.RESET_ALL}')

    confirm = input(Fore.GREEN + '\n[Aegis] Run this plan? (y/N): ' + Style.RESET_ALL).strip().lower()
    if confirm != 'y':
        print(Fore.YELLOW + '[Aegis] Plan cancelled.' + Style.RESET_ALL)
        return

    for i, step in enumerate(steps, 1):
        print(Fore.CYAN + f'\n[Aegis] Step {i}/{len(steps)}: {step}' + Style.RESET_ALL)
        success, error = executor.execute_command(step)
        if not success:
            print(Fore.RED + f'[Aegis] Step {i} failed. Stop? (y/N): ' + Style.RESET_ALL, end='')
            if input().strip().lower() == 'y':
                break


# ── Commit Message Generator ──────────────────────────────────────────────────

def generate_commit_message() -> Optional[str]:
    try:
        diff = subprocess.check_output(
            ['git', 'diff', '--staged'], text=True, stderr=subprocess.DEVNULL
        )
    except Exception:
        return None

    if not diff.strip():
        return None

    return _call_groq(
        "You are a git expert. Write a concise conventional commit message (type: description) "
        "for the following diff. One line only. No markdown, no quotes.",
        f"Git diff:\n{diff[:2000]}",
        max_tokens=60,
    )


# ── Conversation Context ──────────────────────────────────────────────────────

class ConversationContext:
    def __init__(self):
        self._context: List[str] = []

    def add(self, fact: str):
        self._context.append(fact)
        print(Fore.CYAN + f'[Aegis] Context noted: {fact}' + Style.RESET_ALL)

    def clear(self):
        self._context.clear()

    def get_system_suffix(self) -> str:
        if not self._context:
            return ''
        facts = '\n'.join(f'- {f}' for f in self._context)
        return f'\n\nSession context (use this to give better answers):\n{facts}'

    def list_context(self):
        if not self._context:
            print(Fore.YELLOW + '[Aegis] No session context set.' + Style.RESET_ALL)
            return
        print(Fore.CYAN + '[Aegis] Current session context:' + Style.RESET_ALL)
        for f in self._context:
            print(f'  - {f}')


# ── Sensitive Data Warning ────────────────────────────────────────────────────

def check_sensitive_data(command: str) -> Optional[str]:
    for pattern, label in _SENSITIVE_PATTERNS:
        if pattern.search(command):
            return label
    return None
