import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
from setuptools import setup

def check_requirements():
    """Check if all required files exist"""
    required_files = [
        'requirements.txt',
        'README.md',
        'LICENSE',
        'installer.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
            
    if missing_files:
        print("Warning: The following required files are missing:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    return True

def create_icon():
    """Create a default icon if none exists"""
    assets_dir = Path('assets')
    icon_path = assets_dir / 'icon.ico' if platform.system() == 'Windows' else assets_dir / 'icon.icns'
    
    if not assets_dir.exists():
        assets_dir.mkdir()
        
    if not icon_path.exists():
        print(f"Warning: No {icon_path.name} found in assets directory")
        print("Building without icon...")
        return False
    return True

def build_installer():
    """Build the installer using PyInstaller"""
    try:
        # Check requirements
        if not check_requirements():
            print("Please create the missing files before building")
            return False
            
        # Check/create icon
        has_icon = create_icon()
        
        # Install PyInstaller if not already installed
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        
        # Prepare PyInstaller command
        system = platform.system()
        if system == 'Windows':
            cmd = [
                'pyinstaller',
                '--name=AegisShell',
                '--onefile',
                '--windowed',
                '--add-data=requirements.txt;.',
                '--add-data=README.md;.',
                '--add-data=LICENSE;.'
            ]
            if has_icon:
                cmd.append('--icon=assets/icon.ico')
        elif system == 'Darwin':  # macOS
            cmd = [
                'pyinstaller',
                '--name=AegisShell',
                '--onefile',
                '--windowed',
                '--add-data=requirements.txt:.',
                '--add-data=README.md:.',
                '--add-data=LICENSE:.'
            ]
            if has_icon:
                cmd.append('--icon=assets/icon.icns')
        else:
            print(f"Unsupported operating system: {system}")
            return False
            
        # Add main script
        cmd.append('installer.py')
        
        # Build the installer
        subprocess.check_call(cmd)
        
        print("\nInstaller built successfully!")
        print("You can find the installer in the 'dist' directory")
        
        # Create platform-specific package
        if system == 'Windows':
            create_windows_package()
        elif system == 'Darwin':
            create_mac_package()
            
        return True
    except Exception as e:
        print(f"Error building installer: {e}")
        return False

def create_windows_package():
    """Create Windows installer package"""
    try:
        # Create release directory
        release_dir = Path('release/windows')
        release_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy files
        shutil.copy2('dist/AegisShell.exe', release_dir)
        shutil.copy2('README.md', release_dir)
        shutil.copy2('LICENSE', release_dir)
        
        # Create zip file
        shutil.make_archive('AegisShell-Windows', 'zip', release_dir)
        print("Windows package created: AegisShell-Windows.zip")
    except Exception as e:
        print(f"Error creating Windows package: {e}")

def create_mac_package():
    """Create Mac installer package"""
    try:
        # Create release directory
        release_dir = Path('release/mac')
        release_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy files
        shutil.copy2('dist/AegisShell', release_dir)
        shutil.copy2('README.md', release_dir)
        shutil.copy2('LICENSE', release_dir)
        
        # Create zip file
        shutil.make_archive('AegisShell-Mac', 'zip', release_dir)
        print("Mac package created: AegisShell-Mac.zip")
    except Exception as e:
        print(f"Error creating Mac package: {e}")

if __name__ == "__main__":
    build_installer() 