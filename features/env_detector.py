import os
from typing import Dict, List, Optional, Set
from pathlib import Path
import json
from colorama import Fore, Style


class EnvironmentDetector:
    def __init__(self):
        self.ide_patterns = {
            'vscode':   ['.vscode', 'settings.json'],
            'pycharm':  ['.idea', 'workspace.xml'],
            'eclipse':  ['.project', '.classpath'],
            'intellij': ['.idea', 'workspace.xml'],
            'vim':      ['.vimrc', '.vim'],
            'sublime':  ['.sublime-project', '.sublime-workspace'],
        }
        self.framework_patterns = {
            'django':  ['manage.py', 'settings.py'],
            'flask':   ['app.py', 'flask_app.py'],
            'react':   ['package.json', 'src/App.js'],
            'angular': ['angular.json', 'src/app'],
            'vue':     ['package.json', 'src/App.vue'],
            'spring':  ['pom.xml', 'application.properties'],
            'laravel': ['artisan', 'composer.json'],
            'rails':   ['Gemfile', 'config/routes.rb'],
        }
        self.build_tools = {
            'maven':    ['pom.xml'],
            'gradle':   ['build.gradle', 'settings.gradle'],
            'npm':      ['package.json'],
            'yarn':     ['yarn.lock'],
            'pip':      ['requirements.txt'],
            'composer': ['composer.json'],
            'cargo':    ['Cargo.toml'],
            'go':       ['go.mod'],
        }
        self.database_patterns = {
            'postgresql': ['postgresql.conf', 'pg_hba.conf'],
            'mysql':      ['my.cnf', 'my.ini'],
            'mongodb':    ['mongod.conf'],
            'redis':      ['redis.conf'],
        }
        self.detected_env: Dict[str, Set[str]] = {
            'ides': set(), 'frameworks': set(),
            'build_tools': set(), 'databases': set(), 'languages': set(),
        }

    def detect_environment(self, path: str = '.') -> Dict[str, Set[str]]:
        root = Path(path).resolve()
        for key in self.detected_env:
            self.detected_env[key] = set()
        self._detect_ides(root)
        self._detect_frameworks(root)
        self._detect_build_tools(root)
        self._detect_databases(root)
        self._detect_languages(root)
        return self.detected_env

    def _exists(self, root: Path, pattern: str) -> bool:
        """Check if pattern exists directly in root — no recursion."""
        return (root / pattern).exists()

    def _detect_ides(self, root: Path):
        for ide, patterns in self.ide_patterns.items():
            if any(self._exists(root, p) for p in patterns):
                self.detected_env['ides'].add(ide)

    def _detect_frameworks(self, root: Path):
        for fw, patterns in self.framework_patterns.items():
            if any(self._exists(root, p) for p in patterns):
                self.detected_env['frameworks'].add(fw)

    def _detect_build_tools(self, root: Path):
        for tool, patterns in self.build_tools.items():
            if any(self._exists(root, p) for p in patterns):
                self.detected_env['build_tools'].add(tool)

    def _detect_databases(self, root: Path):
        for db, patterns in self.database_patterns.items():
            if any(self._exists(root, p) for p in patterns):
                self.detected_env['databases'].add(db)

    def _detect_languages(self, root: Path):
        language_extensions = {
            'python':     '.py',
            'javascript': '.js',
            'typescript': '.ts',
            'java':       '.java',
            'csharp':     '.cs',
            'php':        '.php',
            'ruby':       '.rb',
            'go':         '.go',
            'rust':       '.rs',
            'c':          '.c',
            'cpp':        '.cpp',
            'swift':      '.swift',
            'kotlin':     '.kt',
            'scala':      '.scala',
        }
        # Only scan top-level files — no recursion
        try:
            top_files = {f.suffix for f in root.iterdir() if f.is_file()}
        except PermissionError:
            return
        for lang, ext in language_extensions.items():
            if ext in top_files:
                self.detected_env['languages'].add(lang)

    def print_environment(self):
        print(Fore.CYAN + '\nDetected Development Environment:' + Style.RESET_ALL)
        sections = [
            ('IDEs',       'ides'),
            ('Frameworks', 'frameworks'),
            ('Build Tools','build_tools'),
            ('Databases',  'databases'),
            ('Languages',  'languages'),
        ]
        for label, key in sections:
            items = sorted(self.detected_env[key])
            if items:
                print(Fore.GREEN + f'\n{label}:' + Style.RESET_ALL)
                for item in items:
                    print(f'  - {item}')
