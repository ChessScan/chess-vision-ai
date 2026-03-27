# Data Generation API Design Plan
**Project:** Chess Vision AI Training Data Generator  
**Status:** Planning Phase  
**Last Updated:** 2026-03-27  
**Target:** Simple JSON/YAML-based API → 130,000+ training images

---

## 1. Design Principles

### Simplicity First
```python
# The API should be this simple:
from chess_data_gen import Generator

gen = Generator.from_config("config.yaml")
dataset = gen.generate(count=1000)
dataset.export("./output/", format="coco")
```

### Separation of Concerns
- **Configuration** → What to generate
- **Generation** → How to generate (Blender backend)
- **Export** → Where and in what format

---

## 2. API Layers (3-Tier Architecture)

### Layer 1: Declarative Config (User-Facing)
YAML/JSON files defining entire generation runs.

```yaml
# dataset_config.yaml
generation:
  total_images: 130000
  distribution:
    train: 0.8      # 104,000
    val: 0.1        # 13,000
    test: 0.1       # 13,000

board_positions:
  source: "curated"           # curated | random | pgn_import
  count: 130
  categories:
    opening: 20
    middlegame: 40
    endgame: 30
    tactical: 25
    random_legal: 15
  constraints:
    min_pieces: 3
    max_pieces: 32
    enforce_kings: true

camera:
  angle_range: [30, 60]           # degrees from horizontal
  rotation_range: [0, 360]        # full circle
  distance_range: [25, 45]        # cm from board center
  focal_length: 26                # mm (iPhone standard)
  lens_distortion: 0.02           # barrel/pincushion
  depth_of_field:
    enabled: true
    f_stop: [2.8, 5.6]            # aperture range

lighting:
  environments:
    - name: "office_morning"
      hdri: "assets/hdri/office_01.hdr"
      intensity: [0.8, 1.0]
    - name: "tournament_hall"
      hdri: "assets/hdri/venue_02.hdr"
      intensity: [1.0, 1.3]
    - name: "home_warm"
      hdri: "assets/hdri/home_03.hdr"
      intensity: [0.6, 0.9]
  color_temperature_range: [4500, 6500]  # Kelvin
  shadow_softness: [0.3, 0.8]

materials:
  board_variants:
    - wood_walnut         # dark/light
    - wood_maple          # light contrast
    - tournament_plastic  # green/buff
  piece_variants:
    - tournament_plastic  # standard
    - weighted_wood       # classic
    - 3d_printed_matt     # casual
  wear_level: [0.0, 0.3]   # scratches, patina

augmentation:
  post_render:
    sensor_noise:
      enabled: true
      probability: 0.7
      intensity: [0.01, 0.05]
    jpeg_artifacts:
      enabled: true
      probability: 0.5
      quality: [70, 95]
    motion_blur:
      enabled: true
      probability: 0.1
      kernel: [3, 7]
    color_jitter:
      hue: [-0.15, 0.15]
      saturation: [-0.1, 0.1]
      brightness: [-0.1, 0.1]
    
constraints:
  occlusion:
    min_overlap: 0.0
    max_overlap: 0.3
    ensure_variety: true      # at least 20% with occlusion
  board_rotation:
    allow_180: true           # "white on left" scenarios
    probability: 0.25
  piece_visibility:
    min_partial: 0.6          # at least 60% visible

output:
  resolution: [640, 640]
  format: "coco"              # coco | yolo | tfrecord | voc
  include_metadata: true
  version: "1.0.0"
```

### Layer 2: Programmatic API (Library Usage)
Python class-based API for fine-grained control.

```python
from chess_data_gen import Generator, Config, ExportFormat

# Build configuration programmatically
config = Config()

# Board positions
config.positions.from_file("tactical_puzzles.json", count=100)
config.positions.add_random(count=30, min_pieces=5)

# Camera variations  
config.camera.angle(30, 60).samples(5)
config.camera.rotation(0, 360).samples(8)
config.camera.distance(25, 45).distribution("uniform")

# Multi-lighting scenarios
config.lighting.add_environment(
    name="my_office",
    hdri_path="assets/my_hdri.hdr",
    intensity_range=(0.8, 1.2)
)

# Constraints
config.constraints.occlusion(min=0, max=0.3)
config.constraints.board_rotation(enabled=True, probability=0.25)

# Output
config.output.set_resolution(640, 640)
config.output.set_format(ExportFormat.COCO)

# Generate
generator = Generator(config, backend="blender")
generator.set_worker_count(4)
generator.on_progress(lambda p: print(f"{p.percent}% complete"))

dataset = generator.generate()

# Post-process
dataset.augment(sensor_noise=0.02, jpeg_quality=85)
dataset.split(train=0.8, val=0.1, test=0.1)

# Export
dataset.export("./dataset_v1/")
dataset.export("./dataset_yolo/", format=ExportFormat.YOLO)
```

### Layer 3: CLI Interface (Scripting/DevOps)
Command-line tool for batch operations and CI/CD.

```bash
# Basic usage
chess-gen --config dataset_config.yaml --output ./dataset/

# Generate specific subset
chess-gen \
  --positions tactical:50 \
  --camera-angle 30:60:5 \
  --camera-rotation 0:360:8 \
  --lighting office,tournament \
  --count 1000 \
  --output ./output/

# Resume interrupted generation
chess-gen --config dataset_config.yaml \
  --resume ./checkpoint.json \
  --output ./dataset/

# Validation/inspection
chess-gen validate ./dataset/  # Check annotations

# Distributed (multiple machines)
chess-gen --config config.yaml \
  --shard 3/10 \
  --output ./output/
  # Generates positions 30,001-40,000 of 100,000
```

---

## 3. Core Modules & Responsibilities

### Module: Position Generator (`positions/`)
**Responsibility:** Create diverse, realistic chess positions

```python
class PositionGenerator:
    """Generate chess positions in FEN notation."""
    
    # Strategies
    def from_fen(self, fen: str) -> ChessPosition
    def from_pgn(self, pgn_path: str, move_range: Tuple[int, int]) -> List[ChessPosition]
    def random_legal(self, min_pieces: int, max_pieces: int, count: int) -> List[ChessPosition]
    def opening_book(self, eco_codes: List[str], count: int) -> List[ChessPosition]
    def endgame_tablebase(self, piece_count: int, count: int) -> List[ChessPosition]
    def tactical_puzzles(self, elo_range: Tuple[int, int], themes: List[str]) -> List[ChessPosition]
    
    # Filtering
    def filter_legal(self)
    def filter_stockfish_eval(self, min_eval: int)  # Clear positions
    def filter_novelty(self, min_ply: int)  # Not common openings
    
    # Output
    def to_collection(self) -> PositionCollection

@dataclass
class ChessPosition:
    fen: str
    category: str  # "middlegame", "endgame", etc.
    piece_count: int
    pawn_structure: str
    eval_score: Optional[float]  # From Stockfish
    tags: List[str]  # "tactical", "blocked", "open", etc.
```

**Position Categories to Support:**
- **Opening** (20 positions): Ruy Lopez, Queen's Gambit, Sicilian entries
- **Middlegame** (40 positions): Open games, closed positions, attacks
- **Endgame** (30 positions): King+pawn, rook endings, minor piece endings
- **Tactical** (25 positions): Pins, forks, skewers, discovered attacks visible
- **Random Legal** (15 positions): Coverage edge cases

### Module: Camera Controller (`camera/`)
**Responsibility:** Map camera parameters → realistic transforms

```python
class CameraController:
    """Control virtual camera in 3D space."""
    
    def __init__(self, focal_length: float = 26.0, sensor_size: str = "APS-C"):
        self.focal_length = focal_length
        self.sensor_size = sensor_size
    
    def set_angle(self, degrees_from_horizontal: float):
        """30-60° typically. 90° = top-down (detected, needs flag)."""
        pass
    
    def set_rotation(self, degrees_around_center: float):
        """0-360° around board center."""
        pass
    
    def set_distance(self, centimeters: float):
        """25-45cm from board center point."""
        pass
    
    def set_lens_distortion(self, k1: float, k2: float = 0):
        """Barrel/pincushion distortion coefficients."""
        pass
    
    def compute_view_frustum(self) -> ViewFrustum:
        """Calculate visible squares for occlusion planning."""
        pass
    
    def is_square_visible(self, square: str) -> bool:
        """Check if square 'e4' is in camera view."""
        pass
    
    def get_ground_truth_projection(self, piece: Piece) -> BoundingBox:
        """Project 3D piece to 2D image coordinates."""
        pass

@dataclass
class CameraPose:
    """A complete camera configuration."""
    vertical_angle: float      # 30-60°
    horizontal_rotation: float # 0-360°
    distance: float            # 25-45cm
    tilt: float = 0            # ±5° board alignment errors
    roll: float = 0            # ±3° accidental rotation

@dataclass  
class BoundingBox:
    """2D image projection of a chess piece."""
    x: float
    y: float  
    width: float
    height: float
    square: str        # Board square, e.g., "e4"
    piece: str         # "white_queen"
    occlusion_ratio: float  # 0.0-1.0 (1.0 = fully visible)
```

**Parameter Ranges:**
| Parameter | Min | Max | Default | Notes |
|-----------|-----|-----|---------|-------|
| Vertical angle | 30° | 60° | 45° | Below 30 = too flat, above 60 = too steep |
| Horizontal rotation | 0° | 360° | 0° | Full circle coverage |
| Distance | 25cm | 45cm | 35cm | Closer = pieces larger, farther = more board visible |
| Focal length | 24mm | 28mm | 26mm | iPhone 26mm equivalent |
| Barrel distortion | -0.05 | 0.05 | 0 | Simulates real lens imperfections |

### Module: Lighting Controller (`lighting/`)
**Responsibility:** Realistic illumination with variations

```python
class LightingController:
    """Manage scene lighting setup."""
    
    def set_hdri_environment(self, path: str, rotation: float = 0, intensity: float = 1.0):
        """Set HDRI for ambient lighting and reflections."""
        pass
    
    def add_key_light(self, direction: Tuple[float, float, float], intensity: float, 
                      color_temp: int = 6500):
        """Primary illumination source."""
        pass
    
    def add_fill_light(self, direction: Tuple[float, float, float], intensity: float):
        """Reduce harsh shadows from key light."""
        pass
    
    def add_rim_light(self, direction: Tuple[float, float, float], intensity: float):
        """Edge definition on pieces."""
        pass
    
    def set_color_temperature(self, kelvin: int):
        """Overall white balance (4500=warm, 6500=daylight, 9000=cool)."""
        pass
    
    def randomize_shadow_softness(self, min_softness: float, max_softness: float):
        """Vary shadow edges (0=sharp, 1=fully diffused)."""
        pass
```

**Lighting Presets:**
- **Morning Office:** Warm (4500K), soft key from window
- **Tournament Hall:** Neutral (5500K), overhead spotlights
- **Evening Home:** Warm (3500K), mixed artificial
- **Studio:** Cool (6500K), even illumination

### Module: Material/Asset Manager (`assets/`)
**Responsibility:** Load and randomize 3D models and textures

```python
class AssetManager:
    """Manage 3D models, textures, materials."""
    
    def __init__(self, asset_root: Path):
        self.assets = self._scan_assets(asset_root)
    
    def load_piece_set(self, variant: str = "tournament") -> PieceSet:
        """Load 12 pieces (6 white, 6 black)."""
        pass
    
    def load_board(self, variant: str = "walnut") -> Board:
        """Load chess board with materials."""
        pass
    
    def load_hdri(self, name: str) -> HDRI:
        """Load environment map."""
        pass
    
    def randomize_material(self, mesh: Mesh, wear_level: float = 0.0):
        """Add surface imperfections, wear."""
        pass
    
    def apply_prototype_substitution(self, 
        piece: Piece, 
        variation: Literal["scale", "material", "color"]
    ):
        """Support for domain randomization (different visual appearance)."""
        pass

@dataclass
class PieceSet:
    """Complete chess set with both colors."""
    white: Dict[PieceType, Piece3D]  # {KING: obj, QUEEN: obj...}
    black: Dict[PieceType, Piece3D]
    base_scale: float = 1.0
    material_variant: str
```

**Asset Structure:**
```
assets/
├── pieces/
│   ├── tournament_01/
│   │   ├── white_king.obj
│   │   ├── white_queen.obj
│   │   ├── ...
│   │   └── black_pawn.obj
│   └── classic_wood/
│       └── ...
├── boards/
│   ├── walnut_4k/
│   │   ├── model.obj
│   │   ├── light_square_albedo.png
│   │   ├── dark_square_albedo.png
│   │   └── normal_map.png
│   └── maple_tournament/
│       └── ...
└── hdri/
    ├── office_morning_4k.hdr
    ├── tournament_hall_4k.hdr
    └── home_evening_4k.hdr
```

### Module: Scene Composer (`scene/`)
**Responsibility:** Build complete Blender scene from position + params

```python
class SceneComposer:
    """Assemble complete 3D scene for rendering."""
    
    def __init__(self, blender_backend: Backend):
        self.backend = blender_backend
    
    def create_scene(self, position: ChessPosition, params: RenderParams) -> Scene:
        """Build scene with all elements."""
        scene = Scene()
        
        # Place board
        scene.add(self.assets.load_board(params.board_variant))
        
        # Place pieces from FEN
        for square, piece in position.pieces:
            mesh = self.assets.load_piece(piece, params.piece_variant)
            scene.add_at(mesh, square, rotation=params.board_rotation)
        
        # Set camera
        scene.set_camera(self.camera.compute_pose(params.camera_params))
        
        # Set lighting
        scene.set_lighting(self.lighting.create_setup(params.lighting_params))
        
        return scene
    
    def compute_ground_truth(self, scene: Scene) -> List[Annotation]:
        """Calculate 2D projections of all pieces."""
        annotations = []
        for piece in scene.pieces:
            bbox = self.camera.project_to_2d(piece)
            if bbox.is_partially_visible(min_ratio=0.6):
                annotations.append(Annotation(
                    bbox=bbox,
                    piece_class=piece.class_name,
                    square=piece.board_square
                ))
        return annotations

@dataclass
class RenderParams:
    """Complete parameter set for one render."""
    position: ChessPosition
    board_variant: str
    piece_variant: str
    board_rotation: float  # 0, 90, 180, 270
    camera_params: CameraPose
    lighting_params: LightingConfig
    wear_level: float
    materials_seed: int
```

### Module: Rendering Backend (`backends/`)
**Responsibility:** Abstract over rendering engines (Blender primary)

```python
class BlenderBackend:
    """Blender 3.6+ rendering via Python API (bpy)."""
    
    def __init__(self, blend_file: Path = None):
        self.blend_path = blend_file or self._create_template_scene()
    
    def render(self, scene: Scene, output_path: Path) -> RenderResult:
        """Render scene to PNG, return path + metadata."""
        # bpy.ops.render.render(write_still=True)
        pass
    
    def get_3d_to_2d_projection(self, object_3d: Object) -> BoundingBox:
        """Calculate ground truth bounding box."""
        # Use bpy_extras.object_utils.world_to_camera_view
        pass
    
    def batch_render(self, scenes: List[Scene], callback: Callable) -> List[RenderResult]:
        """Efficient batch rendering with scene reuse."""
        pass
    
    def set_quality(self, samples: int = 128, denoise: bool = True):
        """Control render quality vs speed tradeoff."""
        pass

# Future backends
class MarmosetBackend:
    """Alternative: Marmoset Toolbag (faster, game-art optimized)."""
    pass

class UnrealBackend:
    """Alternative: Unreal Engine 5 (ray tracing, Nanite)."""
    pass

class ProceduralBackend:
    """Fast fallback: Generate bounding boxes without full render."""
    pass
```

### Module: Post-Processing/Augmentation (`augmentation/`)
**Responsibility:** Apply training-safe augmentations after rendering

```python
class PostProcessor:
    """Post-render image modifications."""
    
    def __init__(self, probability: float = 0.5):
        self.probability = probability
    
    def add_sensor_noise(self, image: Image, intensity: float) -> Image:
        """Gaussian noise simulating camera sensor."""
        pass
    
    def add_jpeg_artifacts(self, image: Image, quality: int) -> Image:
        """Compression artifacts from real saving."""
        pass
    
    def add_motion_blur(self, image: Image, kernel_size: int) -> Image:
        """Slight camera shake."""
        pass
    
    def color_jitter(self, image: Image, 
                     hue: float, saturation: float, brightness: float) -> Image:
        """HSV perturbations."""
        pass
    
    def resize(self, image: Image, size: Tuple[int, int], 
               interpolation: str = "bilinear") -> Image:
        """Resize to target resolution for model training."""
        pass
    
    def center_crop(self, image: Image, target_size: Tuple[int, int]) -> Image:
        """Ensure board in center."""
        pass

class AugmentationPipeline:
    """Chain of augmentations with probability."""
    
    def __init__(self):
        self.steps = []
    
    def add(self, augmenter: Callable, probability: float = 1.0):
        self.steps.append((augmenter, probability))
    
    def apply(self, image: Image) -> Image:
        for aug, prob in self.steps:
            if random.random() < prob:
                image = aug(image)
        return image
```

**Augmentations to Support:**
| Augmentation | Range | Probability | Purpose |
|--------------|-------|-------------|---------|
| Sensor noise | 0.01-0.05 | 0.7 | Real camera noise |
| JPEG compression | 70-95 | 0.5 | Real saving artifacts |
| Motion blur | 3-7px | 0.1 | Hand shake simulation |
| Hue shift | ±15% | 0.3 | Color robustness |
| Saturation | ±10% | 0.3 | Varying material colors |
| Brightness | ±10% | 0.4 | Lighting variations |
| Contrast | ±15% | 0.2 | Shadow emphasis |
| Sharpness | ±30% | 0.2 | Focus variations |

### Module: Annotation Export (`exporters/`)
**Responsibility:** Convert internal format → training formats

```python
class COCOExporter:
    """COCO JSON format (most common for object detection)."""
    
    def export(self, images: List[Image], annotations: List[Annotation], 
               output_path: Path):
        """Save images + annotations.json."""
        pass
    
    def format_annotation(self, ann: Annotation) -> Dict:
        return {
            "id": ann.id,
            "image_id": ann.image_id,
            "category_id": ann.category_id,
            "bbox": [ann.x, ann.y, ann.width, ann.height],
            "area": ann.area,
            "iscrowd": 0,
            "square": ann.board_square
        }

class YOLOExporter:
    """YOLO format (.txt files per image, categories.txt)."""
    
    def export(self, images: List[Image], annotations: List[Annotation], 
               output_path: Path):
        """Save images + labels/ folder with .txt files."""
        pass

class TFRecordExporter:
    """TensorFlow TFRecord format (efficient loading)."""
    pass

class VOCExporter:
    """Pascal VOC XML format (legacy support)."""
    pass
```

**Categories (13 classes):**
1. white_king
2. white_queen
3. white_rook
4. white_bishop
5. white_knight
6. white_pawn
7. black_king
8. black_queen
9. black_rook
10. black_bishop
11. black_knight
12. black_pawn
13. empty_square (optional for segmentation)

---

## 4. Pipeline Orchestration

### Generation Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│  CONFIG (YAML/Python/CLI)                                    │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: POSITION GENERATION                                │
│  ├─ Load curated positions (PGN, FEN database)               │
│  ├─ Generate random legal positions                          │
│  ├─ Filter by constraints (min/max pieces, eval score)       │
│  └─ Create PositionCollection (130 positions)                │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: PARAMETER SAMPLING                                   │
│  ├─ For each position, sample 1000 parameter combinations    │
│  ├─ Camera: angle, rotation, distance                        │
│  ├─ Lighting: HDRI, intensity, color temp                    │
│  ├─ Materials: board variant, piece variant                    │
│  └─ Constraints: check occlusion limits, visibility            │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 3: SCENE BUILDING (Blender)                             │
│  ├─ Load base .blend scene template                          │
│  ├─ Place board with selected material                       │
│  ├─ Place pieces per FEN notation                            │
│  ├─ Set camera pose                                          │
│  └─ Configure lighting setup                                 │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 4: RENDERING                                          │
│  ├─ Calculate ground-truth projections (before render)         │
│  ├─ Execute render (Cycles/EEVEE)                            │
│  ├─ Validate output image                                    │
│  └─ Extract final 2D bounding boxes                          │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 5: POST-PROCESSING                                      │
│  ├─ Apply sensor noise (probabilistic)                       │
│  ├─ Add JPEG compression artifacts                           │
│  ├─ Color jittering (HSV shifts)                             │
│  ├─ Resize to model input resolution (640×640)               │
│  └─ Adjust bounding boxes to match final resolution          │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 6: DATASET ORGANIZATION                                 │
│  ├─ Split into train/val/test                                │
│  ├─ Export to selected format (COCO/YOLO/TFRecord)           │
│  ├─ Generate metadata (statistics, class distribution)       │
│  └─ Save checkpoint for reproducibility                      │
└─────────────────────────────────────────────────────────────┘
```

### Parallelization Strategy

```python
class ParallelGenerator:
    """Distribute rendering across CPU cores/machines."""
    
    def __init__(self, config: Config, workers: int = 4):
        self.config = config
        self.workers = workers
    
    def generate_parallel(self, total: int) -> Dataset:
        """Split work across workers."""
        chunk_size = total // self.workers
        
        with ProcessPoolExecutor(max_workers=self.workers) as executor:
            futures = [
                executor.submit(self._generate_chunk, i, chunk_size)
                for i in range(self.workers)
            ]
            results = [f.result() for f in futures]
        
        return Dataset.merge(results)
    
    def generate_distributed(self, shard: Tuple[int, int]) -> Dataset:
        """Generate subset for distributed computing."""
        shard_id, total_shards = shard
        positions = self._get_positions_for_shard(shard_id, total_shards)
        return self._generate_positions(positions)
```

---

## 5. Configuration Reference

### Complete Parameter Matrix

| Category | Parameter | Type | Range | Default | Impact |
|----------|-----------|------|-------|---------|--------|
| **Camera** | angle | float | 30-60° | 45° | Depth perception |
| | rotation | float | 0-360° | 0° | Viewpoint diversity |
| | distance | float | 25-45cm | 35cm | Piece size in frame |
| | focal_length | float | 24-28mm | 26mm | Perspective |
| | lens_distortion | float | -0.05-0.05 | 0.0 | Realism |
| | depth_of_field | bool | true/false | true | Background blur |
| **Lighting** | hdri | enum | file list | office | Environment |
| | color_temp | int | 4500-6500K | 5500 | White balance |
| | key_intensity | float | 0.8-1.2 | 1.0 | Exposure |
| | shadow_softness | float | 0.3-0.8 | 0.5 | Shadow edges |
| **Materials** | board_type | enum | 3 variants | walnut | Appearance |
| | piece_type | enum | 3 variants | tournament | Appearance |
| | wear_level | float | 0.0-0.3 | 0.1 | Imperfections |
| **Position** | piece_count | int | 3-32 | 24 | Complexity |
| | board_rotation | float | 0/180° | 0° | Square color |
| **Augmentation** | jpeg_quality | int | 70-95 | 85 | Artifacts |
| | sensor_noise | float | 0.01-0.05 | 0.03 | Grain |
| | hue_shift | float | -0.15-+0.15 | 0.05 | Color |

### Constraint Validation Rules

```python
CONSTRAINT_RULES = {
    "occlusion": {
        "max_overlap": 0.30,  # Bounding box IoU
        "ensure_variety": 0.20,  # At least 20% have occlusion
    },
    "visibility": {
        "min_partial": 0.60,  # At least 60% visible
        "min_total_pieces": 0.80,  # At least 80% of pieces visible
    },
    "distortion": {
        "max_barrel": 0.05,  # k1 coefficient
        "max_pincushion": -0.05,
    },
    "lighting": {
        "min_brightness": 30,  # Pixel value 0-255
        "max_brightness": 240,
        "max_contrast_ratio": 15.0,  # Avoid extremes
    }
}
```

---

## 6. Implementation Roadmap

### Milestone 1: Core Infrastructure (Week 1-2)
**Goal:** Generate first 100 images with full pipeline

- [ ] Set up project structure (`data_generation/`)
- [ ] Implement Config classes (YAML/JSON loading)
- [ ] Create PositionGenerator with FEN support
- [ ] Build BlenderBackend scaffolding
- [ ] Create SceneComposer basics
- [ ] Export to simple JSON format

**Success Criteria:**
- ✅ Can generate a single image from CLI
- ✅ Annotations match image content
- ✅ Can render 100 images in < 10 minutes (CPU)

---

### Milestone 2: Parameter Maturation (Week 3-4)
**Goal:** Full parameter space coverage

- [ ] Complete CameraController with all parameters
- [ ] Implement all Lighting presets
- [ ] Add Material/AssetManager with variants
- [ ] Build comprehensive parameter sampling
- [ ] Add constraint validation pipeline

**Success Criteria:**
- ✅ All config parameters affect output
- ✅ Occlusion checks pass
- ✅ 130 positions × 100 renders = 13,000 images

---

### Milestone 3: Quality & Export (Week 5-6)
**Goal:** Production-ready dataset generation

- [ ] Implement post-processing augmentations
- [ ] Build COCO/YOLO/TFRecord exporters
- [ ] Add quality control pipeline
- [ ] Create train/val/test splitting
- [ ] Add checkpoint/resume functionality

**Success Criteria:**
- ✅ 130,000 images generated successfully
- ✅ Export to multiple formats works
- ✅ < 5% rejection rate on validation
- ✅ Can resume from checkpoint

---

### Milestone 4: Optimization (Week 7-8)
**Goal:** Scalable generation

- [ ] Parallel rendering across CPU cores
- [ ] Distributed generation (multiple machines)
- [ ] Cloud backend support (AWS/ GCP)
- [ ] Progress monitoring & telemetry
- [ ] Optimization for render speed

**Success Criteria:**
- ✅ 4× speedup with parallelization
- ✅ Remote generation works
- ✅ Progress callbacks functional
- ✅ 130,000 images in < 3 days

---

## 7. File Structure Plan

```
data_generation/
├── README.md                          # Quick start guide
├── API_DESIGN_PLAN.md                 # This file
├── SPECIFICATION.md                   # Detailed API specs
├── IMPLEMENTATION.md                  # How To Build
├── CONFIG_REFERENCE.md                # All parameters documented
├── examples/
│   ├── basic_generation.yaml          # Simple config example
│   ├── full_production.yaml           # 130k image config
│   ├── tactical_focus.yaml            # Emphasis on tactics
│   └── python_script_example.py       # Programmatic usage
├── src/
│   ├── chess_data_gen/                # Main package
│   │   ├── __init__.py
│   │   ├── config.py                  # Config classes
│   │   ├── generator.py               # Main Generator class
│   │   ├── positions/
│   │   │   ├── __init__.py
│   │   │   ├── generator.py           # Position generation
│   │   │   ├── curated.py             # Known positions
│   │   │   └── random.py              # Legal position generator
│   │   ├── camera/
│   │   │   ├── __init__.py
│   │   │   ├── controller.py          # Camera manipulations
│   │   │   └── projection.py          # 3D to 2D math
│   │   ├── lighting/
│   │   │   ├── __init__.py
│   │   │   └── controller.py          # Light setup
│   │   ├── assets/
│   │   │   ├── __init__.py
│   │   │   ├── manager.py             # Asset loading
│   │   │   └── materials.py           # Material randomization
│   │   ├── scene/
│   │   │   ├── __init__.py
│   │   │   ├── composer.py            # Scene assembly
│   │   │   └── validation.py          # Pre-render checks
│   │   ├── backends/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                # Abstract backend
│   │   │   └── blender.py             # Blender implementation
│   │   ├── augmentation/
│   │   │   ├── __init__.py
│   │   │   ├── post_processor.py
│   │   │   └── pipeline.py
│   │   ├── exporters/
│   │   │   ├── __init__.py
│   │   │   ├── coco.py
│   │   │   ├── yolo.py
│   │   │   └── tfrecord.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── parallel.py            # Multiprocessing
│   │       └── checkpoint.py          # Resume capability
│   └── cli/
│       ├── __init__.py
│       └── main.py                    # Command-line interface
├── tests/
│   ├── test_config.py
│   ├── test_positions.py
│   ├── test_camera.py
│   ├── test_scene.py
│   └── integration_tests.py
├── assets/                            # 3D models (git-lfs)
│   ├── pieces/
│   ├── boards/
│   └── hdri/
├── docs/
│   ├── BACKEND_BLENDER.md             # Blender-specific docs
│   ├── EXPORT_FORMATS.md              # Format specifications
│   ├── POSITIONS_DATABASE.md          # Curated positions source
│   └── TROUBLESHOOTING.md
└── scripts/
    ├── install_blender.py             # Setup helper
    ├── validate_installation.py       # Check requirements
    └── benchmark.py                   # Performance testing
```

---

## 8. Known Challenges & Solutions

### Challenge: Blender Python API Complexity
**Problem:** `bpy` API is complex, hard to abstract cleanly  
**Solution:** Create thin wrapper that maps our semantic parameters to Blender calls

```python
class BlenderScene:
    """Hide bpy complexity."""
    def place_piece(self, piece: Piece3D, square: str):
        # Translate square "e4" → Blender coordinates
        x, y = self._square_to_coords(square)
        bpy.ops.import_scene.obj(filepath=piece.path)
        obj = bpy.context.selected_objects[0]
        obj.location = (x, y, BOARD_Z + PIECE_BASE_HEIGHT)
```

### Challenge: Render Speed on CPU
**Problem:** Cycles on CPU is slow (~5s per image)  
**Solution:** 
- Reduce samples (64 for speed, 128 for quality)
- Use tile rendering
- Parallelize by running multiple Blender instances
- Cloud bursting for batch generation

### Challenge: Bounding Box Accuracy
**Problem:** Projected boxes may not match visual boundaries  
**Solution:**
- Use mesh vertices, not bounding spheres
- Add small margin (2-3 pixels) for imprecision
- Visual validation tool to spot-check

### Challenge: Memory Management
**Problem:** Loading 130 positions × 12 pieces in parallel = memory pressure  
**Solution:**
- Streaming generation: Load position → Render → Unload
- Shared piece meshes (instancing)
- Cleanup between batches

### Challenge: Reproducibility
**Problem:** Need identical dataset given same config  
**Solution:**
- Seed all random generators
- Save full random state with checkpoint
- Version all assets with hashes
- Document Blender version

---

## 9. Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Generation speed | <5s per image (CPU) | Timer around render() |
| Annotation accuracy | >99% IoU | Visual spot check + automated validation |
| Parameter coverage | 100% of config matrix | Coverage report |
| Export correctness | 100% loadable by training frameworks | test_coco_load(), test_yolo_load() |
| Resume capability | Resume from any checkpoint | Kill and resume test |
| Memory usage | <4GB peak | Monitor with memory_profiler |
| Disk space | <100GB for 130k images | Measure output size |

---

## 10. Next Steps

1. **Review this plan** - Mark sections as approved/revision needed
2. **Create SPECIFICATION.md** - Formal API contracts
3. **Set up project skeleton** - Folder structure, __init__.py files
4. **Implement Config class** - YAML parsing, validation
5. **Build first working render** - Single image end-to-end
6. **Iterate on parameter space** - Test variations
7. **Scale to batch generation** - 100 → 1000 → 130,000

---

**Questions to Resolve:**
1. Should we support multiple backends (Blender + Unreal) or Blender-only?
2. Do we include "empty" squares as class 13 for segmentation?
3. Should we include top-down (90°) renders or exclude them?
4. What Blender version to target? (3.6+ has best Python API)
5. Do we need real-time preview, or batch-only generation?

Ready to move to implementation planning.