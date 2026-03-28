# Model Training Agent Specification
**Agent:** codex-train  
**Task:** Train YOLO + piece classifier  
**Duration:** ~4 hours

---

## OBJECTIVE
Train computer vision models for:
1. Chess board detection (YOLOv8)
2. Piece classification (CNN/ResNet)
3. Move tracking (optical flow)

---

## INPUTS

**Training Data:**
- `/workspace/shared/datasets/synthetic_renders/` (from Data Agent)
- Real board images (if available)
- Annotation files with bounding boxes

**Specifications:**
- Board detection: COCO format
- Piece classification: Directory structure per class
- Move tracking: Sequence of frames

---

## MODELS TO TRAIN

### 1. Board Detection (YOLOv8)
**Purpose:** Detect chess board in camera frame

**Dataset format:**
```
datasets/board_detection/
├── images/
│   ├── train/
│   └── val/
└── labels/
    ├── train/
    └── val/
```

**Training params:**
- Model: YOLOv8n (nano) for mobile inference
- Epochs: 100
- Batch: 16
- Image size: 640x640
- Validation split: 20%

**Success criteria:**
- mAP > 0.85
- Inference time < 50ms on CPU

---

### 2. Piece Classification (CNN)
**Purpose:** Identify piece type + color from board crops

**Classes:**
- White pieces: P, N, B, R, Q, K
- Black pieces: p, n, b, r, q, k
- Empty squares

**Architecture:**
- Base: ResNet-18 (pretrained on ImageNet)
- Fine-tune on chess pieces
- Input: 64x64 square crops

**Training params:**
- Epochs: 50
- Batch: 32
- Augmentation: rotation, scale, lighting

**Success criteria:**
- Top-1 accuracy > 0.95
- Per-class accuracy > 0.90

---

### 3. Move Tracking (Optional)
**Purpose:** Detect when moves occur

**Approach:**
- Frame differencing
- Optical flow (Farneback)
- Board state comparison

---

## OUTPUT

**Location:** `/workspace/shared/models/`

```
models/
├── board_detection/
│   ├── best.pt
│   ├── last.pt
│   └── metrics.json
├── piece_classifier/
│   ├── model.pth
│   ├── classes.txt
│   └── metrics.json
└── training_logs/
    └── training_log.csv
```

---

## WORKFLOW

1. Load training data from shared/datasets
2. Preprocess images (resize, normalize)
3. Split train/validation
4. Train board detection model
5. Evaluate on validation set
6. Train piece classifier
7. Evaluate on validation set
8. Export models to shared/models
9. Update status file
10. Generate training report

---

## INTEGRATION POINTS

**Consumes:**
- Synthetic renders from Data Agent

**Produces:**
- Trained models for CV Agent
- Metrics for reporting

---

## CHECKPOINTS

- Dataset loaded and preprocessed
- Board detection: First epoch
- Board detection: 50 epochs (mAP check)
- Board detection: Complete
- Piece classifier: First epoch
- Piece classifier: Complete
- Export models
- Status: complete

**On completion:**
- Models exported to shared/models
- Training report generated
- Status updated
- Notify CV Agent (models ready)
