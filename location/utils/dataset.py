import os
import torch
from torch.utils.data import Dataset
from PIL import Image
import re

class CS2Dataset(Dataset):
    def __init__(self, root_dir, feature_extractor, max_samples=None):
        self.root_dir = root_dir
        self.feature_extractor = feature_extractor
        self.samples = []

        # Собираем все изображения
        for map_name in os.listdir(root_dir):
            map_dir = os.path.join(root_dir, map_name)
            if not os.path.isdir(map_dir):
                continue

            for filename in os.listdir(map_dir):
                if filename.endswith(".jpg"):
                    metadata = parse_filename(filename)
                    img_path = os.path.join(map_dir, filename)
                    self.samples.append((img_path, metadata))

                    if max_samples and len(self.samples) >= max_samples:
                        break

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, metadata = self.samples[idx]
        image = Image.open(img_path).convert("RGB")

        # Нормализуем метки (если нужно)
        labels = torch.tensor([
            metadata["x"],
            metadata["y"],
            metadata["z"],
            metadata["pitch"],
            metadata["yaw"],
        ], dtype=torch.float32)

        # Преобразуем изображение через ViTFeatureExtractor
        inputs = self.feature_extractor(image, return_tensors="pt")
        inputs = {k: v.squeeze(0) for k, v in inputs.items()}  # Убираем batch dimension

        return inputs, labels
    

# Парсинг названия файла
def parse_filename(filename):
    # cs_italy -521 -1071 -164 -2.00 68.44 -0.261799 3.490659.JPG
    pattern = r"^(.+?) (-?[\d.]+) (-?[\d.]+) (-?[\d.]+) (-?[\d.]+) (-?[\d.]+) (-?[\d.]+) (-?[\d.]+)\.(jpg|JPG)$"
    # pattern = r"(.+?) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?[\d.]+) (-?[\d.]+)\.jpg$"

    match = re.match(pattern, filename)
    if match:
        return {
            "map": match.group(1),
            "x": float(match.group(2)),
            "y": float(match.group(3)),
            "z": float(match.group(4)),
            "denormalizedPitch": float(match.group(5)),
            "denormalizedYaw": float(match.group(6)),
            "pitch": float(match.group(7)),
            "yaw": float(match.group(8)),
        }
    else:
        raise ValueError(f"Не удалось распарсить название файла: {filename}")