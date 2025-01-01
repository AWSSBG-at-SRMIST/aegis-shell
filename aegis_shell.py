import os
import sys
import json
import shlex
import subprocess
import time
import platform
from pathlib import Path

__version__ = "1.0.0"
from colorama import init, Fore, Style
from cryptography.fernet import Fernet
import requests

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding import KeyBindings

init()

from utils.command_executor import CommandExecutor
from llm.llm_handler import classify_and_translate
from features.documentation import DocumentationManager
from features.env_detector import EnvironmentDetector
from features.help_system import HelpSystem

# New feature modules
from features.ai_features import (
    explain_command, diagnose_error, plan_task, run_task_plan,
    generate_commit_message, ConversationContext, check_sensitive_data,
)
from features.prompt_builder import build_prompt
from features.session_recorder import SessionRecorder
from features.themes import load_theme, set_theme, list_themes, current_theme, c as theme_c
from features.dev_workflow import (
    load_dotenv, detect_venv, activate_venv,
    list_ports, kill_port, detect_and_run_tests, create_project,
    ssh_add, ssh_connect, ssh_list, TEMPLATES,
)
from features.macros import MacroRecorder, run_macro, list_macros, delete_macro
from features.hooks import register as hook_register, fire as hook_fire
from features.session_vars import is_assignment, handle_assignment, expand as var_expand, list_vars, unset as var_unset
from features.credential_manager import (
    secret_set, secret_get, secret_delete, secret_list, expand_secrets,
)
from features.integrations import (
    is_http_command, run_http_command, copy_to_clipboard, expand_all_aliases,
    paste_from_clipboard,
)
from config_loader import load_command_mappings
from features.analytics import record as analytics_record, show_analytics
from features.learning import show_cheat, show_startup_tip, CHEAT_SHEETS
from features.system_dashboard import show_dashboard
from features.aegis_scripts import run_script
from features.audit_log import log_command

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.3-70b-versatile"

GROQ_MODELS = [
    ("llama-3.3-70b-versatile", "Best quality — recommended"),
    ("llama3-8b-8192",          "Faster, lighter"),
    ("mixtral-8x7b-32768",      "Good balance of speed and quality"),
]
_GROQ_MODEL_NAMES = {m for m, _ in GROQ_MODELS}


class AegisShell:
    def __init__(self):
        self.config_dir  = Path.home() / '.aegis'
        self.config_file = self.config_dir / 'config.json'
        self.encryption_key = None
        self.model  = None
        self.api_key = None
        self._last_exit = 0
        self._tips_seen = []

        self.setup_config()
        load_theme()

        self.command_executor = CommandExecutor()
        self.doc_manager      = DocumentationManager()
        self.env_detector     = EnvironmentDetector()
        self.help_system      = HelpSystem()
        self.context          = ConversationContext()
        self.recorder         = SessionRecorder()
        self.macro_recorder   = MacroRecorder()

        self._setup_prompt()
        self._completer = self._build_completer()
        self._register_hooks()

    # ── Config & encryption ───────────────────────────────────────────────────

    def setup_config(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_encryption()
        if not self.config_file.exists():
            self._first_time_setup()
        else:
            self._load_config()

    def _setup_encryption(self):
        key_file = self.config_dir / '.key'
        if not key_file.exists():
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            try:
                os.chmod(key_file, 0o600)
            except Exception:
                pass  # Windows does not support chmod; protected by user-profile ACLs
        else:
            with open(key_file, 'rb') as f:
                key = f.read()
        self.encryption_key = Fernet(key)

    def _encrypt(self, value: str) -> str:
        return self.encryption_key.encrypt(value.encode()).decode()

    def _decrypt(self, value: str) -> str:
        return self.encryption_key.decrypt(value.encode()).decode()

    def _load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            model = config.get('model', '')
            if model not in _GROQ_MODEL_NAMES:
                print(theme_c('warning') + '[Aegis] Outdated config detected, running first-time setup...' + Style.RESET_ALL + '\n')
                self.config_file.unlink(missing_ok=True)
                self._first_time_setup()
                return
            self.model   = model
            self.api_key = self._decrypt(config['api_key'])
            self._tips_seen = config.get('tips_seen', [])
        except Exception as e:
            print(theme_c('error') + f'Error loading config: {e}' + Style.RESET_ALL)
            sys.exit(1)

    def _save_config(self):
        config = {
            'model':     self.model,
            'api_key':   self._encrypt(self.api_key),
            'first_run': False,
            'tips_seen': self._tips_seen,
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)

    def _first_time_setup(self):
        print(theme_c('info') + '=' * 60 + Style.RESET_ALL)
        print(theme_c('info') + '        Welcome to Aegis Shell — First-time Setup' + Style.RESET_ALL)
        print(theme_c('info') + '=' * 60 + Style.RESET_ALL + '\n')
        print(theme_c('warning') + 'Aegis uses Groq for AI features — free and very fast.' + Style.RESET_ALL)
        print(theme_c('warning') + 'Get your free API key at: ' + theme_c('info') + 'https://console.groq.com/keys' + Style.RESET_ALL + '\n')
        print(theme_c('success') + 'Choose a model:' + Style.RESET_ALL)
        for i, (name, desc) in enumerate(GROQ_MODELS, 1):
            suffix = ' (default)' if i == 1 else ''
            print(f'  {i}. {name} — {desc}{suffix}')

        choice = input(theme_c('success') + f'\nEnter 1-{len(GROQ_MODELS)} (or Enter for default): ' + Style.RESET_ALL).strip()
        try:
            idx = int(choice) - 1
            self.model = GROQ_MODELS[idx][0] if 0 <= idx < len(GROQ_MODELS) else DEFAULT_MODEL
        except (ValueError, IndexError):
            self.model = DEFAULT_MODEL
        print(theme_c('info') + f'Using: {self.model}' + Style.RESET_ALL + '\n')

        while True:
            self.api_key = input(theme_c('success') + 'Enter your Groq API key: ' + Style.RESET_ALL).strip()
            if not self.api_key:
                print(theme_c('error') + 'API key cannot be empty.' + Style.RESET_ALL)
                continue
            if not self.api_key.startswith('gsk_'):
                print(theme_c('warning') + "Note: Groq keys usually start with 'gsk_'." + Style.RESET_ALL)
                if input(theme_c('warning') + 'Continue anyway? (y/N): ' + Style.RESET_ALL).strip().lower() != 'y':
                    continue
            print(theme_c('info') + 'Validating key...' + Style.RESET_ALL)
            if self._validate_api_key():
                print(theme_c('success') + '[OK] Key valid!' + Style.RESET_ALL)
                break
            else:
                print(theme_c('error') + '[ERROR] Validation failed. Check your key and try again.' + Style.RESET_ALL)
                if input(theme_c('warning') + 'Try again? (Y/n): ' + Style.RESET_ALL).strip().lower() == 'n':
                    sys.exit(0)

        try:
            self._save_config()
            print(theme_c('success') + f'\nSetup complete! Config saved to {self.config_file}' + Style.RESET_ALL + '\n')
        except Exception as e:
            print(theme_c('error') + f'Failed to save config: {e}' + Style.RESET_ALL)
            sys.exit(1)

    def _validate_api_key(self) -> bool:
        try:
            r = requests.post(
                GROQ_API_URL,
                headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'},
                json={'model': self.model, 'messages': [{'role': 'user', 'content': 'Hi'}], 'max_tokens': 5},
                timeout=10,
            )
            return r.status_code == 200
        except Exception:
            return False

    # ── Hooks ─────────────────────────────────────────────────────────────────

    def _register_hooks(self):
        hook_register('on_cd', lambda path: self._on_cd(path))

    def _on_cd(self, path: str):
        venv = detect_venv(path)
        if venv and os.environ.get('VIRTUAL_ENV') != venv:
            activate_venv(venv)
        loaded = load_dotenv(path)
        if loaded:
            print(theme_c('info') + f'[Aegis] Loaded {len(loaded)} vars from .env' + Style.RESET_ALL)

    # ── Prompt ────────────────────────────────────────────────────────────────

    def _setup_prompt(self):
        self.session = PromptSession(
            history=FileHistory(str(self.config_dir / 'shell_history')),
            auto_suggest=AutoSuggestFromHistory(),
        )

    def _build_completer(self):
        known = (
            list(load_command_mappings().keys())
            + [
                'help', 'docs', 'env', 'stats', 'clear', 'cls', 'exit',
                'explain', 'plan', 'commit-msg', 'context', 'diagnose',
                'ports', 'kill-port', 'test', 'new', 'ssh-add', 'ssh-connect', 'ssh-list',
                'macro', 'record', 'theme', 'secret', 'analytics', 'dashboard',
                'cheat', 'vars', 'unset', 'clip', 'paste', 'run',
            ]
        )
        return WordCompleter(sorted(set(known)), ignore_case=True)

    def _make_prompt(self) -> ANSI:
        return ANSI(build_prompt(self._last_exit, theme_c('prompt')))

    # ── REPL ──────────────────────────────────────────────────────────────────

    def display_welcome(self):
        print()
        print(Fore.CYAN  + '  ╔════════════════════════════════════════════════╗' + Style.RESET_ALL)
        print(Fore.CYAN  + '  ║                                                ║' + Style.RESET_ALL)
        print(Fore.CYAN  + '  ║   ' + Style.BRIGHT + '⚔   A E G I S   S H E L L   ⚔' + Style.RESET_ALL + Fore.CYAN + '            ║' + Style.RESET_ALL)
        print(Fore.CYAN  + '  ║                                                ║' + Style.RESET_ALL)
        print(Fore.CYAN  + f'  ║   v{__version__:<44}║' + Style.RESET_ALL)
        print(Fore.CYAN  + '  ║   Tanish · Nidhi · Nishant  ·  SRMIST         ║' + Style.RESET_ALL)
        print(Fore.CYAN  + '  ║                                                ║' + Style.RESET_ALL)
        print(Fore.CYAN  + '  ╚════════════════════════════════════════════════╝' + Style.RESET_ALL)
        print()
        print(theme_c('success') + '  Type commands or plain English.  "help" for built-ins.  "exit" to quit.' + Style.RESET_ALL)
        print()

        try:
            env = self.env_detector.detect_environment('.')
            detected = [item for items in env.values() for item in items]
            if detected:
                print(theme_c('info') + f'  [Aegis] Detected: {", ".join(sorted(detected))}' + Style.RESET_ALL)
        except Exception:
            pass

        key = show_startup_tip(self._tips_seen)
        self._tips_seen.append(key)
        try:
            self._save_config()
        except Exception:
            pass
        print()

    def start(self):
        self.display_welcome()
        hook_fire('on_startup')

        # Auto-load .env and venv in current dir on startup
        self._on_cd('.')

        while True:
            try:
                user_input = self.session.prompt(
                    self._make_prompt(),
                    completer=self._completer,
                ).strip()

                if not user_input:
                    continue

                # Record input if session is being recorded
                if self.recorder.is_recording:
                    self.recorder.record_input(user_input)

                # Record macro step if recording
                if self.macro_recorder.is_recording:
                    if user_input.lower() == 'macro stop':
                        self.macro_recorder.stop()
                        continue
                    self.macro_recorder.record(user_input)

                if not self._handle_builtin(user_input):
                    self._handle(user_input)

            except KeyboardInterrupt:
                print(theme_c('warning') + "\nUse 'exit' to quit" + Style.RESET_ALL)
            except EOFError:
                print(theme_c('warning') + '\nGoodbye!' + Style.RESET_ALL)
                break
            except Exception as e:
                print(theme_c('error') + f'Error: {e}' + Style.RESET_ALL)

        hook_fire('on_exit')

    # ── Built-in command dispatcher ───────────────────────────────────────────

    def _handle_builtin(self, user_input: str) -> bool:
        parts = user_input.strip().split()
        cmd   = parts[0].lower()
        args  = parts[1:]

        # ── Core ──
        if cmd == 'exit':
            print(theme_c('warning') + '\nGoodbye!' + Style.RESET_ALL)
            sys.exit(0)

        if cmd in ('clear', 'cls'):
            os.system('cls' if platform.system() == 'Windows' else 'clear')
            return True

        if cmd == 'docs':
            self.doc_manager.run()
            return True

        if cmd == 'help':
            if args:
                self.help_system.show_help(args[0])
            else:
                self._show_help()
            return True

        if cmd == 'env':
            try:
                self.env_detector.detect_environment('.')
                self.env_detector.print_environment()
            except Exception as e:
                print(theme_c('error') + f'[Aegis] env error: {e}' + Style.RESET_ALL)
            return True

        if cmd == 'stats':
            total   = self.command_executor.total_count
            success = self.command_executor.success_count
            rate    = self.command_executor.get_success_rate()
            print(theme_c('info') + f'\n[Aegis] Session: {success}/{total} commands succeeded ({rate:.1f}%)\n' + Style.RESET_ALL)
            return True

        # ── AI Features ──
        if cmd == 'explain':
            if not args:
                print(theme_c('warning') + 'Usage: explain <command>' + Style.RESET_ALL)
                return True
            cmd_to_explain = ' '.join(args)
            print(theme_c('info') + '[Aegis] Explaining...' + Style.RESET_ALL)
            result = explain_command(cmd_to_explain)
            if result:
                print(theme_c('info') + f'\n[Aegis] {result}\n' + Style.RESET_ALL)
            else:
                print(theme_c('error') + '[Aegis] Could not explain command.' + Style.RESET_ALL)
            return True

        if cmd == 'plan':
            if not args:
                print(theme_c('warning') + 'Usage: plan <task description>' + Style.RESET_ALL)
                return True
            run_task_plan(' '.join(args), self.command_executor)
            return True

        if cmd == 'commit-msg':
            print(theme_c('info') + '[Aegis] Generating commit message from staged diff...' + Style.RESET_ALL)
            msg = generate_commit_message()
            if msg:
                print(theme_c('success') + f'\n  {msg}\n' + Style.RESET_ALL)
                if input(theme_c('warning') + 'Use this message? (y/N): ' + Style.RESET_ALL).strip().lower() == 'y':
                    self._handle(f"git commit -m {shlex.quote(msg)}")
            else:
                print(theme_c('warning') + '[Aegis] No staged changes or could not generate message.' + Style.RESET_ALL)
            return True

        if cmd == 'context':
            if not args:
                self.context.list_context()
                return True
            sub = args[0].lower()
            if sub == 'add' and len(args) > 1:
                self.context.add(' '.join(args[1:]))
            elif sub == 'clear':
                self.context.clear()
                print(theme_c('info') + '[Aegis] Context cleared.' + Style.RESET_ALL)
            else:
                self.context.add(' '.join(args))
            return True

        # ── Dev Workflow ──
        if cmd == 'ports':
            list_ports()
            return True

        if cmd == 'kill-port':
            if not args:
                print(theme_c('warning') + 'Usage: kill-port <port>' + Style.RESET_ALL)
                return True
            try:
                kill_port(int(args[0]))
            except ValueError:
                print(theme_c('error') + '[Aegis] Port must be a number.' + Style.RESET_ALL)
            return True

        if cmd == 'test':
            test_cmd = detect_and_run_tests('.')
            if test_cmd:
                print(theme_c('info') + f'[Aegis] Detected: {test_cmd}' + Style.RESET_ALL)
                self._handle(test_cmd)
            else:
                print(theme_c('warning') + '[Aegis] No test framework detected in current directory.' + Style.RESET_ALL)
            return True

        if cmd == 'new':
            if len(args) < 2:
                print(theme_c('warning') + f'Usage: new <template> <name>' + Style.RESET_ALL)
                print(theme_c('info')  + f'Templates: {", ".join(TEMPLATES)}' + Style.RESET_ALL)
                return True
            create_project(args[0], args[1])
            return True

        if cmd == 'ssh-add':
            # ssh-add <name> <host> [user] [port]
            if len(args) < 2:
                print(theme_c('warning') + 'Usage: ssh-add <name> <host> [user] [port]' + Style.RESET_ALL)
                return True
            name  = args[0]
            host  = args[1]
            user  = args[2] if len(args) > 2 else ''
            port  = int(args[3]) if len(args) > 3 else 22
            ssh_add(name, host, user, port)
            return True

        if cmd == 'ssh-connect':
            if not args:
                ssh_list()
                return True
            cmd_str = ssh_connect(args[0])
            if cmd_str:
                print(theme_c('info') + f'[Aegis] Connecting: {cmd_str}' + Style.RESET_ALL)
                self._handle(cmd_str)
            return True

        if cmd == 'ssh-list':
            ssh_list()
            return True

        # ── Macros ──
        if cmd == 'macro':
            if not args:
                list_macros()
                return True
            sub = args[0].lower()
            if sub == 'record' and len(args) > 1:
                self.macro_recorder.start(args[1])
            elif sub == 'stop':
                self.macro_recorder.stop()
            elif sub == 'run' and len(args) > 1:
                run_macro(args[1], self.command_executor)
            elif sub == 'list':
                list_macros()
            elif sub == 'delete' and len(args) > 1:
                delete_macro(args[1])
            else:
                print(theme_c('warning') + 'Usage: macro record <name> | macro stop | macro run <name> | macro list | macro delete <name>' + Style.RESET_ALL)
            return True

        # ── Session Recording ──
        if cmd == 'record':
            if not args or args[0] == 'start':
                filename = args[1] if len(args) > 1 else None
                path = self.recorder.start(filename)
                print(theme_c('success') + f'[Aegis] Recording to: {path}' + Style.RESET_ALL)
            elif args[0] == 'stop':
                path = self.recorder.stop()
                print(theme_c('success') + f'[Aegis] Saved to: {path}' + Style.RESET_ALL)
            elif args[0] == 'list':
                self.recorder.list_recordings()
            elif args[0] == 'status':
                if self.recorder.is_recording:
                    print(theme_c('success') + f'[Aegis] Recording: {self.recorder.current_file}' + Style.RESET_ALL)
                else:
                    print(theme_c('warning') + '[Aegis] Not recording.' + Style.RESET_ALL)
            return True

        # ── Themes ──
        if cmd == 'theme':
            if not args or args[0] == 'list':
                themes = list_themes()
                print(theme_c('info') + f'[Aegis] Available themes: {", ".join(themes)}' + Style.RESET_ALL)
                print(theme_c('info') + f'[Aegis] Current: {current_theme()}' + Style.RESET_ALL)
            elif args[0] == 'set' and len(args) > 1:
                if set_theme(args[1]):
                    print(theme_c('success') + f'[Aegis] Theme set to "{args[1]}".' + Style.RESET_ALL)
                else:
                    print(theme_c('error') + f'[Aegis] Unknown theme "{args[1]}".' + Style.RESET_ALL)
            return True

        # ── Secrets ──
        if cmd == 'secret':
            if not args:
                secret_list()
                return True
            sub = args[0].lower()
            if sub == 'set' and len(args) >= 3:
                secret_set(args[1], ' '.join(args[2:]))
            elif sub == 'get' and len(args) > 1:
                val = secret_get(args[1])
                if val:
                    masked = val[:4] + '****' + val[-4:] if len(val) > 8 else '****'
                    print(theme_c('success') + f'[Aegis] {args[1]}: {masked}' + Style.RESET_ALL)
                    if input(theme_c('warning') + '  Copy full value to clipboard? (y/N): ' + Style.RESET_ALL).strip().lower() == 'y':
                        copy_to_clipboard(val)
                else:
                    print(theme_c('warning') + f'[Aegis] No secret "{args[1]}".' + Style.RESET_ALL)
            elif sub == 'delete' and len(args) > 1:
                secret_delete(args[1])
            elif sub == 'list':
                secret_list()
            else:
                print(theme_c('warning') + 'Usage: secret set <name> <value> | secret get <name> | secret delete <name> | secret list' + Style.RESET_ALL)
            return True

        # ── Session variables ──
        if cmd == 'vars':
            list_vars()
            return True

        if cmd == 'unset' and args:
            var_unset(args[0])
            return True

        # ── Clipboard ──
        if cmd == 'clip':
            text = ' '.join(args) if args else ''
            if not text:
                print(theme_c('warning') + 'Usage: clip <text>  OR  pipe with |' + Style.RESET_ALL)
                return True
            copy_to_clipboard(text)
            return True

        if cmd == 'paste':
            text = paste_from_clipboard()
            if text:
                print(text)
            else:
                print(theme_c('warning') + '[Aegis] Clipboard is empty.' + Style.RESET_ALL)
            return True

        # ── Analytics ──
        if cmd == 'analytics':
            show_analytics()
            return True

        # ── Dashboard ──
        if cmd == 'dashboard':
            duration = int(args[0]) if args else 30
            show_dashboard(duration=duration, interval=1.0)
            return True

        # ── Cheat sheets ──
        if cmd == 'cheat':
            if not args:
                print(theme_c('info') + f'[Aegis] Available cheat sheets: {", ".join(sorted(CHEAT_SHEETS))}' + Style.RESET_ALL)
            else:
                show_cheat(args[0])
            return True

        # ── Aegis scripts ──
        if cmd == 'run' and args and args[0].endswith('.aegis'):
            run_script(args[0], self.command_executor)
            return True

        # ── Self-update ──
        if cmd == 'update':
            self._self_update()
            return True

        # ── cd with hook ──
        if cmd == 'cd':
            target = args[0] if args else str(Path.home())
            try:
                os.chdir(target)
                hook_fire('on_cd', path=target)
            except FileNotFoundError:
                print(theme_c('error') + f'[Aegis] Directory not found: {target}' + Style.RESET_ALL)
            return True

        return False

    # ── Main command handler ──────────────────────────────────────────────────

    def _handle(self, user_input: str):
        # Session variable assignment: $VAR = value
        if is_assignment(user_input):
            handle_assignment(user_input)
            return

        # Expand $SECRET:NAME
        user_input = expand_secrets(user_input)

        # Expand session $VARs
        user_input = var_expand(user_input)

        # Expand aliases (git, docker, gh, cloud)
        expanded = expand_all_aliases(user_input)
        if expanded:
            print(theme_c('info') + f'[Aegis] → {expanded}' + Style.RESET_ALL)
            user_input = expanded

        # HTTP shorthand: GET/POST/PUT/DELETE https://...
        if is_http_command(user_input):
            run_http_command(user_input)
            return

        # Sensitive data check
        leak = check_sensitive_data(user_input)
        if leak:
            print(theme_c('warning') + f'[Aegis] Warning: This command may contain a {leak}.' + Style.RESET_ALL)
            if input(theme_c('warning') + '  Run anyway? (y/N): ' + Style.RESET_ALL).strip().lower() != 'y':
                return

        # Run .aegis script
        if user_input.strip().endswith('.aegis') and Path(user_input.strip()).exists():
            run_script(user_input.strip(), self.command_executor)
            return

        hook_fire('before_command', command=user_input)

        # LLM classify + translate
        result = classify_and_translate(user_input)
        cmds   = result.get('commands', [])

        if result.get('type') == 'nl':
            if not cmds:
                print(theme_c('warning') + "[Aegis] That doesn't look like a shell command — try rephrasing." + Style.RESET_ALL)
                return
            print(theme_c('info') + f'[Aegis] → {" && ".join(cmds)}' + Style.RESET_ALL)
        else:
            if not cmds:
                cmds = [user_input]

        for cmd in cmds:
            # Re-run sensitive data check on LLM-translated commands
            if result.get('type') == 'nl':
                leak = check_sensitive_data(cmd)
                if leak:
                    print(theme_c('warning') + f'[Aegis] Warning: Translated command may contain a {leak}.' + Style.RESET_ALL)
                    if input(theme_c('warning') + '  Run anyway? (y/N): ' + Style.RESET_ALL).strip().lower() != 'y':
                        continue

            t0 = time.time()
            success, error = self.command_executor.execute_command(cmd)
            duration = time.time() - t0
            self._last_exit = 0 if success else 1

            # Audit log
            log_command(cmd, success, duration)

            # Analytics
            analytics_record(cmd, success, duration)

            if not success:
                hook_fire('on_error', command=cmd, error=error)
                if error:
                    if error.startswith('[Aegis] Blocked:'):
                        # Security block or user cancellation — no diagnosis needed
                        print(theme_c('warning') + error + Style.RESET_ALL)
                    elif error.strip():
                        # Auto-diagnose on real failures
                        print(theme_c('error') + error + Style.RESET_ALL, end='')
                        print(theme_c('info') + '\n[Aegis] Diagnosing...' + Style.RESET_ALL)
                        fix = diagnose_error(cmd, error, 1)
                        if fix:
                            print(theme_c('info') + f'[Aegis] {fix}' + Style.RESET_ALL)
                            # Extract the FIX: command and offer to run it
                            fix_cmd = None
                            for line in fix.splitlines():
                                if line.strip().startswith('FIX:'):
                                    fix_cmd = line.split('FIX:', 1)[1].strip()
                                    break
                            if fix_cmd:
                                ans = input(theme_c('warning') + f'  Run fix? (y/N): ' + Style.RESET_ALL).strip().lower()
                                if ans == 'y':
                                    self._handle(fix_cmd)

            hook_fire('after_command', command=cmd, success=success, duration=duration)

    # ── Self-update ──────────────────────────────────────────────────────────

    def _self_update(self):
        install_dir = Path(__file__).resolve().parent
        git_dir     = install_dir / '.git'

        if not git_dir.exists():
            print(theme_c('warning') + '[Aegis] Not installed via git.' + Style.RESET_ALL)
            print(theme_c('info')   + '[Aegis] Run: pip install --upgrade aegis-shell' + Style.RESET_ALL)
            return

        print(theme_c('info') + '[Aegis] Checking for updates...' + Style.RESET_ALL)
        result = subprocess.run(
            ['git', '-C', str(install_dir), 'pull'],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(theme_c('error') + f'[Aegis] Update failed: {result.stderr.strip()}' + Style.RESET_ALL)
            return

        if 'Already up to date' in result.stdout:
            print(theme_c('success') + '[Aegis] Already up to date.' + Style.RESET_ALL)
            return

        print(theme_c('success') + '[Aegis] Updated! Refreshing dependencies...' + Style.RESET_ALL)
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-q', '-r',
             str(install_dir / 'requirements.txt')],
            capture_output=True
        )
        print(theme_c('success') + '[Aegis] Done. Restart aegis to apply changes.' + Style.RESET_ALL)

    # ── Help ─────────────────────────────────────────────────────────────────

    def _show_help(self):
        print(theme_c('info') + '\n  Aegis Shell — Commands\n' + Style.RESET_ALL)
        groups = [
            ('Core', [
                ('help [cmd]',      'Show help'),
                ('env',             'Detect project environment'),
                ('stats',           'Session success rate'),
                ('docs',            'Documentation browser'),
                ('clear / cls',     'Clear screen'),
                ('cd <path>',       'Change directory (auto .env + venv)'),
                ('update',          'Pull latest version from GitHub'),
                ('exit',            'Quit'),
            ]),
            ('AI', [
                ('explain <cmd>',   'AI explains the command before you run it'),
                ('plan <task>',     'AI plans multi-step task, you approve'),
                ('commit-msg',      'AI writes commit message from staged diff'),
                ('context add ...',  'Add session context for smarter AI replies'),
                ('context clear',   'Clear session context'),
            ]),
            ('Dev Workflow', [
                ('ports',           'List all listening ports'),
                ('kill-port <p>',   'Kill process on port'),
                ('test',            'Auto-detect and run project tests'),
                ('new <tpl> <name>','Scaffold project (flask-app, fastapi-app, react-app, node-api, python-cli)'),
                ('ssh-add',         'Save SSH profile'),
                ('ssh-connect',     'Connect via saved profile'),
                ('ssh-list',        'List saved SSH profiles'),
            ]),
            ('Macros & Scripts', [
                ('macro record <n>','Start recording a macro'),
                ('macro stop',      'Stop recording'),
                ('macro run <n>',   'Replay a macro'),
                ('macro list',      'List macros'),
                ('run <file>.aegis','Run an Aegis script'),
                ('record start',    'Record session to file'),
                ('record stop',     'Stop recording'),
            ]),
            ('Themes & UI', [
                ('theme list',      'List color themes'),
                ('theme set <n>',   'Switch theme (default/dark/light/hacker/minimal)'),
                ('dashboard [sec]', 'Live CPU/RAM/disk/process monitor'),
                ('analytics',       'Command usage stats + charts'),
                ('cheat <topic>',   'Quick reference (git, docker, pip, python, npm, linux, aegis)'),
            ]),
            ('Secrets & Vars', [
                ('secret set K V',  'Store encrypted secret'),
                ('secret get K',    'Retrieve secret'),
                ('secret list',     'List stored secrets'),
                ('$VAR = value',    'Set session variable'),
                ('vars',            'List session variables'),
                ('unset $VAR',      'Remove session variable'),
                ('$SECRET:KEY',     'Expand secret inline in any command'),
            ]),
            ('Integrations', [
                ('GET <url>',       'HTTP request with pretty output'),
                ('POST <url> -d …', 'POST request'),
                ('clip <text>',     'Copy to clipboard'),
                ('paste',           'Paste from clipboard'),
                ('prs',             'gh pr list'),
                ('aws-whoami',      'AWS identity check'),
            ]),
        ]

        for group, items in groups:
            print(theme_c('info') + f'  {group}' + Style.RESET_ALL)
            for name, desc in items:
                print(f'    {theme_c('success')}{name:<26}{Style.RESET_ALL} {desc}')
            print()


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ('--version', 'version', '-v'):
        print(f'Aegis Shell v{__version__}')
        return
    shell = AegisShell()
    shell.start()


if __name__ == '__main__':
    main()
