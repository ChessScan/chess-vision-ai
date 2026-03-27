# Chess Vision Assets

Complete asset library for synthetic chess training data generation.

## Contents

### ♟️ Piece Sets (4 Styles)

| Set | Style | Description | King Height |
|-----|-------|-------------|-------------|
| `set_01_basic` | Simple geometric | Baseline procedural | ~9.8cm |
| `set_02_tournament` | Plastic tournament | Wider bases, defined steps | ~8.3cm |
| `set_03_classic` | Ornate wood | Tall, layered details | ~12.3cm |
| `set_04_modern` | Minimalist | Clean, smooth surfaces | ~8.5cm |

Each set contains:
- 6 white pieces: king, queen, rook, bishop, knight, pawn
- 6 black pieces: king, queen, rook, bishop, knight, pawn
- **Total: 48 OBJ files**

All pieces are **consistently scaled** to tournament proportions (1 unit = 2.5cm).

### 📋 Boards (4 Styles)

| Board | Style | Light Square | Dark Square |
|-------|-------|--------------|-------------|
| `walnut_4k` | Classic dark wood | #F0DAB5 | #8B5A2B |
| `maple_4k` | Tournament green | Cream | #769656 |
| `mahogany_4k` | Rich red-brown | Light | Deep red |
| `plastic_4k` | Standard tournament | Off-white | #4A7C59 |

**Dimensions:** 56cm × 56cm board, 5.7cm squares, 2.5cm thickness

### 🌅 HDRI Environments

| Category | File | Size |
|----------|------|------|
| Office | `office/kloetzle_blei_4k.hdr` | 21.3 MB |
| Studio | `studio/studio_small_09_4k.exr` | 17.7 MB |
| Home | `home/apartment_4k.exr` | 17.8 MB |
| Outdoor | `outdoor/indoor_pool_4k.exr` | 16.6 MB |

### 🛠️ Generation Scripts

- `generate_all_piece_sets.py` - Create 4 piece set variations
- `generate_all_boards.py` - Create 4 board variations with MTL files
- `validate_all_assets.py` - Check all assets for completeness
- `check_assets.sh` - Quick inventory script
- `download_remaining_assets.sh` - Download additional textures

## Scale Reference

All assets use consistent tournament-standard scaling:

- **1 unit in OBJ** = 2.5cm (for pieces, applied by generator)
- **Board dimensions** = 56cm × 56cm (imported as meters)
- **Square size** = 5.7cm
- **Piece heights** = Proportional to Staunton standard

## Usage

```python
# In Blender or other tool:
import bpy

# Import piece
bpy.ops.import_scene.obj(filepath="pieces/set_01_basic/white/king.obj")

# Import board
bpy.ops.import_scene.obj(filepath="boards/walnut_4k/board.obj")

# Set up HDRI environment
bpy.context.scene.world.use_nodes = True
# Load HDRI from hdri/office/kloetzle_blei_4k.hdr
```

## License

See `LICENSES.md` for full attribution.

All downloaded assets ([Polyhaven](https://polyhaven.com)) are **CC0 (Public Domain)**.

Generated procedural assets are MIT licensed.

## Total Size

~285MB (includes all piece sets, boards, textures, and HDRIs)
