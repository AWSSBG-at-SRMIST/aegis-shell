import re
import os
import sys
import subprocess
from typing import Tuple, List, Set, Dict, Optional
import psutil
from pathlib import Path

try:
    import winreg as _winreg
except ImportError:
    _winreg = None

class SecurityManager:
    def __init__(self):
        # These prompt for confirmation rather than being silently blocked
        self.dangerous_commands: Set[str] = {
            'format', 'shutdown', 'regedit',
        }
        # These are risky but common dev tools — warn, don't block
        self.warn_commands: Set[str] = {
            'del', 'rm', 'rmdir', 'rd', 'taskkill',
            'reg', 'netsh', 'net', 'attrib', 'cacls', 'icacls',
        }
        self.safe_directories: Set[str] = set()
        self._init_safe_directories()
        
    def _init_safe_directories(self):
        """Initialize safe directories for command execution"""
        # Add user's home directory
        self.safe_directories.add(os.path.expanduser('~'))
        
        # Add common development directories
        common_dirs = [
            'Documents', 'Downloads', 'Desktop',
            'Projects', 'Development', 'Workspace'
        ]
        
        for dir_name in common_dirs:
            path = os.path.join(os.path.expanduser('~'), dir_name)
            if os.path.exists(path):
                self.safe_directories.add(path)
                
    def validate_command(self, command: str) -> Tuple[bool, str]:
        """
        Validate a command for security.
        Returns: (is_safe, reason)
        Dangerous commands prompt for confirmation; warn_commands allow pass-through with a note.
        """
        try:
            parts = command.split()
            base_command = parts[0].lower()
        except IndexError:
            return False, "Empty command"

        # Hard-block truly destructive commands (format, shutdown, regedit)
        if base_command in self.dangerous_commands:
            from colorama import Fore, Style
            print(Fore.RED + f'[Aegis] WARNING: "{base_command}" is destructive.' + Style.RESET_ALL)
            print(Fore.RED + f'  Command: {command}' + Style.RESET_ALL)
            confirm = input(Fore.YELLOW + '  Run anyway? (yes/N): ' + Style.RESET_ALL).strip()
            if confirm.lower() != 'yes':
                return False, f"Cancelled by user"
            return True, "User confirmed dangerous command"

        # Warn for risky-but-common commands (del, rm, taskkill, etc.)
        if base_command in self.warn_commands:
            from colorama import Fore, Style
            print(Fore.YELLOW + f'[Aegis] Warning: "{base_command}" can be destructive.' + Style.RESET_ALL)
            print(Fore.YELLOW + f'  Command: {command}' + Style.RESET_ALL)
            confirm = input(Fore.YELLOW + '  Continue? (y/N): ' + Style.RESET_ALL).strip()
            if confirm.lower() != 'y':
                return False, "Cancelled by user"
            return True, "User confirmed"

        # Check for system modification commands
        if self._is_system_modification_command(command):
            return False, "Command attempts to modify system settings"

        # Check for network operations
        if self._is_network_command(command):
            if not self._is_safe_network_operation(command):
                return False, "Unsafe network operation detected"
                
        return True, "Command is safe"
        
    def _is_system_modification_command(self, command: str) -> bool:
        """Check if command attempts to modify system settings"""
        system_mod_patterns = [
            r'reg\s+add',
            r'reg\s+delete',
            r'netsh\s+firewall',
            r'netsh\s+interface',
            r'sc\s+config',
            r'sc\s+create',
            r'taskkill\s+/f',
            r'shutdown\s+/s'
        ]
        
        return any(re.search(pattern, command, re.I) for pattern in system_mod_patterns)
        
    def _is_file_operation_command(self, command: str) -> bool:
        """Check if command performs file operations"""
        file_op_patterns = [
            r'del\s+',
            r'rm\s+',
            r'rmdir\s+',
            r'rd\s+',
            r'move\s+',
            r'copy\s+',
            r'xcopy\s+',
            r'robocopy\s+'
        ]
        
        return any(re.search(pattern, command, re.I) for pattern in file_op_patterns)
        
    def _is_safe_file_operation(self, command: str) -> bool:
        """Check if file operation is in safe directories"""
        # Extract file paths from command
        paths = re.findall(r'[\w\\/:.]+', command)
        
        for path in paths:
            if os.path.exists(path):
                abs_path = os.path.abspath(path)
                if not any(abs_path.startswith(safe_dir) for safe_dir in self.safe_directories):
                    return False
        return True
        
    def _is_network_command(self, command: str) -> bool:
        """Check if command performs network operations"""
        network_patterns = [
            r'net\s+use',
            r'net\s+share',
            r'netsh\s+wlan',
            r'ipconfig\s+/release',
            r'ipconfig\s+/renew'
        ]
        
        return any(re.search(pattern, command, re.I) for pattern in network_patterns)
        
    def _is_safe_network_operation(self, command: str) -> bool:
        """Check if network operation is safe"""
        dangerous_net_patterns = [
            r'net\s+share',
            r'net\s+use\s+\*',
            r'netsh\s+wlan\s+connect',
            r'ipconfig\s+/release',
            r'ipconfig\s+/renew',
        ]
        return not any(re.search(p, command, re.I) for p in dangerous_net_patterns)
        
    def check_permissions(self, command: str) -> Tuple[bool, str]:
        """
        Check if command requires elevated permissions
        Returns: (requires_admin, reason)
        """
        admin_patterns = [
            r'reg\s+add',
            r'reg\s+delete',
            r'netsh\s+',
            r'sc\s+',
            r'net\s+user',
            r'net\s+localgroup',
            r'ipconfig\s+/release',
            r'ipconfig\s+/renew'
        ]
        
        if any(re.search(pattern, command, re.I) for pattern in admin_patterns):
            return True, "Command requires administrator privileges"
            
        return False, "Command does not require elevated permissions"
        
    def create_safe_environment(self) -> dict[str, str]:
        """Create a safe environment for command execution"""
        env = os.environ.copy()
        
        # Restrict PATH to safe directories
        safe_path = os.pathsep.join(self.safe_directories)
        env['PATH'] = safe_path
        
        # Set restrictive permissions
        env['PYTHONPATH'] = ''
        env['NODE_PATH'] = ''
        
        return env
        
    def monitor_process(self, process: subprocess.Popen) -> bool:
        """Monitor a process for suspicious activity"""
        try:
            process_info = psutil.Process(process.pid)
            
            # Check for suspicious behavior
            if self._is_suspicious_process(process_info):
                process.terminate()
                return False
                
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
            
    def _is_suspicious_process(self, process: psutil.Process) -> bool:
        """Check if a process exhibits suspicious behavior"""
        try:
            # Check CPU usage
            if process.cpu_percent() > 90:
                return True
                
            # Check memory usage
            if process.memory_percent() > 50:
                return True
                
            # Check for suspicious file operations
            for file in process.open_files():
                if not self._is_safe_file_operation(str(file.path)):
                    return True
                    
            # Check for suspicious network connections
            for conn in process.connections():
                if not self._is_safe_network_connection(conn):
                    return True
                    
            return False
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return True
            
    def _is_safe_network_connection(self, connection) -> bool:
        """Check if a network connection is safe"""
        # Add specific network connection validation logic here
        return True 