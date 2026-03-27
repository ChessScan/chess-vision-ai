# Chess Vision Dev Containers

## Quick Start

```bash
cd docker
docker-compose up -d cv-dev
docker exec -it chess-vision-dev bash
```

## Container Strategy

**Primary: `cv-dev`** - Python/OpenCV/TensorFlow environment for:
- Board detection prototyping
- Piece classification model dev
- PGN/FEN utilities
- Jupyter notebooks for experimentation

## Services

| Service | Purpose | Ports |
|---------|---------|-------|
| cv-dev | Main development | 8888 (Jupyter) |

## Jupyter

```bash
# Inside container
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser
```

Access at: `http://localhost:8888`
