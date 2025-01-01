# Local Setup — Aegis Shell

> This guide is for running Aegis Shell locally or self-hosting it.
> Aegis is a local CLI tool — there is no hosted demo URL.

---

## Prerequisites

- Python 3.9+
- pip
- A free [Groq account](https://console.groq.com/keys) for the AI features (the API key is set interactively on first run)

---

## 1. Clone and install

```bash
git clone https://github.com/tanisheesh/aegis-shell
cd aegis-shell

# Recommended: use a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run directly
python aegis_shell.py
```

Alternatively, install as a package so the `aegis` command is available anywhere:

```bash
pip install -e .
aegis
```

---

## 2. First-time setup

On first launch, Aegis runs an interactive setup:

1. Choose a Groq model (default: `llama-3.3-70b-versatile`)
2. Enter your Groq API key (get one free at [console.groq.com/keys](https://console.groq.com/keys))

Aegis validates the key immediately and encrypts it with Fernet before saving to `~/.aegis/config.json`. The encryption key is stored at `~/.aegis/.key`.

---

## 3. Environment variables

Aegis does not use a `.env` file for its own configuration — everything is stored in `~/.aegis/`. No environment variables are required to run the shell.

If you want to store your own project secrets inside Aegis's encrypted vault:

```bash
# Inside the aegis prompt
secret set MY_KEY sk-xxxxxxxx
# Expand inline in any command
curl -H "Authorization: Bearer $SECRET:MY_KEY" https://api.example.com
```

---

## 4. Platform-specific installers

### Windows

```powershell
# Run from an elevated PowerShell prompt
.\install.ps1
```

The script creates a virtualenv, installs dependencies, and registers `aegis` on the user PATH.

### macOS / Linux

```bash
chmod +x install.sh
./install.sh
```

---

## 5. Standalone executable (PyInstaller)

```bash
pip install pyinstaller
python build_installer.py
```

Produces a single-file executable in `dist/` — no Python installation required on the target machine.

---

## 6. Run locally (development mode)

```bash
python aegis_shell.py
```

Aegis Shell will start at the interactive REPL prompt. Type `help` to see all built-in commands.

---

## 7. Reset configuration

To start fresh (re-run first-time setup):

```bash
rm -rf ~/.aegis
python aegis_shell.py
```

Or on Windows:

```powershell
Remove-Item -Recurse -Force "$env:USERPROFILE\.aegis"
python aegis_shell.py
```

---

## Known local-only limitations

- Groq API requires an internet connection — AI features are unavailable offline, but the shell continues to run commands normally.
- On Windows, `chmod` is not supported; the `.key` file relies on user-profile ACLs for protection instead.
- The `install.sh` / `install.ps1` scripts assume the user has write access to their home directory and that Python 3.9+ is already on PATH.

---

## Author

**Tanish Poddar** — [tanisheesh.in](https://tanisheesh.in) · [LinkedIn](https://linkedin.com/in/tanisheesh) · [GitHub](https://github.com/tanisheesh)
