from colorama import Fore, Style
import subprocess
import importlib
import sys
import time
import os
import re
import platform
import shutil
import tempfile
import zipfile
import urllib.request

# Import the new animator
from utils.download_animation import DownloadAnimator

def is_python_package_installed(package_name):
    """Check if a Python package is installed."""
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False

def get_package_size(package_name, installer="pip"):
    """Get approximate package size in KB (for more realistic progress)"""
    # This is a simplified approach - in a real app, you might want to query
    # package repositories for actual size information
    try:
        if installer == "pip":
            # Get package info but don't show output
            process = subprocess.run(
                ["pip", "search", package_name], 
                capture_output=True, 
                text=True
            )
            # Just return a random reasonable size for demonstration
            return 2048  # 2MB default size
        elif installer == "npm":
            return 5120  # 5MB default size
        elif installer == "winget":
            return 15360  # 15MB default size (apps are larger)
        else:
            return 1024  # 1MB default
    except:
        return 1024  # Default fallback size

def extract_progress_info(line):
    """Extract progress percentage from installer output lines"""
    # For winget style progress
    winget_match = re.search(r'(\d+)%', line)
    if winget_match:
        return int(winget_match.group(1))
    
    # For pip style progress (more complex, simplified here)
    pip_match = re.search(r'Downloading.*\((\d+)/(\d+)\)', line)
    if pip_match:
        current, total = map(int, pip_match.groups())
        return int(current / total * 100)
        
    return None

def get_platform_installer(installer):
    """Get the appropriate installer command based on the platform"""
    system = platform.system().lower()
    
    # Default mapping of generic installer names to platform-specific ones
    installer_map = {
        "windows": {
            "apt": "winget",
            "brew": "winget"
        },
        "darwin": {  # macOS
            "apt": "brew",
            "winget": "brew"
        },
        "linux": {
            "winget": "apt",
            "brew": "apt"
        }
    }
    
    # Get current platform map or empty dict if platform not found
    platform_map = installer_map.get(system, {})
    
    # Return the mapped installer or the original if no mapping exists
    return platform_map.get(installer, installer)

def get_alternative_command(package_name, installer):
    """Get alternative installation commands for common packages"""
    alternatives = {
        "apt": {
            "windows": ["winget install apt-tools"],
            "default": None
        },
        "maven": {
            "windows": ["winget install Apache.Maven", "choco install maven", "manual"],
            "darwin": ["brew install maven"],
            "linux": ["apt install maven", "sudo apt install maven", "manual"]
        },
        "Apache.Maven": {
            "windows": ["choco install maven", "manual"],
            "default": ["manual"]
        }
    }
    
    system = platform.system().lower()
    package_alternatives = alternatives.get(package_name, {})
    
    # Try platform specific alternatives first, then default
    return package_alternatives.get(system, package_alternatives.get("default", []))

def manual_maven_install():
    """Handle manual Maven installation"""
    system = platform.system().lower()
    
    # Verify Java is installed first
    java_installed = False
    try:
        result = subprocess.run(["java", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        java_installed = result.returncode == 0
    except:
        java_installed = False
    
    if not java_installed:
        print(Fore.YELLOW + "[Aegis] Maven requires Java to be installed first.")
        print(Fore.YELLOW + "[Aegis] Please install Java JDK before continuing.")
        
        confirm = input("[Aegis] Would you like to install Java now? (y/N): ").strip().lower()
        if confirm == 'y':
            if system == "windows":
                install_package("Microsoft.OpenJDK.17", "winget")
            elif system == "darwin":  # macOS
                install_package("openjdk", "brew")
            elif system == "linux":
                install_package("default-jdk", "apt")
    
    print(Fore.CYAN + "[Aegis] Starting manual Maven installation...")
    # Maven download URL
    maven_url = "https://dlcdn.apache.org/maven/maven-3/3.9.6/binaries/apache-maven-3.9.6-bin.zip"
    
    # Create temporary folder for download
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "maven.zip")
    
    try:
        # Download Maven
        print(Fore.YELLOW + "[Aegis] Downloading Maven...")
        urllib.request.urlretrieve(maven_url, zip_path)
        
        # Extract to appropriate location based on OS
        print(Fore.YELLOW + "[Aegis] Extracting Maven...")
        
        if system == "windows":
            # For Windows, extract to Program Files
            extract_to = os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"))
        else:
            # For Unix systems, extract to /opt
            extract_to = "/opt" if os.path.exists("/opt") else os.path.expanduser("~")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        
        # Get the extracted folder name
        maven_folder = os.path.join(extract_to, "apache-maven-3.9.6")
        
        # Add to path instructions
        print(Fore.GREEN + "[Aegis] Maven extracted successfully to:", maven_folder)
        print(Fore.YELLOW + "[Aegis] To complete installation, add Maven to your PATH:")
        
        if system == "windows":
            print(Fore.WHITE + f"1. Add {maven_folder}\\bin to your PATH environment variable")
            print(Fore.WHITE + "2. Restart your terminal")
            
            # Offer to add to PATH automatically
            confirm = input("[Aegis] Would you like me to add Maven to PATH now? (y/N): ").strip().lower()
            if confirm == 'y':
                try:
                    # Add to user PATH
                    path_cmd = f'setx PATH "%PATH%;{maven_folder}\\bin"'
                    subprocess.run(path_cmd, shell=True)
                    print(Fore.GREEN + "[Aegis] Maven added to PATH. Please restart your terminal.")
                except Exception as e:
                    print(Fore.RED + f"[Aegis] Error adding to PATH: {e}")
                    print(Fore.YELLOW + "[Aegis] Please add it manually.")
        else:
            # Unix-like systems
            print(Fore.WHITE + f"1. Add the following to your ~/.bashrc or ~/.zshrc:")
            print(Fore.WHITE + f"   export PATH=\"{maven_folder}/bin:$PATH\"")
            print(Fore.WHITE + "2. Run 'source ~/.bashrc' or restart your terminal")
        
        return True
    except Exception as e:
        print(Fore.RED + f"[Aegis] Error during manual installation: {e}")
        return False
    finally:
        # Clean up
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

def handle_winget_error(error_code, package_name):
    """Handle specific winget error codes"""
    error_messages = {
        2316632084: "Installation failed due to winget package not found or repository issues",
        2147942402: "Access denied. Try running as administrator",
        2147943645: "Package is already installed",
        # Add more error codes as needed
    }
    
    message = error_messages.get(error_code, f"Unknown error code: {error_code}")
    print(Fore.YELLOW + f"[Aegis] {message}")
    
    # Special handling for specific packages
    if package_name in ["Apache.Maven", "maven", "mvn"]:
        print(Fore.YELLOW + "[Aegis] Maven can be installed using alternative methods.")
        confirm = input("[Aegis] Would you like to try an alternative installation method? (y/N): ").strip().lower()
        if confirm == 'y':
            alternatives = get_alternative_command(package_name, "winget")
            if "manual" in alternatives:
                return manual_maven_install()
            elif alternatives:
                print(Fore.YELLOW + "[Aegis] Available alternatives:")
                for i, alt in enumerate(alternatives, 1):
                    if alt != "manual":
                        print(f"{i}. {alt}")
                
                choice = input("Select an option: ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(alternatives):
                    alt_cmd = alternatives[int(choice)-1].split()
                    if len(alt_cmd) >= 2:
                        return install_package(alt_cmd[-1], alt_cmd[0])
    
    return False

def install_package(package_name, installer="pip"):
    """Actually install a package using the specified installer with progress animation."""
    print(Fore.YELLOW + f"[Aegis] Preparing to install '{package_name}' using {installer}...")
    
    # Special case for manual Maven installation
    if package_name == "manual" and installer == "manual":
        return manual_maven_install()
    
    # Map installer to platform-appropriate version if needed
    original_installer = installer
    installer = get_platform_installer(installer)
    if original_installer != installer:
        print(Fore.YELLOW + f"[Aegis] Using {installer} instead of {original_installer} on this platform.")
    
    command = []
    if installer == "pip":
        command = ["pip", "install", package_name, "--progress-bar", "on"]
    elif installer == "npm":
        command = ["npm", "install", "-g", package_name]
    elif installer == "winget":
        command = ["winget", "install", package_name]
    elif installer == "apt" and platform.system().lower() == "linux":
        command = ["apt", "install", package_name, "-y"]
    elif installer == "brew" and (platform.system().lower() == "darwin" or 
                                  os.path.exists("/usr/local/bin/brew") or 
                                  os.path.exists("/opt/homebrew/bin/brew")):
        command = ["brew", "install", package_name]
    elif installer == "choco" and platform.system().lower() == "windows":
        command = ["choco", "install", package_name, "-y"]
    elif installer == "manual":
        if package_name == "maven":
            return manual_maven_install()
        else:
            print(Fore.YELLOW + f"[Aegis] No automatic installation available for {package_name}.")
            return False
    else:
        print(Fore.RED + f"[Aegis] Unsupported installer: {installer}")
        
        # Try to find alternatives
        alternatives = get_alternative_command(package_name, installer)
        if alternatives:
            print(Fore.YELLOW + f"[Aegis] Here are alternative installation methods:")
            for i, alt in enumerate(alternatives, 1):
                print(f"{i}. {alt}")
            
            try:
                choice = input("Select an option (or press Enter to skip): ").strip()
                if choice and choice.isdigit() and 1 <= int(choice) <= len(alternatives):
                    alt = alternatives[int(choice)-1]
                    if alt == "manual":
                        return manual_maven_install()
                    else:
                        alt_command = alt.split()
                        print(Fore.GREEN + f"[Aegis] Trying alternative: {' '.join(alt_command)}")
                        return install_package(alt_command[-1], alt_command[0])
            except Exception as e:
                print(Fore.RED + f"[Aegis] Error processing alternative: {e}")
        
        return False

    # Create and start the download animator
    animator = DownloadAnimator(package_name, installer)
    animator.start()

    try:
        # Start the process with pipe for stdout to capture output
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            universal_newlines=True,
            bufsize=1
        )
        
        # Store the full output for error analysis
        full_output = []
        
        # Read output line by line to update progress
        for line in iter(process.stdout.readline, ''):
            # Store output for later analysis
            full_output.append(line.strip())
            
            # Update the animation based on output (when possible)
            progress = extract_progress_info(line)
            if progress is not None:
                animator.progress = progress
                
            # If we detect certain keywords, boost progress
            if "Installing" in line or "Downloaded" in line:
                animator.update_progress(10)
            elif "Extracting" in line:
                animator.update_progress(5)
            
        # Wait for process to complete
        return_code = process.wait()
        
        # Stop the animation
        animator.stop(return_code == 0)
        
        if return_code != 0:
            print(Fore.RED + f"[Aegis] Installation failed with error code {return_code}")
            
            # Special handling for winget errors
            if installer == "winget":
                return handle_winget_error(return_code, package_name)
            
            # Analyze error output
            error_analysis = analyze_error_output(full_output, package_name, installer)
            if error_analysis:
                print(Fore.YELLOW + f"[Aegis] {error_analysis}")
            
            # Try alternatives if appropriate
            alternatives = get_alternative_command(package_name, installer)
            if alternatives:
                print(Fore.YELLOW + f"[Aegis] Would you like to try an alternative installation method? (y/N): ", end="")
                choice = input().strip().lower()
                if choice == 'y':
                    print(Fore.YELLOW + f"[Aegis] Here are alternative installation methods:")
                    for i, alt in enumerate(alternatives, 1):
                        if alt == "manual":
                            print(f"{i}. Manual installation (with detailed instructions)")
                        else:
                            print(f"{i}. {alt}")
                    
                    try:
                        choice = input("Select an option (or press Enter to skip): ").strip()
                        if choice and choice.isdigit():
                            choice_idx = int(choice) - 1
                            if 0 <= choice_idx < len(alternatives):
                                alt = alternatives[choice_idx]
                                if alt == "manual":
                                    return manual_maven_install()
                                else:
                                    alt_command = alt.split()
                                    print(Fore.GREEN + f"[Aegis] Trying alternative: {' '.join(alt_command)}")
                                    return install_package(alt_command[-1], alt_command[0])
                    except Exception as e:
                        print(Fore.RED + f"[Aegis] Error processing alternative: {e}")
            
        return return_code == 0
        
    except Exception as e:
        animator.stop(False)
        print(Fore.RED + f"[Aegis] Error installing '{package_name}': {str(e)}")
        
        # Suggest installing the package manager if appropriate
        if "not recognized" in str(e).lower() or "no such file" in str(e).lower():
            if installer == "winget" and platform.system().lower() == "windows":
                print(Fore.YELLOW + "[Aegis] It seems winget is not installed. "
                                  "You may need to update your Windows App Installer.")
            elif installer == "brew" and (platform.system().lower() == "darwin" or 
                                          platform.system().lower() == "linux"):
                print(Fore.YELLOW + "[Aegis] It seems Homebrew is not installed. "
                                  "You can install it from https://brew.sh/")
            elif installer == "choco" and platform.system().lower() == "windows":
                print(Fore.YELLOW + "[Aegis] It seems Chocolatey is not installed. "
                                  "You can install it from https://chocolatey.org/install")
            elif installer == "apt" and platform.system().lower() == "linux":
                print(Fore.YELLOW + "[Aegis] It seems apt is not available. "
                                  "This may not be a Debian-based Linux distribution.")
        
        return False

def analyze_error_output(output_lines, package_name, installer):
    """Analyze installation error output and suggest solutions"""
    output_text = "\n".join(output_lines).lower()
    
    if "permission denied" in output_text or "access is denied" in output_text:
        if installer in ["apt", "brew"]:
            return "You may need to run with sudo privileges."
        elif installer == "winget":
            return "Try running the terminal as Administrator."
    
    if "could not find a version that satisfies the requirement" in output_text:
        return f"Package '{package_name}' not found in the {installer} repository."
    
    if "network error" in output_text or "connection failed" in output_text:
        return "Network error occurred. Please check your internet connection."
    
    if "disk space" in output_text:
        return "Insufficient disk space for installation."
        
    return None