import subprocess
import os
import platform
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
try:
    import semver
    _SEMVER_AVAILABLE = True
except ImportError:
    _SEMVER_AVAILABLE = False

import requests
from colorama import Fore, Style

class PackageManager:
    def __init__(self):
        self.system = platform.system().lower()
        self.package_managers = self._detect_package_managers()
        self.package_cache: Dict[str, Dict] = {}
        self.dependency_graph: Dict[str, List[str]] = {}
        self._load_cache()
        
    def _detect_package_managers(self) -> Dict[str, bool]:
        """Detect available package managers on the system"""
        managers = {
            'winget': False,
            'choco': False,
            'scoop': False,
            'apt': False,
            'yum': False,
            'dnf': False,
            'brew': False,
            'pip': False,
            'npm': False
        }
        
        for manager in managers:
            try:
                if manager == 'winget':
                    subprocess.run(['winget', '--version'], capture_output=True, check=False)
                else:
                    subprocess.run([manager, '--version'], capture_output=True, check=False)
                managers[manager] = True
            except FileNotFoundError:
                continue
                
        return managers
        
    def _load_cache(self):
        """Load package cache from file"""
        cache_file = Path.home() / '.aegis' / 'package_cache.json'
        if cache_file.exists():
            with open(cache_file) as f:
                self.package_cache = json.load(f)
                
    def _save_cache(self):
        """Save package cache to file"""
        cache_file = Path.home() / '.aegis' / 'package_cache.json'
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(self.package_cache, f)
            
    def get_package_info(self, package_name: str) -> Optional[Dict]:
        """Get package information from cache or fetch it"""
        if package_name in self.package_cache:
            return self.package_cache[package_name]
            
        info = self._fetch_package_info(package_name)
        if info:
            self.package_cache[package_name] = info
            self._save_cache()
        return info
        
    def _fetch_package_info(self, package_name: str) -> Optional[Dict]:
        """Fetch package information from package manager"""
        for manager, available in self.package_managers.items():
            if not available:
                continue
                
            try:
                if manager == 'winget':
                    result = subprocess.run(
                        ['winget', 'show', package_name],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                elif manager == 'choco':
                    result = subprocess.run(
                        ['choco', 'info', package_name],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                elif manager == 'scoop':
                    result = subprocess.run(
                        ['scoop', 'info', package_name],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                elif manager == 'apt':
                    result = subprocess.run(
                        ['apt-cache', 'show', package_name],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                elif manager == 'pip':
                    result = subprocess.run(
                        ['pip', 'show', package_name],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                elif manager == 'npm':
                    result = subprocess.run(
                        ['npm', 'view', package_name],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    
                if result.returncode == 0:
                    return self._parse_package_info(manager, result.stdout)
                    
            except Exception as e:
                print(f"Error fetching package info from {manager}: {e}")
                continue
                
        return None
        
    def _parse_package_info(self, manager: str, output: str) -> Dict:
        """Parse package information from package manager output"""
        info = {
            'manager': manager,
            'name': '',
            'version': '',
            'dependencies': [],
            'description': ''
        }
        
        if manager == 'winget':
            # Parse winget output
            for line in output.split('\n'):
                if 'Name:' in line:
                    info['name'] = line.split('Name:')[1].strip()
                elif 'Version:' in line:
                    info['version'] = line.split('Version:')[1].strip()
                elif 'Description:' in line:
                    info['description'] = line.split('Description:')[1].strip()
                    
        elif manager == 'pip':
            # Parse pip output
            for line in output.split('\n'):
                if 'Name:' in line:
                    info['name'] = line.split('Name:')[1].strip()
                elif 'Version:' in line:
                    info['version'] = line.split('Version:')[1].strip()
                elif 'Summary:' in line:
                    info['description'] = line.split('Summary:')[1].strip()
                elif 'Requires:' in line:
                    deps = line.split('Requires:')[1].strip()
                    if deps:
                        info['dependencies'] = [d.strip() for d in deps.split(',')]
                        
        # Add more parsers for other package managers
        
        return info
        
    def resolve_dependencies(self, package_name: str) -> List[str]:
        """Resolve package dependencies"""
        if package_name in self.dependency_graph:
            return self.dependency_graph[package_name]
            
        dependencies = []
        info = self.get_package_info(package_name)
        if info and 'dependencies' in info:
            dependencies.extend(info['dependencies'])
            for dep in info['dependencies']:
                dependencies.extend(self.resolve_dependencies(dep))
                
        self.dependency_graph[package_name] = list(set(dependencies))
        return self.dependency_graph[package_name]
        
    def check_version_conflicts(self, package_name: str, version: str) -> List[Tuple[str, str, str]]:
        """Check for version conflicts with installed packages"""
        conflicts = []
        info = self.get_package_info(package_name)
        if not info:
            return conflicts
            
        for dep in self.resolve_dependencies(package_name):
            dep_info = self.get_package_info(dep)
            if dep_info and 'version' in dep_info:
                if not self._is_compatible_version(dep_info['version'], version):
                    conflicts.append((dep, dep_info['version'], version))
                    
        return conflicts
        
    def _is_compatible_version(self, installed: str, required: str) -> bool:
        """Check if installed version is compatible with required version"""
        if not _SEMVER_AVAILABLE:
            return True  # can't compare without semver, assume compatible
        try:
            return semver.compare(installed, required) >= 0
        except ValueError:
            return False
            
    def install_package(self, package_name: str, version: Optional[str] = None) -> bool:
        """Install a package with version management"""
        # Check for conflicts
        conflicts = self.check_version_conflicts(package_name, version or 'latest')
        if conflicts:
            print(f"Version conflicts detected for {package_name}:")
            for dep, installed, required in conflicts:
                print(f"  {dep}: installed={installed}, required={required}")
            return False
            
        # Install package
        for manager, available in self.package_managers.items():
            if not available:
                continue
                
            try:
                if manager == 'winget':
                    cmd = ['winget', 'install', package_name]
                    if version:
                        cmd.extend(['--version', version])
                elif manager == 'choco':
                    cmd = ['choco', 'install', package_name]
                    if version:
                        cmd.extend(['--version', version])
                elif manager == 'scoop':
                    cmd = ['scoop', 'install', package_name]
                elif manager == 'apt':
                    cmd = ['apt', 'install', package_name]
                elif manager == 'pip':
                    cmd = ['pip', 'install', package_name]
                    if version:
                        cmd.extend(['==', version])
                elif manager == 'npm':
                    cmd = ['npm', 'install', '-g', package_name]
                    if version:
                        cmd.extend(['@', version])
                        
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                if result.returncode == 0:
                    print(f"Successfully installed {package_name} using {manager}")
                    return True
                    
            except Exception as e:
                print(f"Error installing package using {manager}: {e}")
                continue
                
        return False
        
    def update_package(self, package_name: str) -> bool:
        """Update a package to the latest version"""
        for manager, available in self.package_managers.items():
            if not available:
                continue
                
            try:
                if manager == 'winget':
                    cmd = ['winget', 'upgrade', package_name]
                elif manager == 'choco':
                    cmd = ['choco', 'upgrade', package_name]
                elif manager == 'scoop':
                    cmd = ['scoop', 'update', package_name]
                elif manager == 'apt':
                    cmd = ['apt', 'upgrade', package_name]
                elif manager == 'pip':
                    cmd = ['pip', 'install', '--upgrade', package_name]
                elif manager == 'npm':
                    cmd = ['npm', 'update', '-g', package_name]
                    
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                if result.returncode == 0:
                    print(f"Successfully updated {package_name} using {manager}")
                    return True
                    
            except Exception as e:
                print(f"Error updating package using {manager}: {e}")
                continue
                
        return False
        
    def uninstall_package(self, package_name: str) -> bool:
        """Uninstall a package"""
        for manager, available in self.package_managers.items():
            if not available:
                continue
                
            try:
                if manager == 'winget':
                    cmd = ['winget', 'uninstall', package_name]
                elif manager == 'choco':
                    cmd = ['choco', 'uninstall', package_name]
                elif manager == 'scoop':
                    cmd = ['scoop', 'uninstall', package_name]
                elif manager == 'apt':
                    cmd = ['apt', 'remove', package_name]
                elif manager == 'pip':
                    cmd = ['pip', 'uninstall', '-y', package_name]
                elif manager == 'npm':
                    cmd = ['npm', 'uninstall', '-g', package_name]
                    
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                if result.returncode == 0:
                    print(f"Successfully uninstalled {package_name} using {manager}")
                    return True
                    
            except Exception as e:
                print(f"Error uninstalling package using {manager}: {e}")
                continue
                
        return False
        
    def rollback_package(self, package_name: str, version: str) -> bool:
        """Rollback a package to a specific version"""
        return self.install_package(package_name, version) 