from transformers import ViTModel
import torch.nn as nn

class ViTRegression(nn.Module):
    def __init__(self, output_dim=5):
        super().__init__()
        self.vit = ViTModel.from_pretrained("google/vit-base-patch16-224") # change to google/vit-small-patch16-224
        self.regressor = nn.Linear(self.vit.config.hidden_size, output_dim)

    def forward(self, x):
        outputs = self.vit(**x)
        cls_token = outputs.last_hidden_state[:, 0, :]  # [CLS] токен
        return self.regressor(cls_token)
   