import os
import torch
from ai.location.model import ViTRegression
import torch
from typing import Dict, Optional

class ModelManager:
    _instance = None
    MODELS_DIR = 'ai/location/models'
    
    # Статические поля класса
    _models_cache: Dict[str, torch.nn.Module] = {}
    _current_model_name: Optional[str] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            # Инициализация при первом создании
            cls._ensure_models_dir_exists()
        return cls._instance
    
    @classmethod
    def _ensure_models_dir_exists(cls):
        if not os.path.exists(cls.MODELS_DIR):
            os.makedirs(cls.MODELS_DIR)

    @classmethod
    def getFullPath(cls, model_name: str) -> Optional[str]:
        # Получить полный путь к модели по имени
        if not model_name.endswith('.pth'):
            model_name += '.pth'
        path = os.path.join(cls.MODELS_DIR, model_name)

        return path if os.path.isfile(path) else None

    @classmethod
    def list(cls) -> list:
        """Список доступных моделей"""
        return [f for f in os.listdir(cls.MODELS_DIR) if f.endswith(".pth")]
    
    @classmethod
    def getCurrentModel(cls):
        """Возвращает текущую модель и её имя"""
        if cls._current_model_name:
            return cls._models_cache[cls._current_model_name], cls._current_model_name
        return None, None
    
    @classmethod
    def switchModel(cls, model_name: str) -> Optional[torch.nn.Module]:
        """Переключает текущую модель"""
        if cls._current_model_name == model_name:
            return cls._models_cache[model_name]
        return cls.upload(model_name)

    @classmethod
    def upload(cls, model_name):
        """Загружает и кэширует модель"""
        if model_name in cls._models_cache:
            cls._current_model_name = model_name
            return cls._models_cache[model_name]
        
        model_path = cls.getFullPath(model_name)
        if not model_path:
            return None
        
        # Загрузка новой модели
        try:
            # Upload model
            model = ViTRegression(output_dim=5)
            model.load_state_dict(torch.load(model_path, map_location="cuda"))
            model.to("cuda")
            model.eval()

            cls._models_cache[model_name] = model
            cls._current_model_name = model_name
            return model
        except Exception as e:
            print(f"Error loading model {model_name}: {str(e)}")
            return None
        
    @classmethod
    def clear_cache(cls):
        """Очищает кэш моделей"""
        cls._models_cache.clear()
        cls._current_model_name = None
        torch.cuda.empty_cache()
