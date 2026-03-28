# CV Pipeline Agent Specification
**Agent:** codex-cv  
**Task:** Build CV pipeline module  
**Duration:** ~3 hours

---

## OBJECTIVE
Build complete computer vision pipeline:
Camera → Board Detection → Piece Classification → Move Tracking → FEN Export

---

## PIPELINE STAGES

### Stage 1: Camera Capture
**Input:** Device camera (iOS/Android)
**Output:** Frames (1280x720, 30fps)
**Tech:** Platform channels to native camera

### Stage 2: Board Detection
**Input:** Camera frame (RGB)
**Output:** Board bounding box + corner coordinates
**Tech:** YOLOv8 (from Train Agent)
**Performance:** < 50ms per frame

### Stage 3: Board Normalization
**Input:** Board bbox + frame
**Output:** Normalized board (64x64 grid)
**Tech:** Perspective transform (OpenCV)
**Steps:**
1. Crop board region
2. Apply perspective correction
3. Extract 64 squares

### Stage 4: Piece Classification
**Input:** 64 square images (64x64)
**Output:** Board state matrix (8x8 pieces)
**Tech:** ResNet-18 classifier (from Train Agent)
**Performance:** < 100ms for all 64 squares

### Stage 5: FEN Generation
**Input:** Board state matrix
**Output:** FEN string
**Tech:** Chess library
**Validation:** Legal position check

### Stage 6: Move Detection
**Input:** Sequential FENs
**Output:** Move notation (e.g., "e2e4")
**Detection:** State diff between frames
**Filtering:** Debounce (wait for stable position)

### Stage 7: Game Export
**Input:** List of moves
**Output:** PGN format
**Additional:** Meta-data (player names, date, event)

---

## ARCHITECTURE

```
camera_frame ──┬─→ Board Detector ──→ Board Crop ──→ Square Extractor
               │       (YOLOv8)           (OpenCV)        (Grid split)
               │                                     ↓
               │                         Piece Classifier ──→ Board State
               │                           (ResNet-18)
               │                                     ↓
               └──────────────────────→ Move Detector ──→ FEN/PNG
                                         (State diff)
```

---

## IMPLEMENTATION

**Language:** Python (shared) + Dart (Flutter integration)
**Location:** `/workspace/agents/cv-agent/`
**Export:** `cv_pipeline/` module

**Core classes:**
```python
class BoardDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
    
    def detect(self, frame) -> BoardBBox:
        ...

class PieceClassifier:
    def __init__(self, model_path):
        self.model = load_model(model_path)
    
    def classify(self, square_image) -> Piece:
        ...

class Pipeline:
    def __init__(self, detector, classifier):
        self.detector = detector
        self.classifier = classifier
        self.state_history = []
    
    def process_frame(self, frame) -> PipelineResult:
        board = self.detector.detect(frame)
        squares = self.extract_squares(frame, board)
        state = self.classify_squares(squares)
        fen = self.state_to_fen(state)
        move = self.detect_move(state)
        return PipelineResult(fen=fen, move=move)
```

---

## INTEGRATION POINTS

**Consumes:**
- Models from Train Agent (`shared/models/`)
- Camera frames from App

**Produces:**
- FEN strings
- Move detection
- PGN export

---

## PERFORMANCE TARGETS

**End-to-end pipeline:**
- Input: 30fps camera
- Processing: 5fps (every 6th frame)
- Latency: < 200ms from capture to FEN
- Accuracy: > 95% board detection, > 90% piece classification

---

## EDGE CASES

**Handle:**
- Partial board in frame
- Obstructed view
- Moving pieces (motion blur)
- Multiple boards
- Hand over board
- Changing lighting

**Strategy:**
- Quality scoring per detection
- Reject low-confidence frames
- Temporal smoothing (vote across frames)
- User override (manual position entry)

---

## CHECKPOINTS

- Board detection standalone working
- Piece classification working
- Perspective transform working
- Full pipeline integration
- Flutter bridge integration
- End-to-end test with camera
- Performance profiling
- Status: complete

**On completion:**
- Export module to shared/
- Document API
- Hand off to App Agent
- Update status
