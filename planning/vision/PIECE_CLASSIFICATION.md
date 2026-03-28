# Piece Classification

How to identify chess pieces from square images.

## Problem Definition

**Input:** 100×100 RGB image of a single chessboard square  
**Output:** 13-class classification (empty + 12 piece types)  
**Confidence:** Per-class probability + overall confidence score

### The Classes

```
Class 0:  [empty]          - Empty square

White Pieces (Uppercase in FEN):
Class 1:  ♔ White King
Class 2:  ♕ White Queen
Class 3:  ♖ White Rook
Class 4:  ♗ White Bishop
Class 5:  ♘ White Knight
Class 6:  ♙ White Pawn

Black Pieces (Lowercase in FEN):
Class 7:  ♚ Black King
Class 8:  ♛ Black Queen
Class 9:  ♜ Black Rook
Class 10: ♝ Black Bishop
Class 11: ♞ Black Knight
Class 12: ♟ Black Pawn
```

## Architecture: EfficientNet-B0

**Selected model:** EfficientNet-B0 (baseline)
**Rationale:**
- State-of-the-art accuracy-to-parameter ratio
- Fast inference on mobile (<5ms per image on CPU with quantization)
- Well-supported in TensorFlow/PyTorch
- Easy to convert to TFLite

### Model Architecture

```
Input: 100×100×3 RGB image (BGR in OpenCV, converted to RGB)

┌─────────────────────────────────────────────┐
│ EfficientNet-B0 Backbone                  │
│ - Pre-trained on ImageNet                   │
│ - Global Average Pooling                    │
│ - Output: 1280-dim features                 │
│ - Parameters: ~5.3M                         │
└─────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│ Classification Head                         │
│ - Dropout(0.5)                              │
│ - Dense(512, ReLU)                          │
│ - Dropout(0.3)                              │
│ - Dense(13, Softmax)                        │
└─────────────────────────────────────────────┘
                       │
                       ▼
        [13 probability scores, sum to 1.0]
```

### Alternative Models to Consider

| Model | Params | Accuracy | Latency* | Status |
|-------|--------|----------|----------|--------|
| EfficientNet-B0 | 5.3M | High | ~5ms | **Baseline** |
| MobileNetV3-L | 5.4M | Medium | ~4ms | Alternative |
| MobileNetV3-S | 2.9M | Lower | ~3ms | If B0 too slow |
| ResNet18 | 11.7M | Medium | ~8ms | Fallback |

*Latency measured on Snapdragon 865 CPU, TFLite quantized INT8

## Training Data

### Dataset Requirements

**Total Images:** 130,000  
**Breakdown:** 130 curated positions × 100 variations each

**Curated Positions:**
- Opening positions: 30
- Middle game positions: 60  
- Endgame positions: 30
- Edge case positions: 10

**Variations per position:**
- Camera angles: 20
- Lighting conditions: 20
- Piece styles: 10
- Board styles: 10
- Small random offsets: 40

### Data Generation (Blender)

```python
# Config structure for generation
# See: data_generation/API_DESIGN_PLAN.md

generation_config:
  positions:
    source: "curated/"
    count: 130
    
  camera:
    angles: [30, 45, 60]  # degrees from vertical
    distance: [1.5, 2.0, 2.5]  # meters
    random_offset: 0.1  # positional variance
    
  lighting:
    types: ["studio", "daylight", "evening"]
    intensity: [0.7, 1.0, 1.3]
    direction_variance: 30  # degrees
    
  materials:
    piece_styles: ["classic", "modern", "minimalist"]
    board_styles: ["wood_brown", "wood_green", "plastic"]
    
  output:
    image_size: [100, 100]
    format: "png"
    annotations: ["class", "piece_type", "confidence"]
```

### Data Augmentation

Applied during training:

```python
train_transforms = A.Compose([
    # Geometric
    A.Rotate(limit=15, p=0.5),  # Pieces slightly rotated
    A.ShiftScaleRotate(
        shift_limit=0.1,
        scale_limit=0.1,
        rotate_limit=0,
        p=0.5
    ),
    
    # Photometric  
    A.RandomBrightnessContrast(
        brightness_limit=0.2,
        contrast_limit=0.2,
        p=0.5
    ),
    A.HueSaturationValue(
        hue_shift_limit=10,
        sat_shift_limit=20,
        val_shift_limit=10,
        p=0.3
    ),
    
    # Noise and blur (simulates real camera)
    A.GaussianBlur(blur_limit=3, p=0.1),
    A.GaussNoise(var_limit=(10.0, 50.0), p=0.1),
    
    # Normalization
    A.Normalize(
        mean=[0.485, 0.456, 0.406],  # ImageNet
        std=[0.229, 0.224, 0.225]
    ),
])
```

### Dataset Split

| Split | Percentage | Count | Purpose |
|-------|------------|-------|---------|
| Train | 70% | 91,000 | Model training |
| Validation | 15% | 19,500 | Hyperparameter tuning |
| Test | 15% | 19,500 | Final evaluation |

Stratified by class and position type.

## Training

### Hyperparameters

```yaml
# config/efficientnet_b0.yaml
training:
  epochs: 100
  batch_size: 64
  
  optimizer:
    type: "AdamW"
    lr: 0.001
    weight_decay: 0.0001
    
  scheduler:
    type: "CosineAnnealing"
    T_max: 100
    eta_min: 0.00001
    
  loss:
    type: "CrossEntropy"
    label_smoothing: 0.1
    
  early_stopping:
    patience: 15
    metric: "val_accuracy"
    mode: "max"
```

### Training Script

```python
# train.py
import torch
import torch.nn as nn
from torchvision import models
from torch.utils.data import DataLoader

from dataset import ChessPieceDataset
from config import load_config

def train():
    # Load config
    config = load_config("config/efficientnet_b0.yaml")
    
    # Model
    model = models.efficientnet_b0(pretrained=True)
    model.classifier = nn.Sequential(
        nn.Dropout(0.5),
        nn.Linear(model.classifier[1].in_features, 512),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(512, 13)
    )
    
    # Data
    train_loader = DataLoader(
        ChessPieceDataset("data/train", transform=train_transforms),
        batch_size=config.batch_size,
        shuffle=True,
        num_workers=4
    )
    
    val_loader = DataLoader(
        ChessPieceDataset("data/val"),
        batch_size=config.batch_size,
        shuffle=False
    )
    
    # Training loop
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.lr,
        weight_decay=config.weight_decay
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=config.epochs
    )
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    
    # [Training loop implementation...]
    
    # Save best model
    torch.save(model.state_dict(), "checkpoints/best_model.pth")

if __name__ == "__main__":
    train()
```

## Evaluation

### Metrics

#### Per-Square Accuracy
```
Accuracy = (# correct predictions) / (# total squares)

Target: >98% on test set
```

#### Per-Class Accuracy
```python
from sklearn.metrics import classification_report

report = classification_report(y_true, y_pred, target_names=CLASS_NAMES)
print(report)
```

#### Confusion Matrix

Expected confusions (acceptable at low rates):
- White rook ↔ White bishop (occasionally)
- Black knight ↔ Black bishop (silhouette similarity)
- Empty squares with shadows

#### Confidence Calibration

```python
from sklearn.calibration import calibration_curve

prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=10)
# Plot to check if confidence matches accuracy
```

### Evaluation Script

```python
# evaluate.py
def evaluate(model, test_loader):
    model.eval()
    all_preds = []
    all_labels = []
    all_probs = []
    
    with torch.no_grad():
        for images, labels in test_loader:
            outputs = model(images)
            probs = torch.softmax(outputs, dim=1)
            preds = torch.argmax(outputs, dim=1)
            
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())
    
    # Calculate metrics
    accuracy = accuracy_score(all_labels, all_preds)
    per_class = precision_recall_fscore_support(
        all_labels, all_preds, average=None
    )
    
    # Confusion matrix
    cm = confusion_matrix(all_labels, all_preds)
    
    return {
        "accuracy": accuracy,
        "per_class_precision": per_class[0],
        "per_class_recall": per_class[1],
        "confusion_matrix": cm
    }
```

## Deployment

### TFLite Conversion

```python
# export_tflite.py
import torch
import tensorflow as tf

# Load PyTorch model
model = load_model("checkpoints/best_model.pth")
model.eval()

# Convert to ONNX (intermediate)
dummy_input = torch.randn(1, 3, 100, 100)
torch.onnx.export(model, dummy_input, "model.onnx",
                  input_names=["input"],
                  output_names=["output"],
                  dynamic_axes={"input": {0: "batch_size"}})

# Convert ONNX to TFLite
converter = tf.lite.TFLiteConverter.from_saved_model("model_onnx")
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.target_spec.supported_types = [tf.float16]

tflite_model = converter.convert()

# Save
with open("model_efficientnet_b0.tflite", "wb") as f:
    f.write(tflite_model)
```

### Quantization

**Post-training INT8 quantization:**

```python
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = representative_data_gen
tflite_model = converter.convert()
```

**Expected size reduction:**
- FP32: ~20MB
- FP16: ~10MB
- INT8: ~5MB

### Mobile Integration

**Android (Kotlin):**
```kotlin
class PieceClassifier(context: Context) {
    private val interpreter: Interpreter
    
    init {
        val model = FileUtil.loadMappedFile(context, "piece_classifier.tflite")
        interpreter = Interpreter(model)
    }
    
    fun classify(squareBitmap: Bitmap): ClassificationResult {
        val input = preprocess(squareBitmap)  // Normalize to [0,1]
        val output = Array(1) { FloatArray(13) }
        
        interpreter.run(input, output)
        
        val probs = output[0]
        val predictedClass = probs.indexOfMax()
        val confidence = probs[predictedClass]
        
        return ClassificationResult(predictedClass, confidence, probs)
    }
}
```

**iOS (Swift):**
```swift
import TensorFlowLite

class PieceClassifier {
    private var interpreter: Interpreter
    
    init() throws {
        interpreter = try Interpreter(modelPath: "piece_classifier.tflite")
    }
    
    func classify(squareImage: UIImage) throws -> ClassificationResult {
        let input = preprocess(squareImage)
        try interpreter.invoke()
        let output = try interpreter.output(at: 0)
        // Process output...
    }
}
```

## Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Per-square accuracy | >98% | On held-out test set |
| Inference latency | <5ms | Per square, quantized INT8 |
| Model size | <10MB | FP16 quantization |
| Batch throughput | 64 sq < 50ms | Batch processing on GPU |

## Known Challenges

### Ambiguity Cases

Some positions naturally have ambiguity:

1. **Castling rook/king position:** Rook at corner could be confused if only partial
2. **Promotion pieces:** Queens from promotion vs original queen
3. **Occlusion:** Pieces partially hidden by other pieces from angle

**Mitigation:**
- Temporal tracking across frames
- Confidence thresholding
- Manual override for ambiguous cases

### Lighting Variations

Real world has extreme lighting:
- Strong shadows
- Overexposure
- Color casts

**Mitigation:**
- Extensive lighting augmentation in training
- Exposure normalization preprocessing
- Fallback to manual input when confidence is low

## Current Status

| Component | Status | Owner |
|-----------|--------|-------|
| Dataset specification | ✅ Complete | Data team |
| Blender rendering pipeline | 🔄 In progress | Data team |
| Model architecture | ✅ Decided | CV team |
| Training implementation | ⏳ Not started | TBD |
| TFLite conversion | ⏳ Not started | TBD |
| Mobile integration | ⏳ Not started | App team |
| Evaluation framework | ⏳ Not started | TBD |

## References

- EfficientNet: "EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks" (Tan & Le, ICML 2019)
- ImageNet normalization: https://pytorch.org/vision/stable/models.html
- TFLite deployment: https://www.tensorflow.org/lite/guide
- Chess piece recognition papers: [To be added]