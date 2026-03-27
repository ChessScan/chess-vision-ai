# Chess Vision AI

Model training and synthetic data generation for chess piece classification.

## Tech Stack
- PyTorch → ONNX → TensorFlow Lite
- Blender (synthetic data generation)
- EfficientNet-B0 backbone

## Structure
- `/synthetic_data/` - Blender scenes and render scripts
- `/training/` - Model training scripts
- `/inference/` - Model export and inference code

## Quick Start
```bash
pip install -r requirements.txt
cd synthetic_data/blender && python generate_dataset.py
```

## Related Repos
- [chess-vision-app](https://github.com/traceaidev/chess-vision-app) - Mobile app
- [chess-vision-docs](https://github.com/traceaidev/chess-vision-docs) - Architecture & planning
