import json
import os
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigLoader:
    """Load and manage configuration settings for PDF processing optimization"""
    
    def __init__(self, config_file: str = "processing_config.json"):
        self.config_file = config_file
        self.config = self._load_default_config()
        self._load_config_file()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration values"""
        return {
            "performance": {
                "max_workers": 4,
                "batch_size": 10,
                "memory_limit_mb": 1024,
                "ocr_batch_size": 5,
                "page_chunk_size": 10
            },
            "features": {
                "enable_ocr": True,
                "enable_digital": True,
                "skip_existing": True,
                "enable_caching": True,
                "enable_checkpointing": True
            },
            "ocr": {
                "tesseract_config": "--psm 4",
                "timeout_seconds": 30,
                "max_ocr_workers": 2
            },
            "memory": {
                "force_cleanup_interval": 2,
                "gc_collection_level": 2
            },
            "logging": {
                "log_level": "INFO",
                "show_progress": True,
                "show_memory_usage": True
            },
            "paths": {
                "hash_cache_file": ".file_hashes.json",
                "checkpoint_file": ".processing_checkpoint.json",
                "log_file": "processing.log"
            }
        }
    
    def _load_config_file(self):
        """Load configuration from JSON file if it exists"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    self._merge_config(file_config)
                    print(f"Loaded configuration from {self.config_file}")
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config file {self.config_file}: {e}")
                print("Using default configuration")
        else:
            print(f"Config file {self.config_file} not found, using default configuration")
            self._save_default_config()
    
    def _merge_config(self, file_config: Dict[str, Any]):
        """Merge file configuration with defaults"""
        for section, settings in file_config.items():
            if section in self.config:
                if isinstance(settings, dict):
                    for key, value in settings.items():
                        if key in self.config[section]:
                            self.config[section][key] = value
                        else:
                            print(f"Warning: Unknown config key: {section}.{key}")
                else:
                    self.config[section] = settings
            else:
                print(f"Warning: Unknown config section: {section}")
    
    def _save_default_config(self):
        """Save default configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"Saved default configuration to {self.config_file}")
        except IOError as e:
            print(f"Warning: Could not save default config: {e}")
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get configuration value by section and key"""
        try:
            return self.config[section][key]
        except KeyError:
            return default
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        return self.config.get(section, {})
    
    def set(self, section: str, key: str, value: Any):
        """Set configuration value"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"Configuration saved to {self.config_file}")
        except IOError as e:
            print(f"Error saving configuration: {e}")
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get configuration suitable for ProcessingConfig class"""
        return {
            "max_workers": self.get("performance", "max_workers", 4),
            "batch_size": self.get("performance", "batch_size", 10),
            "memory_limit_mb": self.get("performance", "memory_limit_mb", 1024),
            "enable_ocr": self.get("features", "enable_ocr", True),
            "enable_digital": self.get("features", "enable_digital", True),
            "skip_existing": self.get("features", "skip_existing", True),
            "enable_caching": self.get("features", "enable_caching", True),
            "enable_checkpointing": self.get("features", "enable_checkpointing", True),
            "ocr_batch_size": self.get("performance", "ocr_batch_size", 5),
            "page_chunk_size": self.get("performance", "page_chunk_size", 10),
            "tesseract_config": self.get("ocr", "tesseract_config", "--psm 4"),
            "ocr_timeout": self.get("ocr", "timeout_seconds", 30),
            "max_ocr_workers": self.get("ocr", "max_ocr_workers", 2)
        }
    
    def print_config(self):
        """Print current configuration"""
        print("Current Configuration:")
        print("=" * 50)
        for section, settings in self.config.items():
            print(f"\n[{section.upper()}]")
            if isinstance(settings, dict):
                for key, value in settings.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  {settings}")
    
    def validate_config(self) -> bool:
        """Validate configuration values"""
        errors = []
        
        # Check performance settings
        max_workers = self.get("performance", "max_workers")
        if max_workers < 1 or max_workers > 32:
            errors.append("max_workers must be between 1 and 32")
        
        memory_limit = self.get("performance", "memory_limit_mb")
        if memory_limit < 100 or memory_limit > 10000:
            errors.append("memory_limit_mb must be between 100 and 10000")
        
        # Check OCR settings
        ocr_timeout = self.get("ocr", "timeout_seconds")
        if ocr_timeout < 5 or ocr_timeout > 300:
            errors.append("ocr timeout_seconds must be between 5 and 300")
        
        if errors:
            print("Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True


if __name__ == "__main__":
    # Test configuration loading
    config = ConfigLoader()
    
    print("Default configuration loaded:")
    config.print_config()
    
    # Test getting values
    print(f"\nMax workers: {config.get('performance', 'max_workers')}")
    print(f"Enable OCR: {config.get('features', 'enable_ocr')}")
    
    # Test validation
    print(f"\nConfiguration valid: {config.validate_config()}")
    
    # Test setting values
    config.set("performance", "max_workers", 8)
    print(f"Updated max workers: {config.get('performance', 'max_workers')}")
    
    # Get processing config
    processing_config = config.get_processing_config()
    print(f"\nProcessing config: {processing_config}")
