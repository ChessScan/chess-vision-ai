# Dev Container Deployment Guide

## Repo Structure

### ChessScan/chess-vision-ai ✅ (DONE)
Already has complete container suite:
- `cv-dev` - General CV/ML (Python, OpenCV, TF, Jupyter)
- `blender-synth` - Blender 4.0 for synthetic data
- `training` - PyTorch/CUDA for model training

### ChessScan/chess-vision-app (TODO)
Staging folder: `staging/chess-vision-app/docker/`

**Push commands:**
```bash
# Clone app repo
git clone git@github.com:ChessScan/chess-vision-app.git /tmp/chess-vision-app
cd /tmp/chess-vision-app

# Copy containers
cp ~/workspace/staging/chess-vision-app/docker/* .

# Commit and push
git add docker/
git commit -m "Add React Native/Expo development container

- Dockerfile.dev: Node.js + React Native CLI + Expo
- docker-compose.yml: Metro bundler and Expo ports exposed
- README.md: Usage instructions"
git push origin main
```

### ChessScan/chess-vision-docs (TODO)
Staging folder: `staging/chess-vision-docs/docker/`

**Push commands:**
```bash
# Clone docs repo
git clone git@github.com:ChessScan/chess-vision-docs.git /tmp/chess-vision-docs
cd /tmp/chess-vision-docs

# Copy containers
cp ~/workspace/staging/chess-vision-docs/docker/* .

# Commit and push
git add docker/
git commit -m "Add MkDocs development container

- Dockerfile.dev: MkDocs with Material theme
- docker-compose.yml: Live reload on port 8000
- README.md: Usage instructions"
git push origin main
```

## Build Commands (Tomorrow)

```bash
# In each repo's docker/ folder:
docker-compose build

# Or build specific container:
docker-compose build cv-dev
docker-compose build blender-synth
docker-compose build training

# Push to registry (if needed):
docker tag chess-vision:dev ghcr.io/chessscan/cv-dev:latest
docker push ghcr.io/chessscan/cv-dev:latest
```

## Container Summary

| Repo | Container | Purpose | Ports |
|------|-----------|---------|-------|
| chess-vision-ai | cv-dev | General Python CV/ML | 8888 (Jupyter) |
| chess-vision-ai | blender-synth | Synthetic data gen | - |
| chess-vision-ai | training | GPU model training | 8889, 6006 |
| chess-vision-app | app-dev | React Native/Expo | 8081, 19000-19002 |
| chess-vision-docs | docs-dev | MkDocs | 8000 |
