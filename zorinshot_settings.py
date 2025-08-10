#!/usr/bin/env python3
"""
ZorinShot Settings Management System

Handles user preferences, autosave configuration, and settings persistence.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class ZorinShotSettings:
    """ZorinShot user settings data class."""
    
    # Autosave settings
    autosave_enabled: bool = False
    default_save_location: str = ""
    filename_pattern: str = "Screenshot_%Y%m%d_%H%M%S"
    default_format: str = "png"
    
    # UI settings
    window_width: int = 900
    window_height: int = 600
    toolbar_style: str = "icons"  # "icons", "text", "both"
    
    # Annotation settings
    default_pen_width: float = 3.0
    default_arrow_width: float = 3.0
    default_rect_width: float = 3.0
    default_text_size: int = 16
    default_color_r: int = 153
    default_color_g: int = 51
    default_color_b: int = 255
    default_color_a: int = 242
    
    # Behavior settings
    copy_to_clipboard_on_save: bool = True
    show_save_confirmation: bool = True
    auto_close_after_save: bool = False
    remember_tool_selection: bool = True
    last_selected_tool: str = "arrow"
    
    # Advanced settings
    temp_dir: str = ""
    max_undo_levels: int = 20
    image_quality_jpeg: int = 95

class SettingsManager:
    """Manages ZorinShot settings persistence and access."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "zorinshot"
        self.config_file = self.config_dir / "settings.json"
        self.settings = ZorinShotSettings()
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Set default save location if not set
        if not self.settings.default_save_location:
            self.settings.default_save_location = str(Path.home() / "Pictures")
        
        # Set default temp directory if not set
        if not self.settings.temp_dir:
            self.settings.temp_dir = str(Path.home() / ".cache" / "zorinshot")
            Path(self.settings.temp_dir).mkdir(parents=True, exist_ok=True)
        
        # Load existing settings
        self.load_settings()
    
    def load_settings(self) -> bool:
        """Load settings from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                # Update settings with loaded data
                for key, value in data.items():
                    if hasattr(self.settings, key):
                        setattr(self.settings, key, value)
                
                print(f"Settings loaded from {self.config_file}")
                return True
            else:
                print("No existing settings file found, using defaults")
                return False
                
        except Exception as e:
            print(f"Error loading settings: {e}")
            return False
    
    def save_settings(self) -> bool:
        """Save settings to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(asdict(self.settings), f, indent=2)
            
            print(f"Settings saved to {self.config_file}")
            return True
            
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get_default_save_path(self, filename: Optional[str] = None) -> str:
        """Get the full path for saving a file."""
        if not filename:
            import time
            filename = time.strftime(self.settings.filename_pattern) + f".{self.settings.default_format}"
        
        return str(Path(self.settings.default_save_location) / filename)
    
    def get_default_color(self) -> tuple:
        """Get the default annotation color as RGBA tuple."""
        return (
            self.settings.default_color_r,
            self.settings.default_color_g,
            self.settings.default_color_b,
            self.settings.default_color_a
        )
    
    def update_setting(self, key: str, value: Any) -> bool:
        """Update a single setting."""
        if hasattr(self.settings, key):
            setattr(self.settings, key, value)
            return self.save_settings()
        return False
    
    def reset_to_defaults(self) -> bool:
        """Reset all settings to defaults."""
        self.settings = ZorinShotSettings()
        return self.save_settings()
    
    def export_settings(self, filepath: str) -> bool:
        """Export settings to a file."""
        try:
            with open(filepath, 'w') as f:
                json.dump(asdict(self.settings), f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting settings: {e}")
            return False
    
    def import_settings(self, filepath: str) -> bool:
        """Import settings from a file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Validate and update settings
            for key, value in data.items():
                if hasattr(self.settings, key):
                    setattr(self.settings, key, value)
            
            return self.save_settings()
            
        except Exception as e:
            print(f"Error importing settings: {e}")
            return False

# Global settings manager instance
settings_manager = SettingsManager()

def get_settings() -> ZorinShotSettings:
    """Get the current settings."""
    return settings_manager.settings

def save_settings() -> bool:
    """Save the current settings."""
    return settings_manager.save_settings()

def update_setting(key: str, value: Any) -> bool:
    """Update a single setting."""
    return settings_manager.update_setting(key, value)

