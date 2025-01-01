# Aegis Shell — Architecture

<!--
Companion to PRD.md.
PRD says WHAT the system does. This says HOW.
Audience: an engineer who needs to understand the system well
enough to build it, debug it, or extend it.
-->

---

## 1. Stack

| Layer | Tech |
|---|---|
| Runtime | Python 3.9+ |
| Shell UI | prompt_toolkit 3.x — history, autocomplete, ANSI prompt, key bindings |
| AI / LLM | Groq API (OpenAI-compatible) · Llama 3.3-70B (default) |
| Encryption | cryptography · Fernet (AES-128-CBC + HMAC-SHA256) |
| System info | psutil 5.9+ |
| Colour output | colorama |
| Packaging | setuptools + pyproject.toml — pip-installable, `aegis` CLI entrypoint |
| Platform | Windows · macOS · Linux |

---

## 2. Components

```
aegis_shell.py         Main REPL — AegisShell class, startup, command dispatch
config_loader.py       Loads commands_mapping.json for known tool → install hints
llm/
  llm_handler.py       Groq API wrapper — classify_and_translate, handle_unknown_command
features/
  ai_features.py       explain_command, diagnose_error, plan_task, generate_commit_message
  prompt_builder.py    Builds the coloured shell prompt string
  themes.py            Five colour themes — loads/saves ~/.aegis/theme.json
  credential_manager.py  Fernet-encrypted secret store — secret_set/get/delete/list
  session_vars.py      In-memory $VAR assignment and expansion
  integrations.py      HTTP shorthand (GET/POST), alias expansion, clipboard
  dev_workflow.py      .env auto-load, venv detect+activate, port manager, project scaffold
  analytics.py         Per-command timing + success/fail stats — ~/.aegis/analytics.json
  audit_log.py         JSONL audit trail — ~/.aegis/audit.log
  macros.py            Record/replay sequences of commands
  session_recorder.py  Write full session transcript to file
  system_dashboard.py  Live psutil CPU/RAM/disk/net monitor
  learning.py          Startup tips + cheat sheets (git, docker, pip, python, npm, linux)
  hooks.py             Event bus: on_startup, on_exit, on_cd, before_command, after_command, on_error
  aegis_scripts.py     Run .aegis script files (line-by-line command lists)
  command_detection.py Known-command lookup against commands_mapping.json
  env_detector.py      Detect project type from directory contents
  help_system.py       Per-command help text
  package_manager.py   Install package via detected package manager
  documentation.py     Interactive documentation browser
utils/
  command_executor.py  Execute commands, stream stdout/stderr, handle Ctrl+C / Escape
  router.py            Detect shell dialect (powershell/cmd/unix_on_windows/direct/script/unknown)
  security_manager.py  Block/warn on dangerous commands; sensitive-file checks
  installers.py        Wrap package manager install commands
  download_animation.py  Progress bar for install operations
config/
  commands_mapping.json  Known tool → package → install method database
  config.json          Default shell config (default_language)
```

### AegisShell (aegis_shell.py)

The top-level REPL class. On startup it initialises config (first-time Groq API key setup + model choice), loads the theme, builds the prompt_toolkit session with history and autocomplete, and fires the `on_startup` hook. The main loop calls `_handle_builtin` first; if not matched, falls through to `_handle`. `_handle` runs the full pipeline: variable/secret expansion → alias expansion → HTTP shorthand check → sensitive data guard → LLM classify/translate → CommandExecutor → AI error diagnosis on failure.

### LLM Handler (llm/llm_handler.py)

Thin Groq API client. Two functions matter: `classify_and_translate` (decides if input is a real shell command or natural language, returns `{type, commands, explanation}`) and `handle_unknown_command` (given a command name, returns what it is and how to install it). Both return safe fallbacks on network failure — the shell degrades gracefully rather than crashing.

### CommandExecutor (utils/command_executor.py)

Validates the command through SecurityManager, detects the shell dialect via the router, checks if the binary exists, optionally triggers AI-assisted install, then runs the command via `subprocess.Popen` with live stdout/stderr streaming. A background thread watches for Escape keypress to terminate the child process cleanly.

### Router (utils/router.py)

Classifies a command string into one of six dialects: `powershell`, `cmd`, `unix_on_windows`, `direct`, `script`, `unknown`. Builds the correct `subprocess` argument list for each dialect so commands run in the right interpreter on every OS.

### Credential Manager (features/credential_manager.py)

Fernet-encrypted JSON store at `~/.aegis/credentials.json`. Key at `~/.aegis/.key` (reuses the same key as the API key store). `$SECRET:NAME` tokens in any command are expanded and shell-quoted before execution so secret values cannot inject commands.

### Security Manager (utils/security_manager.py)

Two tiers: hard-block commands (`format`, `shutdown`, `regedit`) require typing `yes` to proceed; warn commands (`del`, `rm`, `taskkill`, etc.) require `y`. Pattern matching blocks `reg add/delete`, firewall changes, and similar system-modification forms. Sensitive data patterns (token, API key, password, Groq/OpenAI/GitHub key formats) are scanned on every command.

---

## 3. Data Flow

```
[User types input]
     │
     ├─ Built-in? (exit/clear/explain/plan/secret/…)
     │       └─ Handle directly → output
     │
     └─ _handle() pipeline:
           │
           ├─ Variable/secret expansion ($VAR, $SECRET:NAME)
           ├─ Alias expansion (prs → gh pr list, aws-whoami → aws sts …)
           ├─ HTTP shorthand? → run_http_command() → output
           ├─ Sensitive data guard → warn + confirm or abort
           │
           ├─ classify_and_translate() [Groq API]
           │       type=command → commands=[original input]
           │       type=nl      → commands=[translated shell commands]
           │
           └─ For each command:
                 ├─ SecurityManager.validate_command()
                 │       dangerous → require "yes" / warn → require "y"
                 ├─ router.detect_dialect()
                 ├─ is_available(base)? No → _auto_install() [Groq API]
                 ├─ subprocess.Popen() — live stdout/stderr streaming
                 ├─ log_command() → ~/.aegis/audit.log
                 ├─ analytics_record() → ~/.aegis/analytics.json
                 └─ on failure → diagnose_error() [Groq API]
                                  → offer FIX: command
```

1. User types input at the prompt_toolkit REPL.
2. Built-in commands (50+) are dispatched directly without LLM involvement.
3. Everything else enters `_handle()`: expansions, guards, then Groq classification.
4. Natural language is translated to real OS commands before execution.
5. The command runs via subprocess with real-time streaming output.
6. On failure, a second Groq call diagnoses the error and proposes a fix.

---

## 4. Persistent Storage

All data lives under `~/.aegis/` (user home directory):

- `config.json` — Groq model choice + Fernet-encrypted API key + tips_seen list
- `.key` — Fernet encryption key (chmod 600 where supported; Windows relies on user-profile ACLs)
- `credentials.json` — Fernet-encrypted named secrets
- `theme.json` — active colour theme name
- `shell_history` — prompt_toolkit readline-style command history
- `analytics.json` — JSONL command timing and success/fail records (capped at 5000 entries)
- `audit.log` — append-only JSONL audit trail: timestamp, command, success, duration
- `macros/` — named macro files (sequences of commands)
- `recordings/` — session transcript files

No database, no server, no cloud sync. Everything is local files.

---

## 5. AI / LLM Design

### Input

Three distinct Groq call types:

1. **Classify/translate** — the raw user input string as plain text.
2. **Unknown command** — the base command name (`flutter`, `kubectl`, etc.) with an OS-specific install hint.
3. **Error diagnosis** — the failed command, exit code, stderr (truncated to 800 chars), plus live system context (service names, Python version, port ownership) gathered from the local machine.

### System prompt strategy

Each call uses a minimal, instruction-only system prompt with `temperature: 0.1` to maximise determinism. The classify prompt instructs the model to return only a JSON object — no markdown, no explanation outside the JSON. The diagnosis prompt restricts output to one diagnosis sentence and a `FIX:` prefixed command — nothing else.

### Response schema

Classify/translate:
```jsonc
{
  "type": "command" | "nl",
  "commands": ["cmd1", "cmd2"],
  "explanation": "brief note"
}
```

Unknown command (free-form, two lines):
```
EXPLANATION: [one sentence]
INSTALL: [exact install command]
```

### Validation

`classify_and_translate` strips markdown fences before `json.loads`. On parse failure it falls back to `{type: "command", commands: [original input]}` — the shell never crashes because the LLM returned bad JSON.

### Failure handling

All Groq calls have a 10–15 second timeout. On any network or parse failure the function returns `None` or a safe fallback. The shell continues running; AI features degrade silently rather than hard-failing the session.

---

## 6. Key Built-in Commands

| Command | Description |
|---|---|
| `explain <cmd>` | AI explains a shell command in plain English before you run it |
| `plan <task>` | AI generates a multi-step command plan; user approves before execution |
| `commit-msg` | AI writes a conventional commit message from `git diff --staged` |
| `diagnose` | Auto-triggered on any command failure; surfaces a `FIX:` command |
| `secret set/get/delete/list` | Fernet-encrypted secret store |
| `dashboard [sec]` | Live psutil CPU/RAM/disk/net monitor |
| `analytics` | ASCII bar chart of most-used and most-failed commands |
| `cheat <topic>` | Quick reference sheets for git, docker, pip, python, npm, linux, aegis |
| `theme set <name>` | Switch colour theme (default/dark/light/hacker/minimal) |
| `macro record/run/list` | Record and replay command sequences |
| `new <template> <name>` | Scaffold flask-app, fastapi-app, react-app, node-api, or python-cli |
| `ports` / `kill-port <p>` | List listening ports; kill process on a specific port |

---

## 7. Security

- **API key storage:** Groq API key encrypted with Fernet (AES-128-CBC) before writing to `~/.aegis/config.json`. Key file is `chmod 600` where OS supports it; on Windows it is protected by user-profile ACLs.
- **Secret expansion:** `$SECRET:NAME` tokens are expanded with `shlex.quote()` before injection into commands so values containing shell metacharacters cannot break out.
- **Sensitive data guard:** regex patterns catch passwords, API keys (Groq `gsk_`, OpenAI `sk-`, GitHub `ghp_`), and Bearer tokens in any command before it runs.
- **Dangerous command gate:** `format`, `shutdown`, `regedit` require typing `yes` in full. `del`, `rm`, `taskkill`, and similar warn + require `y`.
- **System modification block:** patterns like `reg add`, `netsh firewall`, `sc create` are blocked outright.

---

## 8. Error Handling & Reliability

| Failure | Behaviour |
|---|---|
| Groq API down or timeout | Returns `None`; shell falls back to running user input as-is |
| Bad JSON from LLM | Stripped of markdown fences, re-parsed; on failure returns safe default |
| Missing binary | `_auto_install()` flow: AI suggests install command, user confirms, installer runs, original command replays |
| Command Ctrl+C | Child process terminated gracefully (SIGTERM, then SIGKILL after 3s) |
| Escape key during run | Background watcher thread sets stop flag; child process terminated |
| Config file corrupt | Detected on load; first-time setup runs again to rebuild config |

---

## 9. Deployment

Aegis Shell is a locally installed CLI tool, not a hosted service.

1. **pip install:** `pip install aegis-shell` registers the `aegis` entrypoint via pyproject.toml.
2. **Source install:** `git clone` + `pip install -e .` for development.
3. **Windows installer:** `install.ps1` automates venv creation, dependency install, and PATH registration.
4. **Unix installer:** `install.sh` does the same for macOS/Linux.
5. **Packaging:** `build_installer.py` bundles a standalone executable via PyInstaller.

No cloud infrastructure required. All state is local to `~/.aegis/`.

---

## 10. Explicit Scope Cuts

- **Multi-user / server mode** — Aegis is a single-user local shell; no auth, no multi-tenancy, no daemon.
- **Plugin API** — the hook system (`hooks.py`) exists but there is no external plugin loader or marketplace.
- **Web UI** — terminal only; no browser-based interface.
- **Streaming LLM responses** — current Groq calls block until complete; real-time token streaming is a v2 item.
- **Git integration beyond commit-msg** — no PR review, no blame, no graph; those belong to dedicated tools.
