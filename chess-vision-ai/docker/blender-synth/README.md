# ChessVision Blender Synthetic Data Generator

Containerized version of the alpha prototype from `/home/jan/Desktop/chess/blender/`

## Quick Start

```bash
# Build the container
docker-compose build blender-synth

# Generate 100 synthetic training images
docker-compose run blender-synth batch 100

# Or run interactively
docker-compose run --rm blender-synth bash
```

## Configuration

Environment variables:
- `RENDER_COUNT` - Number of images to generate
- `RESOLUTION` - Output resolution (default: 712)
- `ELEVATION_MIN/MAX` - Camera elevation angle range (5-15°)
- `AZIMUTH_MIN/MAX` - Camera azimuth range (±60°)
- `CAMERA_RADIUS` - Distance from board (18 units)

## Output Format

Generates per render:
- `{uuid}.png` - Rendered image with random camera angle
- `{uuid}_segmentation.png` - Color-coded segmentation mask
- `{uuid}.json` - Metadata with FEN, piece positions (x,y), board corners

## Architecture

- **Blender 4.0** - 3D rendering with EEVEE engine
- **7 chess model sets** - From BlenderKit assets
- **Procedural camera positioning** - Phone-at-table perspective (5-15° elevation)
- **Ground truth generation** - Board corners + 32 piece positions per image

## Dev Machine Connection

```bash
export DOCKER_HOST=tcp://127.0.0.1:2375
docker -H $DOCKER_HOST compose up -d
```
