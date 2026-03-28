# Chess Vision - Blender Side-View Rendering

## Overview

This is a **complete Blender-based rendering pipeline** for generating photorealistic chess training data from a **side-view phone perspective**.

## What Gets Generated

**Camera Perspective:**
- Angle: 30-60° from horizontal (phone propped up on table)
- Distance: 25-45cm from board center
- Rotation: 0-360° around board (any viewing angle)
- Focal length: 26mm (iPhone standard)
- Resolution: 640×640 pixels

**Scene:**
- Tournament chess board: 56cm × 56cm
- Standard pieces (4 style variations available)
- HDRI environment lighting (studio/office/home)
- Cycles ray-tracing for photorealistic shadows and materials

**Output:**
- PNG images (640×640)
- Ground truth bounding boxes (COCO format)
- Camera parameters and position metadata

## Requirements

**Option 1: Run with Docker (Recommended)**
```bash
cd data_generation
./render_with_docker.sh 5
```

**Option 2: Run with local Blender**
```bash
# Must have Blender 3.0+ installed
blender --background --python blender_side_view_render.py -- \
  --count 10 \
  --output ./renders/ \
  --assets ./assets/
```

## Assets Available

**Piece Sets (4 styles):**
- `set_01_basic` - Simple geometric
- `set_02_tournament` - Plastic tournament style
- `set_03_classic` - Ornate wood
- `set_04_modern` - Minimalist

**Board Styles (4 types):**
- `walnut_4k` - Classic dark wood
- `maple_4k` - Tournament green
- `mahogany_4k` - Rich red-brown
- `plastic_4k` - Standard tournament

**HDRI Environments:**
- Office, Studio, Home, Outdoor (Polyhaven CC0)

## Output Structure

```
output/
├── renders/
│   ├── chess_render_0000.png
│   ├── chess_render_0001.png
│   └── ...
└── annotations.json
```

**annotations.json** contains:
- Image paths
- Position FEN strings
- Camera parameters
- Bounding boxes for each piece
- COCO-compatible format

## Sample Usage

```python
from chess_data_gen import Generator, Config

# Load config
config = Config.from_yaml("config.yaml")
config.camera.angle_range = (35, 55)  # Phone angle
config.camera.distance_range = (30, 40)  # Phone distance

# Generate
gen = Generator(config, backend="blender")
dataset = gen.generate(count=1000)
dataset.export("./output/", format="coco")
```

## Implementation Details

**File:** `blender_side_view_render.py`

Key components:
1. **ChessSceneBuilder** - Scene construction, imports OBJ assets
2. **Camera Setup** - Phone perspective with random variations
3. **Lighting** - HDRI environment + sun lamp
4. **Ground Truth** - Calculates 2D bounding boxes from 3D projection
5. **Render** - Cycles engine with denoising

**Random Variations:**
- Camera angle (phone tilt)
- Position around board (rotation)
- Distance (phone height)
- HDRI environment
- Lighting intensity
- Board/piece styles

## Status

✅ Complete pipeline implemented
✅ All assets committed (4 piece sets, 4 boards, 4 HDRIs)
✅ Blender script ready
⏳ Waiting for: Docker environment or Blender installation to run renders

## Next Steps

1. Run `render_with_docker.sh` to generate sample images
2. Review output quality
3. Adjust camera/lighting parameters if needed
4. Scale up to full 130K image generation
