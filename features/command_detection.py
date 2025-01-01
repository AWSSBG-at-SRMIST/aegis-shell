import os
import re
from typing import List, Dict, Optional
from pathlib import Path
import json
from difflib import get_close_matches
import glob

class CommandDetector:
    def __init__(self):
        self.command_history: List[str] = []
        self.command_aliases: Dict[str, str] = {}
        self.command_templates: Dict[str, str] = {}
        self.fuzzy_threshold = 0.6
        self._load_history()
        self._load_aliases()
        self._load_templates()
        
    def _load_history(self):
        """Load command history from file"""
        history_file = Path.home() / '.aegis' / 'command_history.json'
        if history_file.exists():
            with open(history_file) as f:
                self.command_history = json.load(f)
                
    def _save_history(self):
        """Save command history to file"""
        history_file = Path.home() / '.aegis' / 'command_history.json'
        history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(history_file, 'w') as f:
            json.dump(self.command_history, f)
            
    def _load_aliases(self):
        """Load command aliases from file"""
        alias_file = Path.home() / '.aegis' / 'aliases.json'
        if alias_file.exists():
            with open(alias_file) as f:
                self.command_aliases = json.load(f)
                
    def _save_aliases(self):
        """Save command aliases to file"""
        alias_file = Path.home() / '.aegis' / 'aliases.json'
        alias_file.parent.mkdir(parents=True, exist_ok=True)
        with open(alias_file, 'w') as f:
            json.dump(self.command_aliases, f)
            
    def _load_templates(self):
        """Load command templates from file"""
        template_file = Path.home() / '.aegis' / 'templates.json'
        if template_file.exists():
            with open(template_file) as f:
                self.command_templates = json.load(f)
                
    def _save_templates(self):
        """Save command templates to file"""
        template_file = Path.home() / '.aegis' / 'templates.json'
        template_file.parent.mkdir(parents=True, exist_ok=True)
        with open(template_file, 'w') as f:
            json.dump(self.command_templates, f)
            
    def add_to_history(self, command: str):
        """Add command to history"""
        if command not in self.command_history:
            self.command_history.append(command)
            self._save_history()
            
    def get_suggestions(self, partial: str) -> List[str]:
        """Get command suggestions based on partial input"""
        suggestions = []
        
        # Check aliases
        for alias, command in self.command_aliases.items():
            if alias.startswith(partial):
                suggestions.append(alias)
                
        # Check templates
        for template, _ in self.command_templates.items():
            if template.startswith(partial):
                suggestions.append(template)
                
        # Check history
        for cmd in self.command_history:
            if cmd.startswith(partial):
                suggestions.append(cmd)
                
        # Fuzzy matching
        fuzzy_matches = get_close_matches(
            partial,
            self.command_history + list(self.command_aliases.keys()) + list(self.command_templates.keys()),
            n=5,
            cutoff=self.fuzzy_threshold
        )
        suggestions.extend(fuzzy_matches)
        
        return list(set(suggestions))
        
    def expand_alias(self, command: str) -> str:
        """Expand command alias if it exists"""
        return self.command_aliases.get(command, command)
        
    def apply_template(self, template: str, **kwargs) -> str:
        """Apply command template with given parameters"""
        if template in self.command_templates:
            return self.command_templates[template].format(**kwargs)
        return template
        
    def add_alias(self, alias: str, command: str):
        """Add new command alias"""
        self.command_aliases[alias] = command
        self._save_aliases()
        
    def add_template(self, name: str, template: str):
        """Add new command template"""
        self.command_templates[name] = template
        self._save_templates()
        
    def correct_command(self, command: str) -> str:
        """Attempt to correct command if it's close to a known command"""
        if command in self.command_history or command in self.command_aliases:
            return command
            
        matches = get_close_matches(command, self.command_history, n=1, cutoff=0.8)
        if matches:
            return matches[0]
        return command 