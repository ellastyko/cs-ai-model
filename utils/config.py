import json
import os

class ConfigManager:
    _config_path = "config.json"
    _config = {}

    @classmethod
    def _load(cls):
        if not os.path.exists(cls._config_path):
            cls._config = {}
            cls._save()
        else:
            try:
                with open(cls._config_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    cls._config = json.loads(content) if content else {}
            except (json.JSONDecodeError, IOError):
                print("[ConfigManager] Ошибка чтения config.json. Используется пустой конфиг.")
                cls._config = {}

    @classmethod
    def _save(cls):
        try:
            with open(cls._config_path, "w", encoding="utf-8") as f:
                json.dump(cls._config, f, indent=4, ensure_ascii=False)
        except IOError:
            print("[ConfigManager] Ошибка записи config.json.")

    @classmethod
    def get(cls, key, default=None):
        if not cls._config:
            cls._load()
        return cls._config.get(key, default)

    @classmethod
    def set(cls, key, value):
        cls._config[key] = value
        cls._save()

    @classmethod
    def delete(cls, key):
        if key in cls._config:
            del cls._config[key]
            cls._save()
