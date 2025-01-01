import os
import sys
import json
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from colorama import Fore, Style, init

class HelpSystem:
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else Path.home() / '.aegis' / 'help'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self.commands = self._load_commands()
        self.tutorials = self._load_tutorials()
        self.examples = self._load_examples()
        init()  # Initialize colorama
        
    def _setup_logging(self):
        """Setup logging configuration"""
        log_dir = self.config_dir / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / 'help.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
    def _load_commands(self) -> Dict[str, Any]:
        """Load command documentation"""
        try:
            commands_file = self.config_dir / 'commands.json'
            
            if not commands_file.exists():
                # Create default commands
                commands = {
                    'config': {
                        'description': 'Manage configuration settings',
                        'usage': 'config [get|set|delete] [key] [value]',
                        'options': {
                            'get': 'Get configuration value',
                            'set': 'Set configuration value',
                            'delete': 'Delete configuration value'
                        },
                        'examples': [
                            'config get shell.prompt',
                            'config set shell.prompt "> "',
                            'config delete shell.prompt'
                        ]
                    },
                    'help': {
                        'description': 'Show help information',
                        'usage': 'help [command]',
                        'options': {
                            'command': 'Show help for specific command'
                        },
                        'examples': [
                            'help',
                            'help config'
                        ]
                    },
                    'plugin': {
                        'description': 'Manage plugins',
                        'usage': 'plugin [list|load|unload|reload] [name]',
                        'options': {
                            'list': 'List available plugins',
                            'load': 'Load plugin',
                            'unload': 'Unload plugin',
                            'reload': 'Reload plugin'
                        },
                        'examples': [
                            'plugin list',
                            'plugin load my_plugin',
                            'plugin unload my_plugin',
                            'plugin reload my_plugin'
                        ]
                    },
                    'theme': {
                        'description': 'Manage themes',
                        'usage': 'theme [list|set|reset] [name]',
                        'options': {
                            'list': 'List available themes',
                            'set': 'Set theme',
                            'reset': 'Reset to default theme'
                        },
                        'examples': [
                            'theme list',
                            'theme set dark',
                            'theme reset'
                        ]
                    },
                    'update': {
                        'description': 'Update system',
                        'usage': 'update [check|install|remove] [package]',
                        'options': {
                            'check': 'Check for updates',
                            'install': 'Install updates',
                            'remove': 'Remove updates'
                        },
                        'examples': [
                            'update check',
                            'update install',
                            'update remove'
                        ]
                    }
                }
                
                # Save default commands
                with open(commands_file, 'w') as f:
                    json.dump(commands, f, indent=4)
                    
                return commands
                
            # Load existing commands
            with open(commands_file) as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading commands: {e}")
            return {}
            
    def _load_tutorials(self) -> Dict[str, Any]:
        """Load tutorials"""
        try:
            tutorials_file = self.config_dir / 'tutorials.json'
            
            if not tutorials_file.exists():
                # Create default tutorials
                tutorials = {
                    'getting_started': {
                        'title': 'Getting Started',
                        'description': 'Learn the basics of using the shell',
                        'sections': [
                            {
                                'title': 'Installation',
                                'content': 'Install the shell using your package manager or from source.'
                            },
                            {
                                'title': 'Configuration',
                                'content': 'Configure the shell using the config command.'
                            },
                            {
                                'title': 'Basic Commands',
                                'content': 'Learn basic commands like help, config, and theme.'
                            }
                        ]
                    },
                    'plugins': {
                        'title': 'Using Plugins',
                        'description': 'Learn how to use and create plugins',
                        'sections': [
                            {
                                'title': 'Installing Plugins',
                                'content': 'Install plugins using the plugin command.'
                            },
                            {
                                'title': 'Loading Plugins',
                                'content': 'Load plugins using the plugin load command.'
                            },
                            {
                                'title': 'Creating Plugins',
                                'content': 'Create plugins by following the plugin development guide.'
                            }
                        ]
                    },
                    'themes': {
                        'title': 'Customizing Themes',
                        'description': 'Learn how to customize the shell appearance',
                        'sections': [
                            {
                                'title': 'Built-in Themes',
                                'content': 'Use built-in themes with the theme command.'
                            },
                            {
                                'title': 'Custom Themes',
                                'content': 'Create custom themes by modifying theme files.'
                            },
                            {
                                'title': 'Theme Components',
                                'content': 'Learn about theme components and how to modify them.'
                            }
                        ]
                    }
                }
                
                # Save default tutorials
                with open(tutorials_file, 'w') as f:
                    json.dump(tutorials, f, indent=4)
                    
                return tutorials
                
            # Load existing tutorials
            with open(tutorials_file) as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading tutorials: {e}")
            return {}
            
    def _load_examples(self) -> Dict[str, Any]:
        """Load examples"""
        try:
            examples_file = self.config_dir / 'examples.json'
            
            if not examples_file.exists():
                # Create default examples
                examples = {
                    'configuration': {
                        'title': 'Configuration Examples',
                        'description': 'Examples of common configuration tasks',
                        'examples': [
                            {
                                'title': 'Change Prompt',
                                'command': 'config set shell.prompt "> "',
                                'description': 'Change the shell prompt'
                            },
                            {
                                'title': 'Enable Auto-complete',
                                'command': 'config set shell.auto_complete true',
                                'description': 'Enable command auto-completion'
                            },
                            {
                                'title': 'Set Theme',
                                'command': 'config set theme.name dark',
                                'description': 'Set the shell theme'
                            }
                        ]
                    },
                    'plugins': {
                        'title': 'Plugin Examples',
                        'description': 'Examples of plugin usage',
                        'examples': [
                            {
                                'title': 'List Plugins',
                                'command': 'plugin list',
                                'description': 'List available plugins'
                            },
                            {
                                'title': 'Load Plugin',
                                'command': 'plugin load my_plugin',
                                'description': 'Load a plugin'
                            },
                            {
                                'title': 'Unload Plugin',
                                'command': 'plugin unload my_plugin',
                                'description': 'Unload a plugin'
                            }
                        ]
                    },
                    'themes': {
                        'title': 'Theme Examples',
                        'description': 'Examples of theme usage',
                        'examples': [
                            {
                                'title': 'List Themes',
                                'command': 'theme list',
                                'description': 'List available themes'
                            },
                            {
                                'title': 'Set Theme',
                                'command': 'theme set dark',
                                'description': 'Set a theme'
                            },
                            {
                                'title': 'Reset Theme',
                                'command': 'theme reset',
                                'description': 'Reset to default theme'
                            }
                        ]
                    }
                }
                
                # Save default examples
                with open(examples_file, 'w') as f:
                    json.dump(examples, f, indent=4)
                    
                return examples
                
            # Load existing examples
            with open(examples_file) as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading examples: {e}")
            return {}
            
    def show_help(self, command: str = None):
        """Show help information"""
        try:
            if command:
                # Show command help
                if command in self.commands:
                    data = self.commands[command]
                    print(f"\n{Fore.CYAN}{command}{Style.RESET_ALL}")
                    print(f"\n{data['description']}")
                    print(f"\nUsage: {data['usage']}")
                    
                    if 'options' in data:
                        print("\nOptions:")
                        for opt, desc in data['options'].items():
                            print(f"  {opt}: {desc}")
                            
                    if 'examples' in data:
                        print("\nExamples:")
                        for ex in data['examples']:
                            print(f"  {ex}")
                else:
                    print(f"\n{Fore.RED}No help available for {command}{Style.RESET_ALL}")
                return
                
            # Show general help
            print(f"\n{Fore.CYAN}Available Commands:{Style.RESET_ALL}")
            for cmd, data in self.commands.items():
                print(f"\n{Fore.YELLOW}{cmd}{Style.RESET_ALL}")
                print(f"  {data['description']}")
                
            print(f"\nUse 'help <command>' for more information")
        except Exception as e:
            logging.error(f"Error showing help: {e}")
            
    def show_tutorial(self, tutorial: str = None):
        """Show tutorial"""
        try:
            if tutorial:
                # Show specific tutorial
                if tutorial in self.tutorials:
                    data = self.tutorials[tutorial]
                    print(f"\n{Fore.CYAN}{data['title']}{Style.RESET_ALL}")
                    print(f"\n{data['description']}")
                    
                    for section in data['sections']:
                        print(f"\n{Fore.YELLOW}{section['title']}{Style.RESET_ALL}")
                        print(f"{section['content']}")
                else:
                    print(f"\n{Fore.RED}No tutorial available for {tutorial}{Style.RESET_ALL}")
                return
                
            # Show tutorial list
            print(f"\n{Fore.CYAN}Available Tutorials:{Style.RESET_ALL}")
            for tut, data in self.tutorials.items():
                print(f"\n{Fore.YELLOW}{data['title']}{Style.RESET_ALL}")
                print(f"  {data['description']}")
                
            print(f"\nUse 'tutorial <name>' to view a tutorial")
        except Exception as e:
            logging.error(f"Error showing tutorial: {e}")
            
    def show_examples(self, category: str = None):
        """Show examples"""
        try:
            if category:
                # Show category examples
                if category in self.examples:
                    data = self.examples[category]
                    print(f"\n{Fore.CYAN}{data['title']}{Style.RESET_ALL}")
                    print(f"\n{data['description']}")
                    
                    for example in data['examples']:
                        print(f"\n{Fore.YELLOW}{example['title']}{Style.RESET_ALL}")
                        print(f"Command: {example['command']}")
                        print(f"Description: {example['description']}")
                else:
                    print(f"\n{Fore.RED}No examples available for {category}{Style.RESET_ALL}")
                return
                
            # Show example categories
            print(f"\n{Fore.CYAN}Example Categories:{Style.RESET_ALL}")
            for cat, data in self.examples.items():
                print(f"\n{Fore.YELLOW}{data['title']}{Style.RESET_ALL}")
                print(f"  {data['description']}")
                
            print(f"\nUse 'examples <category>' to view examples")
        except Exception as e:
            logging.error(f"Error showing examples: {e}")
            
    def get_config_directory(self) -> Path:
        """Get configuration directory"""
        return self.config_dir 