# Chess Vision Data Generation

Synthetic training data generator for chess piece recognition using Blender.

## Quick Start

```bash
# Install
pip install -e .

# Generate dataset from config
chess-gen --config examples/basic_generation.yaml --output ./dataset/

# Or use Python API
from chess_data_gen import Generator, Config

config = Config.from_yaml("config.yaml")
gen = Generator(config)
dataset = gen.generate(count=1000)
dataset.export("./output/", format="coco")
```

## Key Files

| File | Purpose |
|------|---------|
| `API_DESIGN_PLAN.md` | Master design document - start here |
| `SPECIFICATION.md` | Detailed API contracts (TODO) |
| `examples/` | Working configuration examples |
| `src/` | Source code (TODO) |

## Status

- [x] Planning complete (API_DESIGN_PLAN.md)
- [ ] Config system implementation
- [ ] Blender backend
- [ ] Position generator
- [ ] Rendering pipeline
- [ ] Export formats

## Target

130,000 training images from 130 curated positions × 100 variations each.

See `API_DESIGN_PLAN.md` for full specification.