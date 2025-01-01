# Engineering Decisions — Aegis Shell

<!--
This is not user documentation. This is for technical interviewers
and senior engineers who want to understand WHY the system is built
the way it is.
-->

---

## Decision 1 — Why Groq over OpenAI or Anthropic

**Context:** Aegis needs an LLM for three interactive tasks: command classification, error diagnosis, and unknown-tool identification. These calls happen inside a running shell session — latency directly impacts the developer's flow. Several providers were available: OpenAI (GPT-4o), Anthropic (Claude), and Groq.

**Decision:** Groq with Llama 3.3-70B as default, with Llama-3-8B and Mixtral-8x7B available as user-selectable alternatives.

**Reason:** Groq's inference hardware delivers sub-second response times for the short prompts Aegis uses (most calls are under 200 tokens input). The free tier quota is sufficient for interactive single-user use without requiring a credit card. Llama 3.3-70B quality is adequate for command classification and error diagnosis — these are structured tasks with tight output schemas, not open-ended generation.

**Tradeoff:** Groq's free tier has stricter rate limits than paid OpenAI. On heavy use (many failures in a session) the user could hit limits. This is acceptable because the shell degrades gracefully — it falls back to running commands as-is rather than crashing.

---

## Decision 2 — Why route to OS-native shell dialects instead of always using bash/PowerShell

**Context:** Developers type commands that assume their usual shell. On Windows a user might type `ls`, `Get-Process`, `dir`, `python script.py`, or `npm install` — each of these needs a different interpreter. Forcing everything through one shell causes failures (`ls` fails in PowerShell 5.x, `Get-Process | Where-Object` fails in cmd.exe).

**Decision:** The `router.py` module classifies each command into one of six dialects (`powershell`, `cmd`, `unix_on_windows`, `direct`, `script`, `unknown`) and builds the correct `subprocess` argument list.

**Reason:** Automatic dialect detection means the user never thinks about which shell to use. `dir` goes to `cmd /c`, `Get-Process` goes to `powershell -Command`, `ls` on Windows gets translated to `dir` via `cmd /c`, and `pip install` runs as a direct subprocess. This covers the vast majority of real developer commands without requiring configuration.

**Tradeoff:** The classifier uses heuristics (PowerShell Verb-Noun regex, CMD built-in list, Unix command set) and will misclassify unusual commands. Unknown commands default to PowerShell on Windows, which is correct for most cases but wrong for some CMD-only scripts. A v2 improvement would be to ask the LLM to classify ambiguous cases.

---

## Decision 3 — Why Fernet for secret encryption instead of OS keychain

**Context:** Aegis stores the Groq API key and any user-defined secrets. Options: OS keychain (Windows Credential Manager, macOS Keychain, libsecret on Linux), or in-process encryption with a file-based key.

**Decision:** Fernet (from the `cryptography` package) with a key file at `~/.aegis/.key`.

**Reason:** OS keychain APIs are inconsistent across platforms. macOS Keychain requires `keyring` or `security` CLI access. Windows Credential Manager has different behavior across Python versions. libsecret on Linux requires D-Bus and is not available in all environments (e.g., minimal Docker images, CI). Fernet is pure-Python, cross-platform, and gives AES-128-CBC with HMAC-SHA256 — strong enough for API keys stored locally.

**Tradeoff:** The Fernet key is stored in a file on disk. If an attacker has read access to the user's home directory, they can read both the key and the ciphertext. This is the same threat model as the OS keychain on most systems without hardware-backed secure storage. `chmod 600` is applied where the OS supports it; on Windows, user-profile ACLs provide equivalent protection.

---

## Decision 4 — Why auto-diagnose on every failure rather than requiring the user to ask

**Context:** When a command fails, the user's typical next step is to copy the error and search the web. Aegis could either wait for the user to type `diagnose` or trigger diagnosis automatically on any non-zero exit code.

**Decision:** Auto-diagnose on every failure — no user command required.

**Reason:** The vast majority of command failures in a developer shell are genuine errors the user wants fixed, not intentional non-zero exits. Requiring a separate `diagnose` command adds friction. The Groq call is fast (under 2s on most queries) and the output is short — showing it inline does not disrupt the session. The `FIX:` command still requires `y` confirmation before running, so the auto-trigger carries no execution risk.

**Tradeoff:** On intentional non-zero exits (a script that returns 1 to signal "not found" or "no matches") the diagnosis will fire unnecessarily. This produces noise but no harm. A v2 improvement would be to skip diagnosis if the stderr is empty (many deliberate non-zero exits produce no error output).

---

## What I'd do differently in v2

- **Streaming Groq responses** — current calls block until the full response arrives. For the `plan` command, which can generate 5–8 steps, the 1–2 second wait is noticeable. Streaming would show tokens as they arrive, making the shell feel more responsive.
- **Replace regex sensitive-data scanner with a token classifier** — the current regex approach catches known patterns (Groq `gsk_`, OpenAI `sk-`, GitHub `ghp_`) but misses custom API key formats and produces false positives on some data strings. A small classifier trained on common secret formats would be more accurate.
- **Persist session variables across restarts** — `$VAR = value` assignments currently live only in memory. A lightweight persist layer (append to `~/.aegis/vars.json` on assignment) would make session variables genuinely useful for long-running workflows.

---

## Explicit non-decisions (deferred to v2)

| Feature | Why deferred |
|---|---|
| Streaming LLM output | Requires switching to the Groq streaming API and restructuring the output pipeline — scope for v1 was correctness over polish |
| OS keychain integration | Cross-platform inconsistency makes it unreliable as the sole mechanism; Fernet covers the security requirement with simpler code |
| Plugin API / extension system | The hook system (`hooks.py`) is the foundation, but a proper plugin loader with namespacing, sandboxing, and discovery adds significant surface area |
| Git PR / branch management | Out of scope for a shell tool — belongs in a dedicated git workflow tool or IDE integration |
| Config TUI | First-time setup via interactive prompts is sufficient for v1; a full TUI would require a curses/textual rewrite of the config layer |
