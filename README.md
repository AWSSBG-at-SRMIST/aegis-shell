<p align="center">
  <img src="assets/icon.ico" alt="Aegis Shell" width="64" height="64">
</p>

<h1 align="center">Aegis Shell</h1>

<p align="center">
  <strong>An AI-powered developer shell that runs any command, on any OS, and fixes what breaks — automatically.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Groq-F55036?style=flat-square" alt="Groq">
  <img src="https://img.shields.io/badge/Llama_3.3_70B-8B5CF6?style=flat-square" alt="Llama 3.3 70B">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square" alt="Platform">
  <img src="https://img.shields.io/badge/license-GPL--3.0-blue?style=flat-square" alt="License">
</p>

---

## What is Aegis Shell?

Aegis Shell is a cross-platform AI-powered terminal shell that bridges the gap between developer intent and OS execution. It understands natural language alongside real shell commands, diagnoses failures automatically with an AI model, and resolves dependency gaps without leaving the prompt. Where a standard shell surfaces an error and stops, Aegis surfaces the root cause, proposes a fix, and — with one keypress confirmation — applies it and replays the original command.

The goal is to reduce the friction and error rate in developer workflows: less time context-switching to documentation or Stack Overflow, more time delivering. For engineering teams onboarding to unfamiliar environments or operating across mixed Windows/macOS/Linux setups, Aegis provides a consistent, safe command surface with built-in sensitive-data protection.

---

## What you get

- **Natural language to shell** — Type "compress this folder" or "show running ports" and Aegis translates it to the correct OS-native command before running it. Works on PowerShell, CMD, Bash, and Zsh without configuration.
- **AI error diagnosis** — When any command fails, Groq (Llama 3.3-70B) diagnoses the stderr and surfaces a `FIX:` command the user can accept with one keypress. Reduces mean-time-to-resolution for common environment errors.
- **Auto-install unknown tools** — Missing binary detected; the LLM identifies the correct package manager and package name, asks for confirmation, installs it, and replays the original command. Eliminates the most common onboarding blocker on new machines.
- **Encrypted secret manager** — Store API keys, tokens, and credentials with Fernet AES-128 encryption. Expand them inline as `$SECRET:NAME` in any command without ever exposing the plaintext in shell history.
- **Sensitive data guard** — Scans every command before execution and warns if it contains a password, token, or key pattern. Acts as a last-line-of-defence against accidental credential exposure.

---

## Business Impact

| Stakeholder | Problem Solved |
|---|---|
| Individual developers | Eliminate documentation lookups for command syntax across platforms |
| Engineering teams | Consistent shell behaviour across Windows, macOS, and Linux reduces environment-specific bugs |
| DevOps / IT | Auto-install removes the need to maintain per-OS onboarding scripts |
| Security-conscious orgs | Credential guard and encrypted secret store reduce the risk of accidental secret exposure in logs or history |
| New hires / interns | Natural language input lowers the barrier to contributing on day one |

---

## Stack

| Layer | Tech |
|---|---|
| Runtime | Python 3.9+ |
| Shell UI | prompt_toolkit 3.x (history, autocomplete, ANSI prompt) |
| AI / LLM | Groq API · Llama 3.3-70B (default), Llama-3-8B, Mixtral-8x7B |
| Encryption | cryptography · Fernet (AES-128-CBC + HMAC) |
| System info | psutil |
| Platform | Windows · macOS · Linux |
| Packaging | setuptools · pyproject.toml · pip-installable (`aegis` entrypoint) |

---

## Engineering Decisions

**Why Groq over OpenAI/Anthropic?**
Groq's inference is significantly faster for small prompts (sub-second on most queries), and the free-tier quota is generous for interactive use. Latency matters in a shell — a 3-second wait for a diagnosis kills the developer's flow state. The Llama 3.3-70B model quality is sufficient for command classification and error diagnosis, and the open-weight nature of the underlying model reduces vendor lock-in risk for enterprise deployments.

**Why translate commands to OS-native shell dialects rather than using WSL?**
WSL is not installed on most Windows machines and requires admin setup that many enterprise IT environments restrict. Aegis detects whether a command is PowerShell, CMD, or a Unix idiom and routes it to the appropriate interpreter automatically, making it deployable on a fresh corporate Windows machine with zero prerequisites and no IT escalation.

**Why Fernet for secrets over OS keychain?**
OS keychain APIs differ across platforms and require elevated permissions or GUI frameworks on some systems. Fernet gives AES-128 encryption with a file-based key stored at `~/.aegis/.key` (chmod 600 where supported), keeping the implementation pure-Python and cross-platform. The tradeoff — the key file must be protected at the OS level — is explicitly documented and acceptable for developer-workstation use cases.

**What would you do differently in v2?**
Add streaming output for long-running AI calls (currently the LLM call blocks until complete), replace the regex-based sensitive-data scanner with a proper token classifier to reduce false negatives, and add Azure AD integration for teams that want centralised secret management rather than per-user key files.

---

## Risk Register

| Risk | Mitigation |
|---|---|
| Accidental credential exposure in shell history | Sensitive data guard scans every command pre-execution; secret store expands tokens inline without writing plaintext to history |
| AI-suggested fix commands causing unintended side effects | Every fix requires explicit one-keypress confirmation; destructive operations are flagged with a warning prefix |
| Cross-platform command routing failure | Platform detection runs at shell startup; unrecognised commands fall back to the system default interpreter |
| Encrypted key file loss | Documented recovery path: re-generate key, re-enter secrets. Key derivation from a passphrase is a v2 candidate |
| LLM hallucinating incorrect package names | Auto-install requires user confirmation before executing; the shell prints the exact install command for review |

---

## Docs

| Document | Description |
|---|---|
| [PRD](docs/PRD.md) | Product requirements — goals, user stories, non-goals |
| [Architecture](docs/ARCHITECTURE.md) | System design, data flow, component breakdown |
| [Decisions](docs/DECISIONS.md) | Every major technical decision and why |
| [Setup](docs/SETUP.md) | Local dev setup, env vars, deployment |

---

## Author

**Tanish Poddar** — [tanisheesh.in](https://tanisheesh.in) · [LinkedIn](https://linkedin.com/in/tanisheesh) · [GitHub](https://github.com/tanisheesh)
