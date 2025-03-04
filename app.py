# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 03:25:39 2025

@author: momin
"""

from flask import Flask, request, send_file
import torch
import io
import os
import cv2
import numpy as np
from PIL import Image
from flask_cors import CORS


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


# Load YOLOv5 model from local file or Google Drive if not present
model_path = "best.pt"
print("🔍 Checking if best.pt exists...")

if not os.path.exists(model_path):
    print("❌ ERROR: best.pt NOT FOUND!")
    exit(1)  # Stop execution if best.pt is missing
else:
    print("✅ best.pt found. Loading YOLOv5...")
    import torch
import os

# Define the cache directory for YOLOv5
torch.hub.set_dir("/opt/render/.cache/torch/hub")  

model = torch.hub.load(
    'ultralytics/yolov5', 
    'custom', 
    path=model_path, 
    trust_repo=True,  # Trust the repository
    force_reload=False  # Prevent unnecessary downloads
)
print("✅ Model loaded successfully!")
    
if not os.path.exists(model_path):
    import gdown
    url = "https://drive.google.com/uc?id=YOUR_FILE_ID"  # Replace with Google Drive file ID
    gdown.download(url, model_path, quiet=False)

model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path, trust_repo=True, force_reload=False)


@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return "No file uploaded", 400

    file = request.files['file']
    image = Image.open(io.BytesIO(file.read()))

    # Perform inference
    results = model(image)

    # Convert detections to JSON
    detections = results.pandas().xyxy[0].to_dict(orient="records")

    # Draw bounding boxes
    img = np.array(image)
    for det in detections:
        x1, y1, x2, y2 = int(det["xmin"]), int(det["ymin"]), int(det["xmax"]), int(det["ymax"])
        conf, cls = det["confidence"], det["name"]
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img, f"{cls} {conf:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Convert back to image
    output_image = Image.fromarray(img)

    # ✅ Ensure image is in RGB mode (Fix for PNG with transparency)
    if output_image.mode != "RGB":
        output_image = output_image.convert("RGB")  # <-- Correct indentation

    # Save as JPEG  
    img_io = io.BytesIO()
    output_image.save(img_io, format="JPEG")
    img_io.seek(0)

    return send_file(img_io, mimetype='image/jpeg')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Use Render's assigned PORT
    print(f"🚀 Running Flask on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
