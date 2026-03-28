# Technical Architecture

Complete system design for ChessScan computer vision pipeline.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INPUT: Video Stream                          │
│                     (30-60° camera angle)                            │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STAGE 1: Board Detection                           │
│                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐   │
│  │  Corner         │───▶│  Homography     │───▶│  Perspective    │   │
│  │  Detection      │    │  Estimation     │    │  Transform      │   │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘   │
│                                                                     │
│  Outputs: Rectified board image (512×512) + confidence score        │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   STAGE 2: Grid Extraction                            │
│                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐                         │
│  │  8×8 Grid       │───▶│  64 Square      │                         │
│  │  Subdivision    │    │  Crops (100×100)│                         │
│  └─────────────────┘    └─────────────────┘                         │
│                                                                     │
│  Output: 64 individual square images, normalized & augmented        │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 STAGE 3: Piece Classification                         │
│                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐                         │
│  │  CNN            │───▶│  13-class       │                         │
│  │  (EfficientNet) │    │  Prediction     │                         │
│  └─────────────────┘    └─────────────────┘                         │
│                                                                     │
│  Classes: ♔♕♖♗♘♙ ♚♛♜♝♞♟ empty (13 total)                          │
│  Output: Class probabilities + confidence for each square          │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 STAGE 4: Board State Assembly                         │
│                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐   │
│  │  Square-level   │───▶│  Board State    │───▶│  FEN Generation │   │
│  │  Results        │    │  Construction   │    │                 │   │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘   │
│                                                                     │
│  Output: FEN string representing current board position             │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                STAGE 5: Temporal Tracking                           │
│                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐   │
│  │  Frame-to-frame │───▶│  Move Detection │───▶│  State Update   │   │
│  │  Comparison     │    │  & Validation   │    │                 │   │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘   │
│                                                                     │
│  Output: Detected move (e2-e4), SAN notation, confidence            │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Specifications

### Board Detection Module

**Purpose:** Find the 4 corners of the chess board in an arbitrary camera view

**Approach Options:**

| Approach | Method | Pros | Cons | Status |
|----------|--------|------|------|--------|
| A | Classical (Hough + Grid) | Fast, no training | Fragile to clutter | Evaluating |
| B | Keypoint Detection (CornerNet) | Robust, learned | Needs training data | Preferred |
| C | Segmentation (U-Net) | Handles occlusion | Slower, complex | Backup |

**Selected:** Approach B (Keypoint Detection)

**Architecture:**
- Input: 640×480 video frame
- Backbone: MobileNetV2 (lightweight)
- Heads: 4 corner heatmaps + corner presence confidence
- Output: (x,y) coordinates for each corner + presence flags

**Training Data:**
- Synthetic: Blender-generated boards at various angles
- Real: 1,000 annotated real-world photos
- Augmentation: Lighting, slight color shifts, noise

### Perspective Rectification

**Purpose:** Transform skewed board to orthogonal view

**Algorithm:**
```python
# Homography estimation from 4 corners
src_points = detected_corners  # [4, 2]
dst_points = [[0, 0], [512, 0], [512, 512], [0, 512]]  # square output

H, _ = cv2.findHomography(src_points, dst_points, cv2.RANSAC, 5.0)
rectified = cv2.warpPerspective(frame, H, (512, 512))
```

**Quality Check:**
- Verify output has parallel edges (within 2°)
- Check for excessive distortion (homography determinant bounds)
- Confidence score based on corner detection quality

### Grid Subdivision

**Purpose:** Extract 64 individual square images from rectified board

**Algorithm:**
```
Board: 512×512 pixels
Square size: 64×64 pixels (512/8)
Extraction: 100×100 pixels (32px padding for context)

for rank in 0..7:
    for file in 0..7:
        x1 = file * 64 - 18  # padded coordinates
        y1 = rank * 64 - 18
        x2 = x1 + 100
        y2 = y1 + 100
        square = board[y1:y2, x1:x2]
```

**Note:** Additional padding captures piece context and handles small rectification errors.

### Piece Classification Model

**Purpose:** Identify piece type and color for each of 64 squares

**Architecture:**
```
Input: 100×100 RGB image (square crop)

┌─────────────────────────────────────┐
│ EfficientNet-B0                     │
│ - Pre-trained on ImageNet           │
│ - Fine-tuned on chess pieces        │
│ - Output: 1280-dim features         │
└─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│ Classification Head                 │
│ - Dense(512, ReLU)                  │
│ - Dropout(0.5)                      │
│ - Dense(13, Softmax)                │
└─────────────────────────────────────┘
                │
                ▼
        [13-class probabilities]
```

**Output Classes:**
```
Index 0:  Empty square
Index 1:  ♔ White King
Index 2:  ♕ White Queen
Index 3:  ♖ White Rook
Index 4:  ♗ White Bishop
Index 5:  ♘ White Knight
Index 6:  ♙ White Pawn
Index 7:  ♚ Black King
Index 8:  ♛ Black Queen
Index 9:  ♜ Black Rook
Index 10: ♝ Black Bishop
Index 11: ♞ Black Knight
Index 12: ♟ Black Pawn
```

**Training Details:**
- Dataset: 130,000 synthetic images (see data_generation/)
- Optimizer: AdamW, lr=1e-4 with cosine decay
- Augmentation: Rotation (±15°), brightness, contrast, blur
- Target accuracy: >98% per-square accuracy
- Inference time: <5ms per square on mobile CPU

### Temporal Tracking Module

**Purpose:** Stable move detection across frames, handle temporary occlusions

**State Machine:**
```
States:
  - STATIC: Board unchanged
  - CHANGING: Pieces moving (ignore)
  - UNSTABLE: Detection confidence low

Transitions:
  STATIC → CHANGING: 2+ squares differ from last stable state
  CHANGING → STATIC: Board stable for N frames (N=3)
  ANY → UNSTABLE: Confidence below threshold
```

**Move Detection:**
```
Compare current_stable_state vs previous_stable_state:

- If 2 squares changed: potential move
  - Validate: Is it legal chess move?
  - If valid: record move
  - If invalid: require manual input or retry

- If 1 square changed: capture (verify)
- If >2 squares changed: likely motion blur, skip
```

## Data Flow Summary

```
Frame (640×480) → Board Detection → Rectified (512×512)
                → Grid Extraction → 64 Squares (100×100 each)
                → Classification   → 64 Predictions (13-class each)
                → State Assembly   → FEN string
                → Temporal Track   → Move detected (SAN)
```

## Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| End-to-end latency | <200ms | Per frame processing |
| Board detection | >95% accuracy | Corner within 5px |
| Piece classification | >98% per-square | Tested on held-out set |
| Move detection | <2s response | From move completion |
| Memory usage | <200MB | Mobile device constraint |
| Model size | <20MB | TFLite quantized |

## Error Handling

**Board Detection Failures:**
- No corners detected → Skip frame, use previous state
- Low confidence (<0.7) → Skip frame, log warning
- Excessive distortion → Request board repositioning

**Classification Failures:**
- Square confidence <0.6 → Mark as "unknown", don't update state
- Multiple frames with unknown → Request manual input

**Move Validation Failures:**
- Illegal move detected → Flag for review, don't auto-accept
- Ambiguous state → Present top 3 candidates to user

## Integration Points

### Mobile App (<-> CV Pipeline)
- Native camera feed (platform-specific)
- Frame extraction at 5-10 FPS
- CV results → Flutter via MethodChannel
- State updates trigger UI refresh

### Data Generation (<-> Model Training)
- Blender Python API for rendering
- COCO format export for detection training
- Custom format for classification training
- GitHub Actions for dataset versioning

## References

- EfficientNet: Tan & Le, ICML 2019
- CornerNet: Law & Deng, ECCV 2018
- Homography estimation: Hartley & Zisserman (book)
- Chess piece recognition: [cite relevant papers if any]