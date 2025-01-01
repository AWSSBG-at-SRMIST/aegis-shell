import json
import os
import sys
from pathlib import Path

# Get the base directory for the project
BASE_DIR = Path(__file__).resolve().parent

# Use proper path joining to ensure cross-platform compatibility
COMMAND_MAPPINGS_FILE = os.path.join(BASE_DIR, "config", "commands_mapping.json")
CONFIG_FILE = os.path.join(BASE_DIR, "config", "config.json")

def load_command_mappings():
    try:
        if not os.path.exists(COMMAND_MAPPINGS_FILE):
            print(f"Warning: Command mappings file not found at {COMMAND_MAPPINGS_FILE}")
            return {}
        with open(COMMAND_MAPPINGS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading command mappings: {e}")
        return {}

def save_command_mappings(mappings):
    with open(COMMAND_MAPPINGS_FILE, "w") as f:
        json.dump(mappings, f, indent=4)

def update_command_mapping(command, environment, package_name, install_method):
    mappings = load_command_mappings()

    if command not in mappings:
        mappings[command] = {}

    mappings[command][environment] = {
        "package": package_name,
        "install": install_method
    }

    save_command_mappings(mappings)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)