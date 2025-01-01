"""
Build script for creating standalone Aegis Shell installers
"""
import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        return True
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        return True

def clean_build_dirs():
    """Clean previous build directories"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}...")
            shutil.rmtree(dir_name)
    
    # Clean .spec files
    for spec_file in Path('.').glob('*.spec'):
        if spec_file.name != 'AegisShell.spec':
            spec_file.unlink()

def create_spec_file():
    """Create PyInstaller spec file"""
    system = platform.system()
    
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['aegis_shell.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('resources', 'resources'),
        ('README.md', '.'),
        ('LICENSE', '.'),
    ],
    hiddenimports=[
        'colorama',
        'prompt_toolkit',
        'psutil',
        'watchdog',
        'requests',
        'cryptography',
        'typing_extensions',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='aegis-shell',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
"""
    
    if system == 'Windows':
        spec_content += "    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,\n"
    elif system == 'Darwin':
        spec_content += "    icon='assets/icon.icns' if os.path.exists('assets/icon.icns') else None,\n"
    
    spec_content += ")\n"
    
    with open('AegisShell.spec', 'w') as f:
        f.write(spec_content)
    
    print("Created AegisShell.spec file")

def build_executable():
    """Build the executable using PyInstaller"""
    print("\nBuilding executable...")
    
    try:
        subprocess.check_call([
            'pyinstaller',
            '--clean',
            'AegisShell.spec'
        ])
        print("\n✓ Build successful!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed: {e}")
        return False

def create_release_package():
    """Create release package with executable and documentation"""
    system = platform.system()
    
    # Create release directory
    release_dir = Path('release')
    release_dir.mkdir(exist_ok=True)
    
    if system == 'Windows':
        package_name = 'AegisShell-Windows'
    elif system == 'Darwin':
        package_name = 'AegisShell-Mac'
    else:
        package_name = 'AegisShell-Linux'
    
    package_dir = release_dir / package_name
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True)
    
    # Copy executable
    exe_name = 'aegis-shell.exe' if system == 'Windows' else 'aegis-shell'
    exe_path = Path('dist') / exe_name
    
    if exe_path.exists():
        shutil.copy2(exe_path, package_dir / exe_name)
        print(f"Copied {exe_name} to release package")
    else:
        print(f"Warning: {exe_name} not found in dist/")
        return False
    
    # Copy documentation
    for doc in ['README.md', 'LICENSE']:
        if os.path.exists(doc):
            shutil.copy2(doc, package_dir / doc)
            print(f"Copied {doc} to release package")
    
    # Create installation instructions
    install_instructions = f"""# Aegis Shell Installation

## Quick Start

1. Extract this archive to your desired location
2. Run `{exe_name}` from your terminal
3. On first run, you'll be prompted to enter your OpenRouter API key
4. Get your free API key at: https://openrouter.ai/keys

## Usage

Simply run the executable:
"""
    
    if system == 'Windows':
        install_instructions += """
```cmd
aegis-shell.exe
```

Or add the directory to your PATH to run from anywhere:
```cmd
aegis-shell
```
"""
    else:
        install_instructions += """
```bash
./aegis-shell
```

Or add the directory to your PATH to run from anywhere:
```bash
aegis-shell
```

You may need to make it executable first:
```bash
chmod +x aegis-shell
```
"""
    
    install_instructions += """
## Features

- AI-powered command detection and installation
- Automatic package manager detection
- Cross-platform support
- Secure API key storage

## Support

For issues and questions, visit: https://github.com/tanisheesh/aegis-shell
"""
    
    with open(package_dir / 'INSTALL.md', 'w') as f:
        f.write(install_instructions)
    
    # Create archive
    print(f"\nCreating archive...")
    archive_path = shutil.make_archive(
        str(release_dir / package_name),
        'zip',
        package_dir
    )
    
    print(f"\n✓ Release package created: {archive_path}")
    print(f"  Size: {os.path.getsize(archive_path) / (1024*1024):.2f} MB")
    
    return True

def main():
    """Main build process"""
    print("=" * 60)
    print("Aegis Shell - Standalone Installer Builder")
    print("=" * 60)
    print(f"\nPlatform: {platform.system()}")
    print(f"Python: {sys.version}")
    
    # Check PyInstaller
    if not check_pyinstaller():
        print("Failed to install PyInstaller")
        return 1
    
    # Clean previous builds
    print("\nCleaning previous builds...")
    clean_build_dirs()
    
    # Create spec file
    print("\nCreating build specification...")
    create_spec_file()
    
    # Build executable
    if not build_executable():
        return 1
    
    # Create release package
    print("\nCreating release package...")
    if not create_release_package():
        return 1
    
    print("\n" + "=" * 60)
    print("Build completed successfully!")
    print("=" * 60)
    print("\nYou can find the release package in the 'release' directory")
    print("Distribute the ZIP file to users for easy installation")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
