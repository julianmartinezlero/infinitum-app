import json
import os
from pathlib import Path
from models.config_model import AppConfig

CONFIG_FILE = "config.json"

class ConfigManager:
    @staticmethod
    def load_config() -> AppConfig:
        if not os.path.exists(CONFIG_FILE):
            return AppConfig()
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AppConfig(**data)
        except Exception:
            return AppConfig()

    @staticmethod
    def save_config(config: AppConfig):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(config.model_dump_json(indent=4))
