#!/usr/bin/env bash
# Aegis Shell — Linux/Mac Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/tanishpoddar/aegis-shell/main/install.sh | bash

set -euo pipefail

REPO_URL="https://github.com/tanishpoddar/aegis-shell.git"
ZIP_URL="https://github.com/tanishpoddar/aegis-shell/archive/refs/heads/main.zip"
INSTALL_DIR="$HOME/.aegis-shell"
TOTAL_STEPS=4

# ── Colours ───────────────────────────────────────────────────────────────────
CY='\033[0;36m'; GR='\033[0;32m'; RD='\033[0;31m'
YL='\033[1;33m'; BD='\033[1m';    RS='\033[0m'

banner() {
  echo ""
  echo -e "${CY}  ╔════════════════════════════════════════════════╗${RS}"
  echo -e "${CY}  ║                                                ║${RS}"
  echo -e "${CY}  ║   ${BD}⚔   A E G I S   S H E L L   ⚔${RS}${CY}            ║${RS}"
  echo -e "${CY}  ║                                                ║${RS}"
  echo -e "${CY}  ║   ${RS}AI-powered terminal. Run anything.${CY}            ║${RS}"
  echo -e "${CY}  ║   ${RS}Tanish · Nidhi · Nishant  ·  SRMIST${CY}          ║${RS}"
  echo -e "${CY}  ║                                                ║${RS}"
  echo -e "${CY}  ╚════════════════════════════════════════════════╝${RS}"
  echo ""
}

step() { echo -e "  ${CY}[$1/$TOTAL_STEPS]${RS}  $2"; }
ok()   { echo -e "  ${GR}✓${RS}  $1"; }
fail() { echo -e "  ${RD}✗${RS}  $1"; }
warn() { echo -e "  ${YL}!${RS}  $1"; }
die()  { fail "$1"; echo ""; exit 1; }

# ── Preflight ─────────────────────────────────────────────────────────────────
check_requirements() {
  echo -e "  ${BD}Checking requirements...${RS}"; echo ""

  # Python
  PYTHON=""
  for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
      ver=$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
      maj=${ver%%.*}; min=${ver##*.}
      if [ "$maj" -ge 3 ] && [ "$min" -ge 9 ]; then
        PYTHON="$cmd"
        ok "Python $ver"; break
      else
        die "Python $ver found — 3.9+ required. Fix: https://python.org/downloads"
      fi
    fi
  done
  [ -z "$PYTHON" ] && die "Python not found. Fix: https://python.org/downloads"

  # pip
  "$PYTHON" -m pip --version &>/dev/null \
    && ok "pip found" \
    || die "pip missing. Fix: $PYTHON -m ensurepip --upgrade"

  # git (optional — fallback to curl+unzip)
  HAS_GIT=false
  command -v git &>/dev/null && HAS_GIT=true && ok "git found" || warn "git not found — will use zip download"

  echo ""
}

# ── Download ──────────────────────────────────────────────────────────────────
download_source() {
  step 1 "Downloading source..."

  if [ -d "$INSTALL_DIR/.git" ]; then
    git -C "$INSTALL_DIR" pull --quiet
    ok "Updated existing install at $INSTALL_DIR"

  elif $HAS_GIT; then
    git clone --quiet --depth=1 "$REPO_URL" "$INSTALL_DIR"
    ok "Cloned to $INSTALL_DIR"

  else
    command -v curl &>/dev/null || die "curl not found — install git or curl and retry"
    TMP_ZIP=$(mktemp /tmp/aegis-XXXXXX.zip)
    TMP_DIR=$(mktemp -d /tmp/aegis-XXXXXX)

    curl -fsSL "$ZIP_URL" -o "$TMP_ZIP"
    command -v unzip &>/dev/null || die "unzip not found — install git or unzip and retry"

    unzip -q "$TMP_ZIP" -d "$TMP_DIR"
    [ -d "$INSTALL_DIR" ] && rm -rf "$INSTALL_DIR"
    mv "$TMP_DIR"/aegis-shell-main "$INSTALL_DIR"
    rm -rf "$TMP_DIR" "$TMP_ZIP"
    ok "Downloaded to $INSTALL_DIR"
  fi
}

# ── Dependencies ──────────────────────────────────────────────────────────────
install_deps() {
  step 2 "Installing dependencies..."
  "$PYTHON" -m pip install --quiet --upgrade pip
  "$PYTHON" -m pip install --quiet -r "$INSTALL_DIR/requirements.txt"
  ok "Dependencies installed"
}

# ── Launcher ──────────────────────────────────────────────────────────────────
create_launcher() {
  step 3 "Creating launcher..."

  BIN_DIR=""
  for d in "/usr/local/bin" "$HOME/.local/bin" "$HOME/bin"; do
    if [ -w "$d" ] 2>/dev/null || mkdir -p "$d" 2>/dev/null; then
      BIN_DIR="$d"; break
    fi
  done
  [ -z "$BIN_DIR" ] && die "No writable bin directory found"

  cat > "$BIN_DIR/aegis" <<LAUNCHER
#!/usr/bin/env bash
exec "$PYTHON" "$INSTALL_DIR/aegis_shell.py" "\$@"
LAUNCHER
  chmod +x "$BIN_DIR/aegis"

  # Add to shell rc if needed
  for RC in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.bash_profile" "$HOME/.profile"; do
    if [ -f "$RC" ]; then
      grep -q "$BIN_DIR" "$RC" 2>/dev/null || echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$RC"
      break
    fi
  done

  ok "Launcher → $BIN_DIR/aegis"
}

# ── Verify ────────────────────────────────────────────────────────────────────
verify() {
  step 4 "Verifying install..."
  if "$PYTHON" -c "import sys; sys.path.insert(0,'$INSTALL_DIR'); import aegis_shell" 2>/dev/null; then
    ok "Aegis Shell is working"
  else
    warn "Verification inconclusive — try running 'aegis' in a new terminal"
  fi
}

# ── Done ──────────────────────────────────────────────────────────────────────
print_done() {
  echo ""
  echo -e "${CY}  ────────────────────────────────────────────────${RS}"
  echo ""
  echo -e "  ${GR}${BD}✓  Aegis Shell installed successfully!${RS}"
  echo ""
  echo -e "  Open a new terminal and run:"
  echo ""
  echo -e "      ${BD}${CY}aegis${RS}"
  echo ""
  echo -e "${CY}  ────────────────────────────────────────────────${RS}"
  echo -e "  Docs     ${CY}github.com/tanishpoddar/aegis-shell${RS}"
  echo -e "  Issues   ${CY}github.com/tanishpoddar/aegis-shell/issues${RS}"
  echo -e "  Update   ${CY}aegis update${RS}"
  echo -e "${CY}  ────────────────────────────────────────────────${RS}"
  echo ""
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
  banner
  check_requirements
  echo -e "  ${BD}Installing Aegis Shell...${RS}"; echo ""
  download_source
  install_deps
  create_launcher
  verify
  print_done
}

main
