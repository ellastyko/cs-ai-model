from utils.models import ModelManager
from transformers import ViTImageProcessor

class LocationPredictor:
    def __init__(self):
        self.processor = ViTImageProcessor.from_pretrained("google/vit-base-patch16-224")

    def predictCoordinates(self, img_path):
        self.model, _ = ModelManager.getCurrentModel()

        # Predict coordinates with image
        image = Image.open(img_path)

        inputs = self.processor(images=image, return_tensors="pt")

        with torch.no_grad():
            pixel_values = inputs["pixel_values"].to("cuda")
            outputs = self.model({"pixel_values": pixel_values})
            predicted_coords = outputs.squeeze().tolist()

            return predicted_coords[0], predicted_coords[1], predicted_coords[2], predicted_coords[3], predicted_coords[4]