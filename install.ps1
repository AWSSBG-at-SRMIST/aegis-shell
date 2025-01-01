# Aegis Shell — Windows Installer
# Usage: irm https://raw.githubusercontent.com/tanishpoddar/aegis-shell/main/install.ps1 | iex

$ErrorActionPreference = 'Stop'

$REPO_URL    = 'https://github.com/tanishpoddar/aegis-shell.git'
$ZIP_URL     = 'https://github.com/tanishpoddar/aegis-shell/archive/refs/heads/main.zip'
$INSTALL_DIR = Join-Path $env:USERPROFILE '.aegis-shell'
$BIN_DIR     = Join-Path $env:USERPROFILE '.local\bin'
$TOTAL       = 4

# ── Helpers ───────────────────────────────────────────────────────────────────
function Write-Banner {
    Write-Host ""
    Write-Host "  ╔════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║                                                ║" -ForegroundColor Cyan
    Write-Host "  ║   " -ForegroundColor Cyan -NoNewline
    Write-Host "⚔   A E G I S   S H E L L   ⚔" -ForegroundColor White -NoNewline
    Write-Host "            ║" -ForegroundColor Cyan
    Write-Host "  ║                                                ║" -ForegroundColor Cyan
    Write-Host "  ║   AI-powered terminal. Run anything.           ║" -ForegroundColor Cyan
    Write-Host "  ║   Tanish · Nidhi · Nishant  ·  SRMIST         ║" -ForegroundColor Cyan
    Write-Host "  ║                                                ║" -ForegroundColor Cyan
    Write-Host "  ╚════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step($n, $msg) {
    Write-Host "  " -NoNewline
    Write-Host "[$n/$TOTAL]" -ForegroundColor Cyan -NoNewline
    Write-Host "  $msg"
}
function Write-Ok($msg)   { Write-Host "  " -NoNewline; Write-Host "✓" -ForegroundColor Green  -NoNewline; Write-Host "  $msg" }
function Write-Fail($msg) { Write-Host "  " -NoNewline; Write-Host "✗" -ForegroundColor Red    -NoNewline; Write-Host "  $msg" }
function Write-Warn($msg) { Write-Host "  " -NoNewline; Write-Host "!" -ForegroundColor Yellow -NoNewline; Write-Host "  $msg" }

function Die($msg) {
    Write-Fail $msg
    Write-Host ""
    exit 1
}

# ── Preflight ─────────────────────────────────────────────────────────────────
function Check-Requirements {
    Write-Host "  Checking requirements..." -ForegroundColor White
    Write-Host ""

    # Python
    $script:PythonCmd = $null
    foreach ($cmd in @('python', 'python3', 'py')) {
        try {
            $ver = & $cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
            if ($ver -match '^(\d+)\.(\d+)$') {
                if ([int]$Matches[1] -ge 3 -and [int]$Matches[2] -ge 9) {
                    $script:PythonCmd = $cmd
                    Write-Ok "Python $ver found"
                    break
                } else {
                    # Offer winget install
                    Write-Fail "Python $ver found — 3.9+ required"
                    Write-Host "    Fix: " -NoNewline; Write-Host "https://python.org/downloads" -ForegroundColor Cyan
                    if (Get-Command winget -ErrorAction SilentlyContinue) {
                        $ans = Read-Host "    Install Python 3.12 via winget now? (y/N)"
                        if ($ans -ieq 'y') {
                            winget install Python.Python.3.12 --silent
                            Write-Warn "Restart this script in a new terminal after Python installs."
                        }
                    }
                    exit 1
                }
            }
        } catch {}
    }
    if (-not $script:PythonCmd) {
        Write-Fail "Python not found"
        Write-Host "    Fix: " -NoNewline; Write-Host "https://python.org/downloads" -ForegroundColor Cyan
        if (Get-Command winget -ErrorAction SilentlyContinue) {
            $ans = Read-Host "    Install Python 3.12 via winget now? (y/N)"
            if ($ans -ieq 'y') { winget install Python.Python.3.12 --silent }
        }
        exit 1
    }

    # pip
    try {
        & $script:PythonCmd -m pip --version | Out-Null
        Write-Ok "pip found"
    } catch {
        Die "pip not found — run: $script:PythonCmd -m ensurepip --upgrade"
    }

    # git (optional)
    $script:HasGit = [bool](Get-Command git -ErrorAction SilentlyContinue)
    if ($script:HasGit) { Write-Ok "git found" } else { Write-Warn "git not found — will use zip download" }

    Write-Host ""
}

# ── Download ──────────────────────────────────────────────────────────────────
function Download-Source {
    Write-Step 1 "Downloading source..."

    if ($script:HasGit -and (Test-Path (Join-Path $INSTALL_DIR '.git'))) {
        git -C $INSTALL_DIR pull --quiet
        Write-Ok "Updated existing install"

    } elseif ($script:HasGit) {
        git clone --quiet --depth=1 $REPO_URL $INSTALL_DIR
        Write-Ok "Cloned to $INSTALL_DIR"

    } else {
        $TmpZip = Join-Path $env:TEMP 'aegis-install.zip'
        $TmpDir = Join-Path $env:TEMP 'aegis-extract'
        Invoke-WebRequest -Uri $ZIP_URL -OutFile $TmpZip -UseBasicParsing
        if (Test-Path $TmpDir) { Remove-Item $TmpDir -Recurse -Force }
        Expand-Archive -Path $TmpZip -DestinationPath $TmpDir -Force
        $extracted = Get-ChildItem $TmpDir | Select-Object -First 1
        if (Test-Path $INSTALL_DIR) { Remove-Item $INSTALL_DIR -Recurse -Force }
        Move-Item $extracted.FullName $INSTALL_DIR
        Remove-Item $TmpZip, $TmpDir -Recurse -Force -ErrorAction SilentlyContinue
        Write-Ok "Downloaded to $INSTALL_DIR"
    }
}

# ── Dependencies ──────────────────────────────────────────────────────────────
function Install-Deps {
    Write-Step 2 "Installing dependencies..."
    & $script:PythonCmd -m pip install --quiet --upgrade pip
    & $script:PythonCmd -m pip install --quiet -r (Join-Path $INSTALL_DIR 'requirements.txt')
    Write-Ok "Dependencies installed"
}

# ── Launcher ──────────────────────────────────────────────────────────────────
function Create-Launcher {
    Write-Step 3 "Creating launcher..."
    New-Item -ItemType Directory -Force -Path $BIN_DIR | Out-Null

    $ScriptPath   = Join-Path $INSTALL_DIR 'aegis_shell.py'
    $LauncherPath = Join-Path $BIN_DIR 'aegis.bat'

    @"
@echo off
"$($script:PythonCmd)" "$ScriptPath" %*
"@ | Set-Content $LauncherPath -Encoding ASCII

    # Add BIN_DIR to user PATH
    $userPath = [Environment]::GetEnvironmentVariable('PATH', 'User') ?? ''
    if ($userPath -notlike "*$BIN_DIR*") {
        [Environment]::SetEnvironmentVariable('PATH', "$BIN_DIR;$userPath", 'User')
        Write-Ok "Added $BIN_DIR to user PATH"
    }
    Write-Ok "Launcher → $LauncherPath"
}

# ── Verify ────────────────────────────────────────────────────────────────────
function Verify-Install {
    Write-Step 4 "Verifying install..."
    $escaped = $INSTALL_DIR -replace '\\', '\\\\'
    try {
        & $script:PythonCmd -c "import sys; sys.path.insert(0,'$escaped'); import aegis_shell" 2>$null
        Write-Ok "Aegis Shell is working"
    } catch {
        Write-Warn "Verification inconclusive — try 'aegis' in a new terminal"
    }
}

# ── Done ──────────────────────────────────────────────────────────────────────
function Print-Done {
    Write-Host ""
    Write-Host "  ────────────────────────────────────────────────" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  " -NoNewline; Write-Host "✓  Aegis Shell installed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Open a new terminal and run:"
    Write-Host ""
    Write-Host "      aegis" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  ────────────────────────────────────────────────" -ForegroundColor Cyan
    Write-Host "  Docs     " -NoNewline; Write-Host "github.com/tanishpoddar/aegis-shell" -ForegroundColor Cyan
    Write-Host "  Issues   " -NoNewline; Write-Host "github.com/tanishpoddar/aegis-shell/issues" -ForegroundColor Cyan
    Write-Host "  Update   " -NoNewline; Write-Host "aegis update" -ForegroundColor Cyan
    Write-Host "  ────────────────────────────────────────────────" -ForegroundColor Cyan
    Write-Host ""
}

# ── Main ──────────────────────────────────────────────────────────────────────
Write-Banner
Check-Requirements
Write-Host "  Installing Aegis Shell..." -ForegroundColor White
Write-Host ""
Download-Source
Install-Deps
Create-Launcher
Verify-Install
Print-Done
