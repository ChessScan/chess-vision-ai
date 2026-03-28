# Board Detection

How to detect the chess board from an angled camera view.

## Problem Definition

**Input:** Video frame with chess board visible at 30-60° angle  
**Output:** 4 corner points (x,y) defining the board quadrilateral  
**Confidence:** 0.0-1.0 score indicating detection quality

### Challenge: Perspective Distortion

At shallow angles, the board appears as a trapezoid, not a rectangle:
- Far edge appears shorter than near edge
- Vertical lines converge toward a vanishing point
- Background may contain other objects

## Approaches

### Option A: Classical Computer Vision

**Pipeline:**
```
Grayscale → Gaussian Blur → Canny Edges → Hough Lines
    │                                          │
    │                                          ▼
    │                                Line Clustering
    │                                (find parallel sets)
    │                                          │
    └──────────────┬───────────────────────────┘
                   ▼
            Intersection Finding
            (compute line intersections)
                   │
                   ▼
            Corner Filtering
            (filter to 4 corners via heuristics)
                   │
                   ▼
            Grid Validation
            (verify 8×8 interior intersections)
```

**Pros:**
- No training data required
- Fast execution (10-20ms)
- Deterministic, explainable

**Cons:**
- Fragile to background clutter
- Sensitive to lighting changes
- Requires clean board/contrast
- Fails with hands/pieces casting shadows

**When to use:** Controlled environments, clean backgrounds

**Implementation Notes:**
```python
import cv2
import numpy as np

def detect_board_classical(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, 
                            minLineLength=100, maxLineGap=10)
    
    # Cluster lines by angle to find 2 orthogonal directions
    # Find intersections, filter to 4 board corners
    # Validate by checking internal grid pattern
    
    return corners, confidence
```

**Status:** Reference implementation available as baseline

---

### Option B: Keypoint Detection (RECOMMENDED)

**Approach:** Train a CNN to directly predict corner locations as heatmaps

**Architecture:**
```
Input: 640×480 image

┌─────────────────────────────────────────┐
│ MobileNetV2 Backbone                  │
│ - Pre-trained on ImageNet               │
│ - Output stride: 16 (40×30 features)    │
└─────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│ Deconvolution Head                    │
│ - Upsample to 160×120 resolution        │
└─────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│ 4 Heatmap Heads (one per corner)      │
│ - Each outputs 160×120 probability map  │
│ - Peak location = corner position       │
│ - Peak value = presence confidence      │
└─────────────────────────────────────────┘
```

**Training:**
- **Synthetic data:** Blender generate boards at random angles (0-60°)
- **Real data:** 1,000 manually annotated photos
- **Augmentation:** Lighting, color jitter, blur, occlusion

**Loss Function:**
```python
def corner_loss(pred_heatmap, gt_heatmap, gt_visible):
    # Focal loss for heatmap regression
    heatmap_loss = focal_loss(pred_heatmap, gt_heatmap)
    
    # Binary cross-entropy for visibility
    visible_loss = bce(pred_visibility, gt_visible)
    
    return heatmap_loss + 0.1 * visible_loss
```

**Inference:**
```python
def predict_corners(model, frame):
    heatmaps = model(frame)  # [4, 160, 120]
    
    corners = []
    confidences = []
    
    for i in range(4):
        # Find peak location
        y, x = np.unravel_index(np.argmax(heatmaps[i]), heatmaps[i].shape)
        confidence = heatmaps[i, y, x]
        
        # Scale to original image coordinates
        corner_x = x * (frame.shape[1] / 160)
        corner_y = y * (frame.shape[0] / 120)
        
        corners.append((corner_x, corner_y))
        confidences.append(confidence)
    
    overall_confidence = np.mean(confidences)
    return corners, overall_confidence
```

**Pros:**
- Robust to clutter and lighting
- Learns board appearance patterns
- Handles partial occlusion
- Better user experience

**Cons:**
- Requires training data
- Slightly slower (50-100ms on mobile)
- Model size (~5MB)

**Status:** Primary approach under development

---

### Option C: Segmentation-Based

**Approach:** Segment the board region, then fit rectangle

**Architecture:** U-Net or DeepLab for binary segmentation

**Pros:** Very robust to occlusion
**Cons:** Expensive inference, post-processing complexity

**Status:** Not currently pursued (overkill for problem)

---

## Selected Approach: Option B (Keypoint Detection)

### Milestones

| Phase | Deliverable | Target |
|-------|-------------|--------|
| 1 | Synthetic dataset (10k images) | Week 1 |
| 2 | Model training (baseline) | Week 2 |
| 3 | Real data collection (1k images) | Week 3 |
| 4 | Fine-tuning & optimization | Week 4 |
| 5 | TFLite conversion & mobile test | Week 5 |

### Model Specifications

```yaml
board_detector:
  backbone: mobilenetv2
  input_size: [480, 640, 3]
  output_stride: 16
  heatmap_size: [120, 160]
  num_corners: 4
  
  training:
    batch_size: 32
    learning_rate: 0.001
    epochs: 100
    optimizer: adam
    
  augmentation:
    rotation: [-30, 30]
    scale: [0.8, 1.2]
    brightness: [0.8, 1.2]
    contrast: [0.8, 1.2]
    blur: [0, 3]  # Gaussian blur sigma
```

### Evaluation Metrics

```python
# Corner error (Euclidean distance)
def corner_error(pred, gt):
    return np.sqrt(((pred - gt) ** 2).sum(axis=1))

# Success rate at threshold
def success_rate(errors, threshold=5.0):
    """Percent of corners within 5 pixels of ground truth"""
    return (errors < threshold).mean()

# Board detection rate (all 4 corners correct)
def detection_rate(errors, threshold=5.0):
    """Percent of images where all corners within threshold"""
    per_image_max = errors.reshape(-1, 4).max(axis=1)
    return (per_image_max < threshold).mean()
```

**Target Metrics:**
- Corner error (mean): <3 pixels
- Success @ 5px: >95%
- Detection rate: >90%

### Homography Validation

After detecting corners, validate the homography:

```python
def validate_homography(corners, image_shape):
    """Check if detected board is reasonable"""
    
    # Check corner ordering (clockwise)
    # Order: top-left, top-right, bottom-right, bottom-left
    
    # Check aspect ratio (chess boards are square)
    # Compute side lengths, should be within 30% of each other
    
    # Check convexity
    # Polygon should be convex
    
    # Check size (board should fill reasonable portion of image)
    board_area = polygon_area(corners)
    image_area = image_shape[0] * image_shape[1]
    
    if board_area < image_area * 0.1:
        return False, "Board too small"
    if board_area > image_area * 0.9:
        return False, "Board too large (likely false positive)"
    
    return True, "OK"
```

## Integration with Pipeline

```python
class BoardDetector:
    def __init__(self, model_path):
        self.model = load_tflite_model(model_path)
        self.last_corners = None
        self.last_confidence = 0.0
    
    def detect(self, frame):
        corners, confidence = self.model.predict(frame)
        
        # Validation
        if confidence < 0.5:
            return self.last_corners, self.last_confidence, "LOW_CONFIDENCE"
        
        valid, reason = validate_homography(corners, frame.shape)
        if not valid:
            return self.last_corners, self.last_confidence, reason
        
        # Temporal smoothing
        if self.last_corners is not None:
            corners = self._smooth(corners, self.last_corners)
        
        self.last_corners = corners
        self.last_confidence = confidence
        
        return corners, confidence, "OK"
    
    def _smooth(self, current, previous, alpha=0.7):
        """Exponential moving average for temporal stability"""
        return alpha * current + (1 - alpha) * previous
```

## References

- MobileNetV2: Sandler et al., CVPR 2018
- CornerNet: Law & Deng, ECCV 2018
- DeepLab: Chen et al., TPAMI 2017
- OpenCV homography tutorial: docs.opencv.org