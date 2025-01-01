import os
import sys
import json
import logging
from pathlib import Path
from colorama import init, Fore, Style

class DocumentationManager:
    def __init__(self):
        self.config_dir = Path.home() / '.aegis' / 'docs'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        self._load_documentation()
        
    def _setup_logging(self):
        """Set up logging configuration"""
        log_dir = self.config_dir / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'documentation.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('DocumentationManager')
        
    def _load_documentation(self):
        """Load or create documentation content"""
        docs_file = self.config_dir / 'documentation.json'
        
        if not docs_file.exists():
            self._create_default_documentation(docs_file)
            
        try:
            with open(docs_file, 'r', encoding='utf-8') as f:
                self.docs = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading documentation: {e}")
            self._create_default_documentation(docs_file)
            
    def _create_default_documentation(self, docs_file):
        """Create default documentation content"""
        self.docs = {
            "developers": {
                "title": "About Developers",
                "content": {
                    "header": "Aegis Shell was developed by:",
                    "team": [
                        "Tanish Poddar       | GitHub: github.com/tanishpoddar",
                        "Nidhi Nayana        | GitHub: github.com/nidhi-nayana",
                        "Nishant Ranjan      | GitHub: github.com/nishant-codess"
                    ],
                    "institution": "They are B.Tech students from SRM Institute of Science and Technology (SRMIST), Kattankulathur.",
                    "about_project": "This project is a result of their shared interest in systems programming and shell design, aiming to create a lightweight, efficient, and user-friendly shell interface.",
                    "repository": "Project Repository:\ngithub.com/tanishpoddar/aegis-shell"
                }
            },
            "contribution": {
                "title": "Contribution Guidelines",
                "content": {
                    "guidelines": [
                        "1. Fork the repository",
                        "2. Create a new branch for your feature",
                        "3. Make your changes",
                        "4. Submit a pull request",
                        "5. Follow the code style guidelines"
                    ],
                    "code_of_conduct": [
                        "1. Be respectful and inclusive",
                        "2. Be patient and welcoming",
                        "3. Be thoughtful",
                        "4. Be collaborative",
                        "5. When disagreeing, try to understand why"
                    ]
                }
            },
            "faq": {
                "title": "Frequently Asked Questions",
                "content": {
                    "installation": [
                        "Q: How do I install Aegis Shell?",
                        "A: Follow the installation guide in the README.md file.",
                        "",
                        "Q: What are the system requirements?",
                        "A: Python 3.8+ and basic system utilities."
                    ],
                    "usage": [
                        "Q: How do I start using Aegis Shell?",
                        "A: Type 'aegis-shell' in your terminal.",
                        "",
                        "Q: What are the basic commands?",
                        "A: Use 'help' command to see all available commands."
                    ],
                    "troubleshooting": [
                        "Q: What if I encounter errors?",
                        "A: Check the error logs and documentation for solutions.",
                        "",
                        "Q: How do I report bugs?",
                        "A: Create an issue on our GitHub repository."
                    ]
                }
            },
            "terms": {
                "title": "Terms and Conditions",
                "content": {
                    "license": "GNU GPL v3",
                    "usage_terms": [
                        "1. This software is provided 'as is'",
                        "2. Users must comply with the GPL v3 license",
                        "3. No warranty is provided",
                        "4. Users are responsible for their use of the software"
                    ],
                    "privacy": [
                        "1. We do not collect personal data",
                        "2. Usage statistics may be collected anonymously",
                        "3. All data is stored locally"
                    ],
                    "disclaimer": "This software is provided without any warranty.",
                    "obligations": [
                        "1. Follow the license terms",
                        "2. Report bugs and issues",
                        "3. Contribute responsibly"
                    ]
                }
            },
            "user_guide": {
                "title": "User Guide",
                "content": {
                    "getting_started": [
                        "1. Installation",
                        "2. Basic configuration",
                        "3. First steps"
                    ],
                    "basic_commands": [
                        "help - Show help information",
                        "config - Configure settings",
                        "theme - Change theme",
                        "plugin - Manage plugins"
                    ],
                    "advanced_features": [
                        "Custom scripting",
                        "Plugin development",
                        "Theme customization",
                        "Advanced configuration"
                    ],
                    "configuration": [
                        "1. User preferences",
                        "2. System settings",
                        "3. Plugin configuration",
                        "4. Theme settings"
                    ],
                    "best_practices": [
                        "1. Regular updates",
                        "2. Backup configuration",
                        "3. Security practices",
                        "4. Performance optimization"
                    ]
                }
            }
        }
        
        try:
            with open(docs_file, 'w', encoding='utf-8') as f:
                json.dump(self.docs, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error creating documentation: {e}")
            
    def show_menu(self):
        """Display the main documentation menu"""
        print(f"\n{Fore.CYAN}=== Aegis Shell Documentation ==={Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Select a section to view:{Style.RESET_ALL}")
        
        sections = list(self.docs.keys())
        for i, section in enumerate(sections, 1):
            print(f"{i}. {self.docs[section]['title']}")
            
        print(f"\n{Fore.GREEN}Enter section number (or 'q' to quit):{Style.RESET_ALL}")
        
    def show_section(self, section_name):
        """Display a specific documentation section"""
        if section_name not in self.docs:
            print(f"{Fore.RED}Section not found: {section_name}{Style.RESET_ALL}")
            return
            
        section = self.docs[section_name]
        print(f"\n{Fore.CYAN}=== {section['title']} ==={Style.RESET_ALL}\n")
        
        if section_name == "developers":
            # Display the exact content with proper formatting
            print("Aegis Shell was developed by:\n")
            
            # Team members with proper spacing
            print("Tanish Poddar       | GitHub: github.com/tanishpoddar")
            print("Nidhi Nayana        | GitHub: github.com/nidhi-nayana")
            print("Nishant Ranjan      | GitHub: github.com/nishant-codess\n")
            
            # Institution and project info
            print("They are B.Tech students from SRM Institute of Science and")
            print("Technology (SRMIST), Kattankulathur.\n")
            
            print("This project is a result of their shared interest in systems")
            print("programming and shell design, aiming to create a lightweight,")
            print("efficient, and user-friendly shell interface.\n")
            
            print("Project Repository:")
            print("github.com/tanishpoddar/aegis-shell")
        else:
            # Default formatting for other sections
            for key, value in section['content'].items():
                if isinstance(value, list):
                    print(f"{Fore.YELLOW}{key.replace('_', ' ').title()}:{Style.RESET_ALL}")
                    for item in value:
                        print(f"  {item}")
                    print()
                else:
                    print(f"{Fore.YELLOW}{key.replace('_', ' ').title()}:{Style.RESET_ALL}")
                    print(f"  {value}\n")
                
    def run(self):
        """Run the documentation interface"""
        while True:
            self.show_menu()
            choice = input().strip().lower()
            
            if choice == 'q':
                break
                
            try:
                section_index = int(choice) - 1
                if 0 <= section_index < len(self.docs):
                    section_name = list(self.docs.keys())[section_index]
                    self.show_section(section_name)
                else:
                    print(f"{Fore.RED}Invalid section number{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}Invalid input{Style.RESET_ALL}")
                
            input(f"\n{Fore.GREEN}Press Enter to continue...{Style.RESET_ALL}")
            
if __name__ == "__main__":
    init()  # Initialize colorama
    doc_manager = DocumentationManager()
    doc_manager.run() 