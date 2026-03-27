# Chess Vision AI - Dev Containers

## Overview

Three specialized containers for AI/CV development:

| Container | Purpose | Image |
|-----------|---------|-------|
| `cv-dev` | General Python CV/ML dev | `chess-vision:dev` |
| `blender-synth` | Synthetic data generation | `chess-vision:blender` |
| `training` | GPU model training | `chess-vision:training` |

## Quick Start

```bash
cd docker

# Build all images
docker-compose build

# Start specific container
docker-compose up -d cv-dev
docker exec -it chess-vision-dev bash
```

## Containers

### cv-dev
General development with OpenCV, TensorFlow, Jupyter.

```bash
docker-compose up -d cv-dev
docker exec -it chess-vision-dev bash

# Start Jupyter
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser
```

Port: `8888` (Jupyter)

### blender-synth
Blender 4.0 + Python for generating synthetic training data.

```bash
docker-compose up -d blender-synth
docker exec -it chess-vision-blender bash

# Generate dataset
blender -b scene.blend -P render.py
```

### training
PyTorch with CUDA for model training. Requires NVIDIA GPU.

```bash
docker-compose up -d training
docker exec -it chess-vision-training bash

# Monitor training
tensorboard --logdir=runs --bind_all
```

Ports: `8889` (Jupyter), `6006` (TensorBoard)

## Building Images (Tomorrow)

```bash
# Standard build
docker-compose build

# For training container, ensure nvidia-docker2 runtime
docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi
```
