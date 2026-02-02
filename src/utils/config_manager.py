#!/usr/bin/env python3
"""
Configuration Manager for Apple Health Dashboard

Handles loading and saving configuration settings.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

def load_config() -> Dict[str, Any]:
    """Load configuration from file, or return defaults if file doesn't exist."""
    config_file = Path("config/config.json")
    
    # Default configuration
    default_config = {
        "visualization": {
            "theme": "light",
            "timezone": "local",
            "date_format": "YYYY-MM-DD",
            "show_outliers": True,
            "smoothing_window": 7
        },
        "data_processing": {
            "exclude_sources": [],
            "exclude_types": [],
            "min_records_for_visualization": 5
        },
        "dashboard": {
            "refresh_interval": 3600,
            "default_view": "overview",
            "show_debug_info": False
        }
    }
    
    # Try to load existing config
    try:
        if config_file.exists():
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                # Merge user config with defaults (user config takes precedence)
                return _deep_merge(default_config, user_config)
        return default_config
    except (json.JSONDecodeError, IOError) as e:
        print(f"⚠️ Error loading config file: {e}")
        return default_config

def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to file."""
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    config_file = config_dir / "config.json"
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Configuration saved to {config_file}")
    except IOError as e:
        print(f"❌ Error saving config file: {e}")

def _deep_merge(default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries, with user values taking precedence."""
    result = default.copy()
    
    for key, value in user.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result