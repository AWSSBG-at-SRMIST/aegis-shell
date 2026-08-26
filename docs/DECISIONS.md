# Engineering Decisions — Aegis Shell

Every decision here follows the same format: what the situation was, what I chose, why I chose it, and what I gave up. This is the reasoning I'd walk through with a technical interviewer or a stakeholder asking "why is it built this way?"

---

## Decision 1 — Groq over OpenAI or Anthropic

**The situation:** Aegis needs an AI model for three interactive tasks inside a live terminal session: classify whether the user typed a real command or plain English, diagnose an error when a command fails, and identify what an unknown tool is and how to install it. Multiple providers were available: OpenAI (GPT-4o), Anthropic (Claude), and Groq.

**What I chose:** Groq with Llama 3.3-70B as the default model, with Llama-3-8B and Mixtral-8x7B as user-configurable alternatives.

**Why:** Latency is the critical constraint in a shell. If the AI response takes 3 seconds, it breaks the developer's flow — the shell feels slow rather than helpful. Groq's inference hardware delivers sub-second responses for the short prompts Aegis uses (most calls are under 200 tokens). The free tier quota is sufficient for single-user interactive use without requiring a credit card, which matters for a tool that runs locally on a developer's machine. Llama 3.3-70B's quality is more than sufficient for these structured tasks — they are command classification and error diagnosis, not open-ended generation.

From a delivery standpoint, choosing a provider that works on the free tier means Aegis has zero cost to the end user and zero risk of surprise billing — which is the right constraint for a local developer tool.

**What I gave up:** Groq's free tier has stricter rate limits than a paid OpenAI plan. On heavy use (many command failures in one session) the user could hit rate limits. This is acceptable because the shell degrades gracefully — if the AI call fails or times out, Aegis runs the command as-is rather than crashing.

---

## Decision 2 — Route to OS-native shell dialects rather than forcing everything through one shell

**The situation:** Developers type commands that assume their usual environment. On Windows, a user might type `ls`, `Get-Process`, `dir`, `python script.py`, or `npm install` in the same session — each of these needs a different interpreter. Forcing everything through PowerShell or CMD causes failures and confusion.

**What I chose:** A `router.py` module that classifies each command into one of six dialects — `powershell`, `cmd`, `unix_on_windows`, `direct`, `script`, `unknown` — and builds the correct subprocess argument list for each.

**Why:** Automatic dialect routing means the user never thinks about which shell to use. They just type. `dir` goes to `cmd /c`, `Get-Process` goes to `PowerShell -Command`, `ls` on Windows gets translated to `dir` automatically, and `pip install` runs as a direct subprocess. This covers the vast majority of real developer commands without any configuration.

The key constraint I was designing around: Aegis needs to work on a fresh corporate Windows machine without admin rights and without WSL installed. Routing to native interpreters was the only approach that met this constraint.

**What I gave up:** The dialect classifier uses heuristics (PowerShell Verb-Noun pattern, CMD built-in list, known Unix command set) and will occasionally misclassify unusual commands. Unknown commands default to PowerShell on Windows, which is correct most of the time but wrong for some CMD-only scripts. A v2 improvement would be to ask the LLM to classify ambiguous cases.

---

## Decision 3 — Fernet file-based encryption for secrets, not the OS keychain

**The situation:** Aegis stores the user's Groq API key and any other named secrets they add. The standard alternative would be the OS keychain: Windows Credential Manager, macOS Keychain, or libsecret on Linux.

**What I chose:** Fernet symmetric encryption (from Python's `cryptography` package) with a key file stored at `~/.aegis/.key`.

**Why:** OS keychain APIs are inconsistent across platforms. macOS Keychain works well but requires the `keyring` package or the `security` CLI. Windows Credential Manager behaves differently across Python versions. libsecret on Linux requires D-Bus and is not available in minimal Docker images or CI environments. Any one of these would be a platform-specific dependency — which breaks the "runs identically on Windows, macOS, and Linux" requirement.

Fernet gives AES-128-CBC with HMAC-SHA256 — strong enough for API keys stored on a personal workstation. The implementation is pure Python, cross-platform, and has no external system dependencies.

**What I gave up:** The encryption key is a file on disk. If an attacker has read access to the user's home directory, they can read both the key and the ciphertext. This is the same threat model as the OS keychain on most consumer machines without hardware-backed secure storage. `chmod 600` is applied to the key file where the OS supports it; on Windows, user-profile ACLs provide equivalent protection.

---

## Decision 4 — Auto-diagnose every failed command, not wait for the user to ask

**The situation:** When a command returns a non-zero exit code, the user's typical next step is to copy the error message and search the web. I could either auto-trigger diagnosis every time a command fails, or make the user type `diagnose` to ask for help.

**What I chose:** Auto-trigger on every failure. The AI diagnosis runs immediately and surfaces a `FIX:` command the user can accept with one keypress — no extra command required.

**Why:** The vast majority of command failures in a developer shell are genuine errors the user wants fixed — not intentional non-zero exits. Requiring a separate `diagnose` command adds friction at exactly the moment the user is most frustrated. The Groq call is fast (under 2 seconds), the output is short, and — critically — the `FIX:` command still requires explicit confirmation before it runs. So the auto-trigger adds no execution risk: the AI cannot do anything without user approval.

This is a "reduce time to resolution" decision. The goal was to compress the error → fix → retry loop from minutes (copy error, open browser, read Stack Overflow, try fix, retry) to seconds (one keypress).

**What I gave up:** Some scripts intentionally return non-zero to signal "not found" or "nothing matched" — these will trigger diagnosis unnecessarily, producing noise. A v2 improvement would be to skip diagnosis when stderr is empty, since deliberate non-zero exits usually produce no error output.

---

## What I'd change in v2

**Streaming AI responses** — current Groq calls block until the full response arrives. For the `plan` command, which generates 5–8 steps, the 1–2 second wait is noticeable. Streaming tokens as they arrive would make the shell feel significantly more responsive.

**Replace the regex sensitive-data scanner with a token classifier** — the current regex approach catches known patterns (Groq `gsk_`, OpenAI `sk-`, GitHub `ghp_`) but misses custom API key formats and produces false positives on some data strings. A small classifier trained on common secret formats would be more accurate and less noisy.

**Azure AD / Entra ID integration for secret management** — for teams that want centralised credential management rather than per-user key files, integrating with a managed identity provider would allow Aegis to pull secrets from an enterprise vault (Azure Key Vault, HashiCorp Vault) at runtime rather than storing them locally.

**Persist session variables across restarts** — `$VAR = value` assignments currently live only in memory. A lightweight persist layer would make session variables genuinely useful for long-running workflows across multiple terminal sessions.
