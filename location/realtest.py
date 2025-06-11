import torch
import torch.nn as nn
from PIL import Image
from transformers import ViTImageProcessor, ViTModel
from model import ViTRegression


# Загрузка и подготовка изображения
image = Image.open("location/cs_italy -18 2320 15 -17 329 0.296706 5.742133.jpg")
processor = ViTImageProcessor.from_pretrained("google/vit-base-patch16-224")
inputs = processor(images=image, return_tensors="pt")

# Загрузка модели
model = ViTRegression(output_dim=5)
model.load_state_dict(torch.load("location/models/cs2_location_predictor_v1.pth", map_location="cuda"))
model.to("cuda")
model.eval()

# Предсказание
with torch.no_grad():
    pixel_values = inputs["pixel_values"].to("cuda")
    outputs = model({"pixel_values": pixel_values})
    predicted_coords = outputs.squeeze().tolist()

    print(f"Predicted:")
    print(f"  X     = {predicted_coords[0]:.2f}")
    print(f"  Y     = {predicted_coords[1]:.2f}")
    print(f"  Z     = {predicted_coords[2]:.2f}")
    print(f"  Pitch = {predicted_coords[3]:.2f}")
    print(f"  Yaw   = {predicted_coords[4]:.2f}")