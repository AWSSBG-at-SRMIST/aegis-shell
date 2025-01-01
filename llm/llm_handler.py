import requests
import re
import json
import platform
from pathlib import Path
from cryptography.fernet import Fernet
from colorama import Fore, Style
from typing import Tuple, Optional, Dict

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.3-70b-versatile"


def _load_config():
    try:
        config_dir = Path.home() / '.aegis'
        config_file = config_dir / 'config.json'
        if not config_file.exists():
            return None, None
        with open(config_file, 'r') as f:
            config = json.load(f)
        key_file = config_dir / '.key'
        if not key_file.exists():
            return None, None
        with open(key_file, 'rb') as f:
            key = f.read()
        api_key = Fernet(key).decrypt(config['api_key'].encode()).decode()
        model = config.get('model', DEFAULT_MODEL)
        return api_key, model
    except Exception:
        return None, None


def _get_headers():
    api_key, _ = _load_config()
    if not api_key:
        return None
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def _get_model():
    _, model = _load_config()
    return model or DEFAULT_MODEL


def classify_and_translate(user_input: str) -> Dict:
    """
    Classify input as a direct shell command or natural language.
    If natural language, translate it to real executable commands.
    Returns: {"type": "command"|"nl", "commands": [...], "explanation": "..."}
    """
    headers = _get_headers()
    if not headers:
        return {"type": "command", "commands": [user_input], "explanation": ""}

    chain_hint = (
        "\n- On Windows PowerShell 5.1: use ';' not '&&' to chain commands"
        if platform.system() == 'Windows' else ""
    )
    payload = {
        "model": _get_model(),
        "messages": [
            {
                "role": "system",
                "content": (
                    f"You are the brain of a universal shell on {platform.system()}. "
                    "Determine if the user's input is a direct shell command or natural language.\n\n"
                    "Respond ONLY with a JSON object in this exact format:\n"
                    '{"type": "command" or "nl", "commands": ["cmd1", "cmd2"], "explanation": "brief note"}\n\n'
                    "Rules:\n"
                    "- If it looks like a real shell command (git, pip, ls, Get-Process, etc.), type='command', commands=[original input as-is]\n"
                    "- If it's natural language (e.g. 'show running processes', 'compress this folder'), type='nl', translate to real commands for the OS\n"
                    "- commands is always an array, even if one item\n"
                    "- No markdown, no explanation outside the JSON"
                    + chain_hint
                )
            },
            {"role": "user", "content": user_input}
        ],
        "temperature": 0.1
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"].strip()
            # Strip markdown fences if model wraps in ```json
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
            return json.loads(content.strip())
    except Exception:
        pass

    return {"type": "command", "commands": [user_input], "explanation": ""}


def handle_unknown_command(command: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Ask LLM what an unknown command is and how to install it.
    Returns (explanation, install_command).
    """
    headers = _get_headers()
    model = _get_model()

    if not headers:
        print(Fore.RED + "[Aegis] API key not configured. Run setup again." + Style.RESET_ALL)
        return None, None

    print(Fore.YELLOW + f"[Aegis] '{command}' not found — asking AI..." + Style.RESET_ALL)

    system = platform.system().lower()
    if system == 'windows':
        install_hint = (
            "For Windows use winget, choco, scoop, pip, or npm.\n"
            "Common winget IDs: Python.Python.3.12, OpenJS.NodeJS, Git.Git, "
            "Docker.DockerDesktop, GoLang.Go, Rustlang.Rustup, Microsoft.VisualStudioCode\n"
            "For tools not in winget, prefer choco."
        )
    elif system == 'linux':
        install_hint = "For Linux use apt, pip, or npm."
    else:
        install_hint = "For macOS use brew, pip, or npm."

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    f"You are inside a developer shell on {platform.system()}. "
                    "A command was not found. Respond in EXACTLY this format — two lines, nothing else:\n\n"
                    "EXPLANATION: [one sentence: what this tool does]\n"
                    "INSTALL: [exact install command]\n\n"
                    f"{install_hint}"
                )
            },
            {"role": "user", "content": f"Command not found: '{command}'"}
        ],
        "temperature": 0.1
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            reply = response.json()["choices"][0]["message"]["content"].strip()
            explanation = None
            install_cmd = None
            for line in reply.split('\n'):
                if line.startswith('EXPLANATION:'):
                    explanation = line.replace('EXPLANATION:', '').strip()
                elif line.startswith('INSTALL:'):
                    install_cmd = line.replace('INSTALL:', '').strip()
            return explanation, install_cmd
        else:
            print(Fore.RED + f"[Aegis] AI request failed: {response.status_code}" + Style.RESET_ALL)
            return None, None
    except Exception as e:
        print(Fore.RED + f"[Aegis] AI error: {e}" + Style.RESET_ALL)
        return None, None
