import torch
import os
import torch.nn as nn
from tqdm import tqdm
from torch.utils.data import Dataset
import re
from PIL import Image
from torch.utils.data import DataLoader
from transformers import ViTImageProcessor, ViTModel

# Парсинг названия файла
def parse_filename(filename):
    # Пример названия: "cs_italy -1 -1225 196 15 200 -0.261799 3.490659.jpg"
    pattern = r"(.+?) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?[\d.]+) (-?[\d.]+)\.jpg"
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
    

class ViTRegression(nn.Module):
    def __init__(self):
        super().__init__()
        self.vit = ViTModel.from_pretrained("google/vit-base-patch16-224")
        self.regressor = nn.Linear(self.vit.config.hidden_size, 5)

    def forward(self, x):
        outputs = self.vit(**x)
        return self.regressor(outputs.last_hidden_state[:, 0, :])

def test_model(model, test_loader, device="cuda"):
    model.to(device)
    model.eval()
    criterion = nn.MSELoss()
    test_loss = 0.0

    with torch.no_grad():
        for batch in tqdm(test_loader, desc="Testing"):
            inputs, labels = batch
            inputs = {k: v.to(device) for k, v in inputs.items()}
            labels = labels.to(device)

            outputs = model(inputs)
            loss = criterion(outputs, labels)
            test_loss += loss.item()

    avg_test_loss = test_loss / len(test_loader)
    print(f"Test Loss (MSE): {avg_test_loss:.4f}")

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

feature_extractor = ViTImageProcessor.from_pretrained("google/vit-base-patch16-224")

# Загрузка тестового датасета
test_dataset = CS2Dataset("dataset/test", feature_extractor)
test_loader = DataLoader(test_dataset, batch_size=16, shuffle=False)

# 3. Загрузка весов (если есть)
model = ViTRegression()
model.load_state_dict(torch.load("location/models/cs2_location_predictor_v1.pth"))  # Пример пути
model.eval()

# Тестирование
test_model(model, test_loader, device=device)