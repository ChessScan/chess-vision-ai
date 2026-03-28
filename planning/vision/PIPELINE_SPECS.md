# Pipeline Specifications

Technical specifications for CV pipeline components, interfaces, and data formats.

## Overview

All components must conform to these specifications to ensure interoperability across the system.

## Component Interfaces

### Board Detector Interface

```python
class BoardDetector(Protocol):
    """Interface for board detection implementations"""
    
    def detect(self, frame: np.ndarray) -> BoardDetectionResult:
        """
        Detect chess board in video frame.
        
        Args:
            frame: BGR image (H×W×3), uint8, any resolution
            
        Returns:
            BoardDetectionResult with corners, confidence, status
        """
        ...

@dataclass
class BoardDetectionResult:
    corners: Optional[np.ndarray]  # [4, 2] float32, ordered [TL, TR, BR, BL]
    confidence: float              # 0.0-1.0
    status: str                   # "OK", "NO_BOARD", "LOW_CONFIDENCE", "INVALID_HOMOGRAPHY"
    processing_time_ms: float
```

### Rectifier Interface

```python
class Rectifier(Protocol):
    """Perspective rectification from skewed to orthogonal view"""
    
    def rectify(self, frame: np.ndarray, corners: np.ndarray) -> RectificationResult:
        """
        Rectify board to 512×512 orthogonal view.
        
        Args:
            frame: Original video frame
            corners: [4, 2] corners from BoardDetector
            
        Returns:
            RectificationResult
        """
        ...

@dataclass  
class RectificationResult:
    image: np.ndarray           # 512×512 BGR uint8
    homography: np.ndarray      # 3×3 homography matrix
    valid: bool               # Whether homography is valid
```

### Grid Extractor Interface

```python
class GridExtractor(Protocol):
    """Extract 64 squares from rectified board"""
    
    def extract_squares(self, rectified_board: np.ndarray) -> GridExtractionResult:
        """
        Extract 64 squares from rectified board.
        
        Args:
            rectified_board: 512×512 BGR uint8
            
        Returns:
            GridExtractionResult
        """
        ...

@dataclass
class GridExtractionResult:
    squares: np.ndarray         # [64, 100, 100, 3] BGR uint8
    squares_metadata: List[SquareMetadata]  # One per square
    board_layout: np.ndarray    # [8, 8] indices into squares array

@dataclass
class SquareMetadata:
    rank: int                   # 0-7 (0=a8, 7=h1)
    file: int                   # 0-7 (0=a, 7=h)
    algebraic: str              # "e4", "a1", etc.
    crop_coords: Tuple[int, int, int, int]  # (y1, x1, y2, x2) in rectified image
```

### Piece Classifier Interface

```python
class PieceClassifier(Protocol):
    """Classify chess pieces from square images"""
    
    def classify_squares(self, squares: np.ndarray) -> ClassificationResult:
        """
        Classify 64 squares.
        
        Args:
            squares: [64, 100, 100, 3] BGR uint8
            
        Returns:
            ClassificationResult
        """
        ...

@dataclass
class ClassificationResult:
    predictions: np.ndarray         # [64, 13] float32 probabilities
    predicted_classes: np.ndarray  # [64] int (0-12)
    confidences: np.ndarray        # [64] float (confidence for each prediction)
    class_names: List[str]         # 13 class names
```

### State Assembler Interface

```python
class StateAssembler(Protocol):
    """Convert classifications to board state (FEN)"""
    
    def assemble(self, classification: ClassificationResult) -> BoardState:
        """
        Convert predictions to board state.
        
        Args:
            classification: From PieceClassifier
            
        Returns:
            BoardState with FEN and per-square info
        """
        ...

@dataclass
class BoardState:
    fen: str                    # Standard FEN notation
    squares: List[SquareState] # 64 elements, a8 to h1
    confidence: float          # Overall board confidence
    timestamp: float         # Unix timestamp

@dataclass
class SquareState:
    algebraic: str             # "e4"
    piece: Optional[str]       # "K", "q", "P", etc. or None
    confidence: float          # Classification confidence
    raw_class_id: int          # Raw model output
```

### Temporal Tracker Interface

```python
class TemporalTracker(Protocol):
    """Track board state across frames, detect moves"""
    
    def update(self, board_state: BoardState) -> TrackingResult:
        """
        Update tracker with new board state.
        
        Args:
            board_state: Current frame's board state
            
        Returns:
            TrackingResult with move detection
        """
        ...
    
    def reset(self):
        """Reset tracker (new game)"""
        ...

@dataclass
class TrackingResult:
    state: str                 # "STATIC", "CHANGING", "UNSTABLE"
    move_detected: bool
    move: Optional[str]        # SAN notation, e.g., "e2-e4"
    from_square: Optional[str]
    to_square: Optional[str]
    captured_piece: Optional[str]
    stable_state: BoardState   # Last stable board state
```

## Data Formats

### Frame Format

```yaml
Frame:
  dimensions: [height, width]  # Any resolution
  channels: 3                  # BGR color space
  dtype: uint8               # 0-255 range
  source: camera             # "camera" | "file" | "stream"
  timestamp: float           # Unix timestamp (optional)
  frame_number: int          # Sequential number (optional)
```

### FEN String

Standard Forsyth-Edwards Notation.

```
Example: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1

Position (first field):
  Lowercase = black pieces
  Uppercase = white pieces
  Numbers = empty squares
  / = rank separator
  
Full format: [position] [turn] [castling] [en_passant] [halfmove] [fullmove]

Simplified (we use): [position] only
```

### SAN Notation

Standard Algebraic Notation for moves.

```
e2-e4      # Pawn move (simplified, our format)
e4         # Pawn to e4
Nf3        # Knight to f3
Qxe7       # Queen captures on e7
O-O        # Kingside castle
Raxb1      # Rook from a-file captures on b1

Our simplified format: [from]-[to]
Examples: "e2-e4", "g1-f3", "e1-g1" (castling)
```

### Chess Piece Encoding

```python
PIECE_ENCODING = {
    # White pieces (uppercase in FEN)
    'K': 'w_king',
    'Q': 'w_queen', 
    'R': 'w_rook',
    'B': 'w_bishop',
    'N': 'w_knight',
    'P': 'w_pawn',
    
    # Black pieces (lowercase in FEN)
    'k': 'b_king',
    'q': 'b_queen',
    'r': 'b_rook', 
    'b': 'b_bishop',
    'n': 'b_knight',
    'p': 'b_pawn',
}

CLASS_ID_TO_FEN = {
    0: None,    # Empty
    1: 'K',     # White King
    2: 'Q',     # White Queen
    ...
}
```

### PGN Export Format

```
[Event "ChessScan Generated Game"]
[Date "2026.03.28"]
[White "Player 1"]
[Black "Player 2"]
[Result "*"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 *
```

## Error Handling

### Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| `NO_BOARD` | No chess board detected | Skip frame, retry |
| `LOW_CONFIDENCE` | Board detected but uncertain | Skip frame, warn user |
| `INVALID_HOMOGRAPHY` | Board corners don't form valid transform | Skip frame, log |
| `MOTION_BLUR` | Frame too blurry for classification | Skip frame |
| `AMBIGUOUS_MOVE` | Move detected but illegal | Flag for manual review |
| `TIMEOUT` | Processing took too long | Skip frame, degrade gracefully |

### Graceful Degradation

```python
class Pipeline:
    def process_frame(self, frame):
        # Try full pipeline
        result = self.try_detect(frame)
        
        if result.status == "OK":
            return result
        
        # Degradation: Use last known state
        if self.last_stable_state and self.degradation_count < 5:
            self.degradation_count += 1
            return self.last_stable_state
        
        # Final: Return empty/error state
        return PipelineResult(error=result.status)
```

## Performance Requirements

### Timing Budgets

| Component | Max Time | Target Time |
|-----------|----------|-------------|
| Board Detection | 100ms | 50ms |
| Rectification | 10ms | 5ms |
| Grid Extraction | 5ms | 2ms |
| Piece Classification (64×) | 320ms | 200ms |
| State Assembly | 5ms | 2ms |
| Temporal Tracking | 5ms | 2ms |
| **TOTAL** | **450ms** | **260ms** |

Note: Classification is parallelizable. With batch inference on GPU: ~30ms.

### Memory Budgets

| Component | Max RAM | Notes |
|-----------|---------|-------|
| Board Detector | 50MB | TFLite model |
| Piece Classifier | 30MB | TFLite model |
| Frame Buffer | 10MB | Double buffering |
| Working Memory | 50MB | Temporary allocations |
| **TOTAL** | **140MB** | Below 200MB mobile target |

### Throughput

- **Minimum:** 2 FPS (board updates every 500ms)
- **Target:** 5 FPS (smooth move detection)
- **Optimal:** 10 FPS (with batch classification)

## Configuration

### Pipeline Configuration File

```yaml
# config/vision.yaml

pipeline:
  # Frame processing
  input_resolution: [640, 480]
  target_fps: 5
  
  # Board detection
  board_detector:
    model_path: "models/board_detector.tflite"
    confidence_threshold: 0.5
    temporal_smoothing: 0.7  # Alpha for EMA
    
  # Rectification
  rectifier:
    output_size: [512, 512]
    interpolation: "LINEAR"
    
  # Grid extraction
  grid_extractor:
    output_square_size: 100
    padding_factor: 0.32  # 32px padding on 64px square
    
  # Piece classification
  classifier:
    model_path: "models/piece_classifier.tflite"
    confidence_threshold: 0.6
    batch_size: 32
    
  # Temporal tracking
  tracker:
    stability_frames: 3
    max_degradation_frames: 5
    
  # Error handling
  error_handling:
    skip_on_low_confidence: true
    max_retry_attempts: 3
    use_last_known_state: true
```

## Testing Interface

### Unit Tests

Each component must have:
- Input/output contract tests
- Error condition tests
- Performance benchmarks

### Integration Tests

Full pipeline tests:
- Synthetic video sequences
- Real video clips (ground truth annotated)
- Edge cases ( occlusions, lighting changes)

### Benchmark Suite

```python
def benchmark_pipeline(model, test_videos):
    results = {}
    
    for video in test_videos:
        metrics = {
            'board_detection_rate': measure_detection_rate(),
            'piece_accuracy': measure_piece_accuracy(),
            'move_detection_accuracy': measure_move_accuracy(),
            'latency_95th': measure_latency_percentile(95),
            'memory_peak': measure_memory_usage(),
        }
        results[video.name] = metrics
    
    return results
```

## Versioning

### Model Versions

```yaml
models:
  board_detector:
    version: "1.0.0"
    trained_on: "2026-03-15"
    accuracy: 0.94
    
  piece_classifier:
    version: "1.0.0"
    trained_on: "2026-03-20"
    accuracy: 0.985
```

### Protocol Versions

- Current: `vision_pipeline_v1`
- Backward compatible: minor versions
- Breaking changes: major version bump

## References

- FEN Specification: https://www.chessprogramming.org/Forsyth-Edwards_Notation
- SAN Specification: https://www.chessprogramming.org/Algebraic_Chess_Notation
- PGN Specification: http://www.saremba.de/chessgml/standards/pgn/pgn-complete.htm
- Protocol Buffers: For serialization (optional future)