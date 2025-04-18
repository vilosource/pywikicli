"""
Configuration management for PyWikiCLI.
Handles loading and saving YAML configuration under ~/.pywikicli/.
"""

import os
import yaml

CONFIG_DIR = os.path.expanduser("~/.pywikicli")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.yaml")


def load_config():
    """
    Load configuration from YAML file.
    
    Returns:
        dict: Configuration data or empty dict if file doesn't exist
    """
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f) or {}


def save_config(data: dict):
    """
    Save configuration to YAML file.
    
    Args:
        data (dict): Configuration data to save
    """
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        yaml.safe_dump(data, f)
    os.chmod(CONFIG_PATH, 0o600)  # Secure permissions for config file