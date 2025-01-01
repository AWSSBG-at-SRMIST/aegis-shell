# Aegis Shell — Product Requirements Document

**Status:** Final
**Owner:** Tanish Poddar
**One-liner:** An AI-powered developer shell that runs any command, on any OS, and fixes what breaks — automatically.

---

## 1. Problem

Developers constantly context-switch to look up the right package manager command, debug cryptic stderr messages, or manually install missing tools before retrying the original command. On Windows this friction is worse — Unix commands fail silently, PowerShell vs CMD inconsistencies cause confusion, and tool setup requires visiting docs. There is no shell that handles this layer of friction transparently so developers can stay in flow.

---

## 2. Goals (v1 / MVP)

1. Accept any command — shell, PowerShell, CMD, Unix, or plain English — and route it to the correct interpreter automatically.
2. When a command fails, call the LLM to diagnose the error and surface a runnable fix in the same prompt.
3. When a tool is missing, identify the correct package and install it on confirmation, then replay the original command.
4. Store the Groq API key encrypted locally — no server, no account beyond Groq's free tier.
5. Work identically on Windows, macOS, and Linux without per-platform configuration.
6. Ship as a `pip install aegis-shell` package with an `aegis` entrypoint.

---

## 3. Non-Goals (explicit scope cuts)

- **Hosted service** — Aegis runs entirely locally; no cloud backend, no accounts, no telemetry.
- **GUI / web interface** — terminal only; a browser UI would require a web server and defeats the purpose.
- **Plugin marketplace** — the hook system is internal; no external plugin ecosystem in v1.
- **Git workflow beyond commit-msg** — PR review, branch management, and merge strategies belong in dedicated git tools.
- **Streaming LLM responses** — all Groq calls block until complete; streaming is a UX improvement for v2.

---

## 4. Users

**Primary:** Developers (student to mid-level) who work across Windows, macOS, and Linux and want a smarter terminal that removes the "look it up, install it, retry" cycle.

**Secondary:** Technical interviewers and recruiters evaluating this as a portfolio piece — the project needs to install cleanly, run without additional setup beyond a Groq key, and demonstrate clear AI integration.

---

## 5. User Stories

1. *As a developer,* I type a plain-English instruction ("show me all listening ports") so that I don't need to remember the exact `netstat` or `ss` flags for my OS.
2. *As a developer,* when a command fails with an obscure error, I want Aegis to tell me what went wrong and offer a one-keystroke fix so I don't have to search Stack Overflow.
3. *As a developer,* when I run a tool that isn't installed (`flutter`, `kubectl`, `terraform`), I want Aegis to identify it, suggest the install command, and run it on my approval — then replay my original command.
4. *As a developer,* I want to store API keys as named secrets and expand them inline (`$SECRET:OPENAI_KEY`) so I never paste secrets into the terminal history.
5. *As a developer,* I want to type `explain tar -xzf archive.tar.gz` before I run it so I understand what each flag does.
6. *As a developer,* I want to record a sequence of commands as a macro and replay it with one command so I don't repeat boilerplate setup steps.
7. *As a developer,* when I `cd` into a project directory, I want the relevant `.env` file loaded and the virtualenv activated automatically.

---

## 6. Functional Requirements

### 6.1 Command Execution

- Accept any string as input and route to the correct interpreter (PowerShell, CMD, bash, or direct subprocess).
- Detect Unix commands on Windows and translate to CMD equivalents (`ls` → `dir`, `rm` → `del`, etc.).
- Detect and run script files by extension (`.py`, `.js`, `.sh`, `.ps1`, `.bat`).
- Stream stdout and stderr in real time; allow Ctrl+C and Escape to terminate the child process.

### 6.2 AI — Natural Language

- Classify input as a real shell command or natural language via Groq API.
- Translate natural language to one or more OS-native shell commands.
- Show the translated command to the user before running it.

### 6.3 AI — Error Diagnosis

- On any non-zero exit code, call Groq to diagnose the command + stderr.
- Gather live system context (service names, Python version, port owners) to make the diagnosis accurate.
- Surface a `FIX:` command; offer to run it with a single keypress.

### 6.4 AI — Unknown Tool Install

- Detect when a binary is not on PATH.
- Ask Groq what the tool is and the correct install command for the current OS.
- Show explanation and install command; install on `y` confirmation.
- Replay the original command after successful install.

### 6.5 Security

- Scan every command for sensitive data patterns (passwords, API keys, tokens) before execution.
- Require `yes` for hard-dangerous commands (`format`, `shutdown`, `regedit`).
- Require `y` for destructive-but-common commands (`del`, `rm`, `taskkill`).
- Block system modification patterns (`reg add`, `netsh firewall`, `sc create`).

### 6.6 Secret Manager

- Store named secrets encrypted with Fernet; key file at `~/.aegis/.key`.
- Expand `$SECRET:NAME` tokens inline in any command; shell-quote the value before injection.
- Commands: `secret set`, `secret get` (masked display + clipboard option), `secret delete`, `secret list`.

### 6.7 Developer Workflow

- Auto-load `.env` on `cd`; print count of loaded variables.
- Auto-detect and activate virtualenv (`venv/`, `.venv/`, `env/`) on `cd`.
- `ports` — list all listening TCP ports with owning process name.
- `kill-port <port>` — terminate the process owning a port.
- `test` — detect test framework (`pytest`, `npm test`, `go test`) and run it.
- `new <template> <name>` — scaffold `flask-app`, `fastapi-app`, `react-app`, `node-api`, `python-cli`.
- `commit-msg` — generate a conventional commit message from `git diff --staged`.

### 6.8 Macros & Scripts

- `macro record <name>` / `macro stop` / `macro run <name>` — record and replay command sequences.
- `record start` / `record stop` — save full session transcript to file.
- `run <file>.aegis` — execute a plain-text Aegis script line by line.

### 6.9 UI

- Five colour themes: `default`, `dark`, `light`, `hacker`, `minimal`.
- `dashboard [seconds]` — live psutil CPU/RAM/disk/network monitor.
- `analytics` — ASCII bar chart of most-used and most-failed commands, hourly activity.
- `cheat <topic>` — quick reference sheets for git, docker, pip, python, npm, linux, aegis.
- Startup tip system — one tip per session, each tip shown only once.
- Tab autocomplete for all built-ins and known command names.

---

## 7. Non-Functional Requirements

- **Latency:** Groq calls must complete within 15 seconds; if they time out, the shell continues without AI assistance.
- **Security:** API key and secrets encrypted at rest (Fernet); sensitive data guard runs on every command before execution.
- **Reliability:** No command silently discarded — every execution is logged to `~/.aegis/audit.log`.
- **Portability:** No OS-specific code in the main REPL; platform branching isolated to `router.py`, `security_manager.py`, and `dev_workflow.py`.
- **Cost:** AI calls are on-demand only (not per keystroke); single-user free-tier Groq quota is sufficient for normal use.

---

## 8. Success Metrics

| Metric | Target |
|---|---|
| Install → first prompt | Under 60 seconds on a machine with Python 3.9+ |
| Missing tool → installed → command replays | Full flow under 60 seconds for a typical tool |
| Error diagnosis accuracy | Correct `FIX:` command for common errors (pip, git, port conflicts) |
| Cross-platform test | Runs without modification on Windows 11, Ubuntu 22.04, macOS 13+ |

---

## 9. Risks & Open Questions

- **Groq rate limits on free tier** — mitigated by on-demand calls only; no background polling.
- **LLM hallucinated install commands** — mitigated by always requiring user confirmation before any install.
- **Windows PATH mutations** — `activate_venv` modifies `os.environ['PATH']` in-process; may conflict with tools that rely on the original PATH. Mitigated by only prepending, not replacing.
- **Open question:** Should `diagnose_error` offer to automatically apply the fix without a confirmation prompt for low-risk fixes (e.g., `pip install missing-package`)?

---

## 10. v2 Candidates

- **Streaming LLM output** — show tokens as they arrive rather than blocking on the full response.
- **Plugin API** — allow third-party `.aegis` extensions to register new built-in commands via the hook system.
- **Shell history search (fzf-style)** — fuzzy search over command history with preview.
- **Git integration** — `aegis pr` to open a PR; `aegis blame` with AI annotation.
- **Config TUI** — interactive theme/model/key management without re-running first-time setup.
