import os
import torch
from torch.utils.data import Dataset
from utils.dataset import CS2Dataset
import matplotlib.pyplot as plt
from transformers import ViTImageProcessor 
import torch.nn as nn
from torch.optim import AdamW, lr_scheduler
from torch.utils.data import DataLoader
from tqdm import tqdm
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime
from model import ViTRegression

def train_model(model, train_loader, val_loader, epochs=10, lr=5e-5, device="cuda"):
    model.to(device)
    optimizer = AdamW(model.parameters(), lr=lr)
    scheduler = lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.1)  # Планировщик LR
    criterion = nn.MSELoss()
    
    best_val_loss = float('inf')
    train_losses = []
    val_losses = []
    
    # Создаем папку для сохранения моделей
    os.makedirs("saved_models", exist_ok=True)
    
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
        
        scheduler.step()
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
        
        print(f"Epoch {epoch + 1}: Train Loss = {avg_train_loss:.4f}, Val Loss = {avg_val_loss:.4f}, LR = {scheduler.get_last_lr()[0]:.2e}")
        
        # Сохраняем модели начиная с 5 эпохи
        if epoch >= 4:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_path = f"saved_models/model_epoch{epoch+1}_{timestamp}.pth"
            torch.save(model.state_dict(), model_path)
            print(f"Model saved to {model_path}")
            
            # Сохраняем лучшую модель
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                torch.save(model.state_dict(), "saved_models/best_model.pth")
                print("New best model saved!")

    return train_losses, val_losses

def plot_losses(train_losses, val_losses):
    plt.figure(figsize=(10, 5))
    plt.plot(train_losses, label="Train Loss")
    plt.plot(val_losses, label="Validation Loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss (MSE)")
    plt.legend()
    plt.title("Training and Validation Loss")
    plt.savefig("training_plot.png")  # Сохраняем график
    plt.show()

if __name__ == "__main__":
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # Инициализация с ViTImageProcessor вместо ViTFeatureExtractor
    feature_extractor = ViTImageProcessor.from_pretrained("google/vit-small-patch16-224")
    
    # Нормализация данных (пример)
    scaler = MinMaxScaler(feature_range=(-1, 1))
    
    # Создание датасетов
    train_dataset = CS2Dataset("location/dataset/train", feature_extractor, scaler)
    val_dataset = CS2Dataset("location/dataset/validation", feature_extractor, scaler)
    
    # DataLoader с увеличенным num_workers
    train_loader = DataLoader(
        train_dataset,
        batch_size=32,
        shuffle=True,
        num_workers=4,
        pin_memory=True
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=32,
        shuffle=False,
        num_workers=4,
        pin_memory=True
    )
    
    # Модель
    model = ViTRegression()
    
    # Обучение
    train_losses, val_losses = train_model(
        model,
        train_loader,
        val_loader,
        epochs=15,  # Увеличили количество эпох
        lr=3e-5,   # Немного уменьшили learning rate
        device=device
    )
    
    # График потерь
    plot_losses(train_losses, val_losses)
    
    # Сохранение финальной модели
    torch.save(model.state_dict(), "final_model.pth")