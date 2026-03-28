# Chess Board Image Generation Framework

## Overview

Generates synthetic chess board images for AI training using Blender.

## Features

- 3D rendered chess boards with realistic lighting
- Variable camera angles (top-down to shallow angles)
- Configurable piece styles (classic, modern, abstract)
- Board materials (wood, marble, plastic)
- Randomized lighting and shadows
- Automatic FEN notation labeling
- Multiple resolutions for training

## Directory Structure

```
/workspace/
├── src/
│   ├── board_generator.py      # Main board rendering
│   ├── camera_controller.py    # Camera positioning
│   ├── lighting.py             # Light setup
│   ├── materials.py              # Texture/material management
│   └── fen_exporter.py          # Label generation
├── scripts/
│   ├── batch_generate.py       # Batch dataset generation
│   └── render_single.py         # Single image render
├── config/
│   ├── styles.yaml             # Piece/board style configs
│   └── camera_angles.yaml      # Camera position presets
├── dataset/
│   ├── images/                  # Generated images
│   └── labels/                  # FEN annotations
└── output/                      # Final processed dataset
```

## Usage

```bash
# Generate single board image
docker run --rm -v $(pwd)/dataset:/workspace/dataset chess-vision/dataset-gen render_single.py

# Batch generation
docker run --rm -v $(pwd)/dataset:/workspace/dataset chess-vision/dataset-gen batch_generate.py --count 1000

# With custom config
docker run --rm -v $(pwd)/dataset:/workspace/dataset -v $(pwd)/config:/workspace/config chess-vision/dataset-gen batch_generate.py --config custom.yaml
```

## Camera Angles

- **Top-down (90°):** Standard overhead view, full board visibility
- **Medium (45-60°):** Tournament-style angle
- **Low (20-30°):** Dramatic perspective
- **Shallow (10-20°):** Challenging low angle (for model robustness)

## Piece Styles

- Classic Staunton
- Modern minimalist
- Abstract geometric
- Hand-drawn/artistic

## Labels

Each image includes:
- FEN string (position notation)
- Camera angle metadata
- Lighting conditions
- Board material type
- Piece style used
