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

Aegis Shell is a replacement terminal shell for developers that understands natural language alongside real shell commands. When a command fails, it diagnoses the error with AI and offers a one-keystroke fix. When a tool is missing, it identifies the right package, asks permission, installs it, and re-runs your original command — all without leaving the prompt. It is the shell that removes friction between your intent and execution.

---

## What you get

- **Natural language to shell** — type "compress this folder" or "show running ports" and Aegis translates it to the correct OS-native command before running it
- **AI error diagnosis** — when any command fails, Groq (Llama 3.3-70B) diagnoses the stderr and surfaces a `FIX:` command you can accept with one keypress
- **Auto-install unknown tools** — missing binary detected, LLM identifies the right package manager and package, installs on confirmation, then replays your original command
- **Encrypted secret manager** — store API keys and tokens with Fernet AES-128, expand them inline as `$SECRET:NAME` in any command
- **Sensitive data guard** — scans every command before execution and warns if it contains a password, token, or key pattern

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
Groq's inference is significantly faster for small prompts (sub-second on most queries), free-tier quota is generous for interactive use, and the Llama 3.3-70B model quality is sufficient for command classification and error diagnosis. Latency matters in a shell — a 3s wait for a diagnosis kills the flow.

**Why translate commands to OS-native shell dialects rather than using WSL?**
WSL is not installed on most Windows machines and requires admin setup. Aegis detects whether a command is PowerShell, CMD, or a Unix idiom and routes it to the appropriate interpreter automatically, so it works on a fresh Windows install with zero prerequisites.

**Why Fernet for secrets over OS keychain?**
OS keychain APIs differ across platforms and require elevated permissions or GUI frameworks on some systems. Fernet gives AES-128 encryption with a file-based key stored at `~/.aegis/.key` (chmod 600 where supported), keeping the implementation pure-Python and cross-platform.

**What would you do differently in v2?**
Add streaming output for long-running AI calls (currently the LLM call blocks until complete), and replace the regex-based sensitive-data scanner with a proper token classifier to reduce false negatives.

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
