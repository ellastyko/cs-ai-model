import json
import os
from typing import Dict, Any, List

class MapManager:
    _instance = None
    ASSETS_DIR = './assets/maps/'
    _maps: Dict[str, Dict[str, Any]] = {}
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MapManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    @classmethod
    def _initialize(cls):
        """Инициализирует менеджер (вызывается автоматически при первом использовании)"""
        if not cls._initialized:
            cls._load_all_maps()
            cls._initialized = True
    
    @classmethod
    def _load_all_maps(cls):
        """Загружает все карты из директории"""
        cls._maps.clear()
        
        if not os.path.exists(cls.ASSETS_DIR):
            os.makedirs(cls.ASSETS_DIR, exist_ok=True)
            return
        
        map_files = [
            f for f in os.listdir(cls.ASSETS_DIR) 
            if f.endswith('.json') and os.path.isfile(os.path.join(cls.ASSETS_DIR, f))
        ]
        
        for map_file in map_files:
            map_name = os.path.splitext(map_file)[0]
            with open(os.path.join(cls.ASSETS_DIR, map_file), 'r', encoding='utf-8') as f:
                cls._maps[map_name] = json.load(f)
    
    @staticmethod
    def get_available_maps() -> List[str]:
        """Возвращает список доступных карт"""
        MapManager._initialize()
        return list(MapManager._maps.keys())
    
    @staticmethod
    def get_map(map_name: str) -> Dict[str, Any]:
        """
        Возвращает данные карты по имени
        :param map_name: Название карты (без расширения)
        :raises KeyError: Если карта не существует
        """
        MapManager._initialize()
        
        if map_name not in MapManager._maps:
            available = MapManager.get_available_maps()
            raise KeyError(f"Map '{map_name}' not found. Available maps: {available}")
        
        return MapManager._maps[map_name]
    
    @staticmethod
    def reload_maps():
        """Перезагружает все карты из файлов"""
        MapManager._load_all_maps()