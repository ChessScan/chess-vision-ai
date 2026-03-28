# Agent Reference for Vision Work

Quick reference for agents working on computer vision tasks.

## Start Here

**New to CV on ChessScan?** Read in order:
1. [README.md](./README.md) - Project overview
2. [TECHNICAL_ARCHITECTURE.md](./TECHNICAL_ARCHITECTURE.md) - System design
3. This file for specific tasks

## Quick Task Reference

### "I need to work on board detection"

→ Read [BOARD_DETECTION.md](./BOARD_DETECTION.md)

**Key decisions already made:**
- Approach: Keypoint detection (CornerNet-style)
- Backbone: MobileNetV2
- Data: Synthetic (Blender) + Real annotated photos

**Your task:**
- Generate synthetic training data OR
- Implement/train keypoint detection model OR
- Evaluate on test set

**Container:** Use `cv-dev` on dev machine (see `memory/dev-machine-setup.md`)

```bash
# Access dev machine
docker -H tcp://100.120.200.17:2375 run -it --rm \
  -v /home/user/chess-vision-ai:/workspace \
  chess-vision:dev
```

---

### "I need to work on piece classification"

→ Read [PIECE_CLASSIFICATION.md](./PIECE_CLASSIFICATION.md)

**Key decisions already made:**
- Architecture: EfficientNet-B0
- Input: 100×100 pixel crops
- Classes: 13 (empty + 6 white + 6 black pieces)

**Your task:**
- Generate training data (Blender synthetic) OR
- Train/fine-tune EfficientNet model OR
- Convert to TFLite OR
- Evaluate accuracy

**Container:** 
```bash
# For training (GPU)
docker -H tcp://100.120.200.17:2375 run -it --rm --gpus all \
  -v /home/user/chess-vision-ai:/workspace \
  chess-vision:training

# For development
docker -H tcp://100.120.200.17:2375 run -it --rm \
  -v /home/user/chess-vision-ai:/workspace \
  chess-vision:dev
```

---

### "I need to generate training data"

→ Read [data_generation/API_DESIGN_PLAN.md](../../data_generation/API_DESIGN_PLAN.md)

**Quick start:**
```bash
# Access blender container
docker -H tcp://100.120.200.17:2375 run -it --rm \
  -v /home/user/chess-vision-ai:/workspace \
  chess-vision:blender

# Inside container
cd /workspace
chess-gen --config examples/basic_generation.yaml --output ./dataset/
```

**Target:** 130,000 images (130 positions × 100 variations)

---

### "I need to integrate CV into the mobile app"

**Interface to implement:** See [PIPELINE_SPECS.md](./PIPELINE_SPECS.md)

**Your task:**
- Create Flutter MethodChannel to native code
- Load TFLite models in Android/iOS
- Pass camera frames to CV pipeline
- Return FEN/move results to Flutter

**Current implementation:** Mock detection service exists
**Replace with:** Real detection service using these models

---

### "I need to evaluate model performance"

**Metrics to report:**
- Board detection: Corner accuracy, success @ 5px
- Piece classification: Per-square accuracy, confusion matrix
- End-to-end: Move detection accuracy, latency distributions

**Test data:** (Not yet created - this could be your task!)
- Annotated real-world videos
- Ground truth board states

---

## Common Commands

### Docker (Dev Machine)

```bash
# View running containers
docker -H tcp://100.120.200.17:2375 ps

# View all containers (including stopped)
docker -H tcp://100.120.200.17:2375 ps -a

# Pull image updates
docker -H tcp://100.120.200.17:2375 pull chess-vision:dev

# Exec into running container
docker -H tcp://100.120.200.17:2375 exec -it <container_id> bash
```

### Model Development

```bash
# Train board detector
cd /workspace/models/board_detection
python train.py --config configs/mobilenetv2.yaml

# Train piece classifier
cd /workspace/models/piece_classification  
python train.py --config configs/efficientnet_b0.yaml

# Convert to TFLite
python export_tflite.py --model checkpoint.pth --output model.tflite
```

### Data Generation

```bash
# Generate dataset from config
chess-gen --config my_config.yaml --output ./dataset/

# Verify generated images
python scripts/visualize_dataset.py --input ./dataset/
```

## File Locations

| What | Where |
|------|-------|
| Vision docs | `planning/vision/` |
| Data generation | `data_generation/` |
| Mobile app | `chess_vision_app/` |
| Models | `chess-vision-ai/models/` (on dev machine) |
| Training data | `/datasets/` on dev machine |
| Docker setup | `docker/` |

## Status Check

**Before starting work**, check:
```bash
# What's currently in progress?
cat memory/heartbeat-state.json
git status

# What models exist?
ls /home/user/chess-vision-ai/models/

# What's the latest commit?
git log --oneline -5
```

## When to Ask (vs. Proceed)

**Proceed without asking:**
- Reading documentation
- Setting up dev environment
- Running existing scripts
- Fixing typos in docs

**Ask first:**
- Changing architecture decisions
- Adding new dependencies
- Modifying interfaces/specs
- Committing to `main` branch
- Using shared resources (GPU, storage)

## Decision Log

Record important decisions here (or in git commits):

| Date | Decision | Context | Decision Maker |
|------|----------|---------|---------------|
| 2026-03-20 | Use EfficientNet-B0 for pieces | Good mobile performance | CV Team |
| 2026-03-20 | Use keypoint detection for board | More robust than classical | CV Team |
| 2026-03-25 | Synthetic data via Blender | Controlled training data | Data Team |

## Resources

- **TFLite Performance:** https://www.tensorflow.org/lite/performance
- **EfficientNet Paper:** https://arxiv.org/abs/1905.11946
- **OpenCV Docs:** https://docs.opencv.org/
- **Flutter + TFLite:** https://pub.dev/packages/tflite_flutter

## Getting Help

1. Check documentation in `planning/vision/`
2. Look at examples in `data_generation/examples/`
3. Check similar tasks in git history
4. Ask in `#ai-training` or `#vision` Discord channels

---

**Remember:** This document is for quick reference. For full details, always check the linked documents.