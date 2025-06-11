import os
import torch
from torch.utils.data import Dataset
from utils.dataset import CS2Dataset
from PIL import Image
import pandas as pd
import matplotlib.pyplot as plt
from transformers import ViTModel, ViTFeatureExtractor
import torch.nn as nn
from torch.optim import AdamW
from torch.utils.data import DataLoader
import numpy as np
from sklearn.model_selection import train_test_split
from tqdm import tqdm
from model import ViTRegression
    
def train_model(model, train_loader, val_loader, epochs=10, lr=5e-5, device="cuda"):
    model.to(device)
    optimizer = AdamW(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    train_losses = []
    val_losses = []

    for epoch in range(epochs):
        model.train()
        epoch_train_loss = 0.0
        for batch in tqdm(train_loader, desc=f"Epoch {epoch + 1}/{epochs} (Train)"):
            inputs, labels = batch
            inputs = {k: v.to(device) for k, v in inputs.items()}
            labels = labels.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            epoch_train_loss += loss.item()

        avg_train_loss = epoch_train_loss / len(train_loader)
        train_losses.append(avg_train_loss)

        # Валидация
        model.eval()
        epoch_val_loss = 0.0
        with torch.no_grad():
            for batch in tqdm(val_loader, desc=f"Epoch {epoch + 1}/{epochs} (Val)"):
                inputs, labels = batch
                inputs = {k: v.to(device) for k, v in inputs.items()}
                labels = labels.to(device)

                outputs = model(inputs)
                loss = criterion(outputs, labels)
                epoch_val_loss += loss.item()

        avg_val_loss = epoch_val_loss / len(val_loader)
        val_losses.append(avg_val_loss)

        print(f"Epoch {epoch + 1}: Train Loss = {avg_train_loss:.4f}, Val Loss = {avg_val_loss:.4f}")

    return train_losses, val_losses

def plot_losses(train_losses, val_losses):
    plt.figure(figsize=(10, 5))
    plt.plot(train_losses, label="Train Loss")
    plt.plot(val_losses, label="Validation Loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss (MSE)")
    plt.legend()
    plt.title("Training and Validation Loss")
    plt.show()

if __name__ == "__main__":
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    # Загрузка feature extractor ViT
    feature_extractor = ViTFeatureExtractor.from_pretrained("google/vit-base-patch16-224")

    # Создание датасетов
    train_dataset = CS2Dataset("location/dataset/train", feature_extractor)
    val_dataset = CS2Dataset("location/dataset/validation", feature_extractor)

    # DataLoader
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=16, shuffle=False)

    # Модель
    model = ViTRegression()

    # Обучение
    train_losses, val_losses = train_model(
        model,
        train_loader,
        val_loader,
        epochs=10,
        lr=5e-5,
        device=device
    )

    # График потерь
    plot_losses(train_losses, val_losses)

    # Сохранение модели
    torch.save(model.state_dict(), "cs2_location_predictor.pth")
