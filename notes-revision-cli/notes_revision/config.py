import json
import os
from pathlib import Path

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "notes-revision"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "notes_dir": "/Users/aks/Desktop/notes",
    "smtp": {
        "server": "smtp.gmail.com",
        "port": 587,
        "use_tls": True,
        "username": "YOUR_EMAIL@gmail.com",
        "password": "YOUR_APP_PASSWORD"
    },
    "recipient_email": "YOUR_EMAIL@gmail.com",
    "sender_name": "Notes Revision Bot 🧠",
    "notes_per_email": 2,
    "selection_strategy": "category_balanced", # Options: "category_balanced", "lru", "random", "spaced_repetition"
    "max_note_length_chars": 12000,
    "exclude_dirs": [".git", "Excalidraw", "screenshots", "node_modules", ".venv", ".gemini", "notes-revision-cli"],
    "exclude_files": [".DS_Store", "todo.md", "study-topics.txt", "config.json", ".revision_state.json", "REVISION_SYSTEM_README.md"]
}

class ConfigManager:
    @staticmethod
    def get_config_path(custom_path: str = None) -> Path:
        if custom_path:
            return Path(custom_path).resolve()
        return DEFAULT_CONFIG_PATH

    @staticmethod
    def load_config(custom_path: str = None) -> tuple:
        """Returns (config_dict, config_path)"""
        cfg_path = ConfigManager.get_config_path(custom_path)
        if cfg_path.exists():
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    user_cfg = json.load(f)
                    merged = DEFAULT_CONFIG.copy()
                    merged.update(user_cfg)
                    return merged, cfg_path
            except Exception as e:
                print(f"⚠️ Warning: Could not read config file at {cfg_path}: {e}. Using defaults.")
        return DEFAULT_CONFIG.copy(), cfg_path

    @staticmethod
    def init_config(custom_path: str = None, notes_dir: str = None) -> Path:
        cfg_path = ConfigManager.get_config_path(custom_path)
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        
        cfg = DEFAULT_CONFIG.copy()
        if notes_dir:
            cfg["notes_dir"] = str(Path(notes_dir).resolve())

        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
            
        return cfg_path
