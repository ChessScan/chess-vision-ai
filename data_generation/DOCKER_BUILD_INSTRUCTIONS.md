# Build Blender Container via Docker API

## Method 1: Direct Docker CLI on Dev Machine

SSH into dev machine and run:
```bash
ssh jan@100.120.200.17

cd ~/.openclaw/workspace || cd ~/workspace

# Build container
docker build -f docker/Dockerfile.blender -t chess-vision-blender:latest .

# Generate sample renders
docker run --rm \
  -v $(pwd)/data_generation:/workspace/data_generation \
  -v $(pwd)/output:/workspace/output \
  chess-vision-blender:latest \
  blender --background --python /workspace/data_generation/blender_side_view_render.py -- \
  --count 5 --output /workspace/output/renders/ --assets /workspace/data_generation/assets/
```

## Method 2: Use Provided Script

File: `build_and_render.sh` (committed)
```bash
chmod +x build_and_render.sh
./build_and_render.sh
```

## Method 3: GitHub Actions

Already configured in `.github/workflows/blender-render.yml`
- Go to GitHub Actions tab
- Run "Blender Chess Render" workflow
- Input: number of images
- Download artifacts when complete

---

## What Will Happen

1. **Build Phase:**
   - Downloads Blender 4.0.2
   - Installs dependencies
   - Copies chess vision code
   - Creates `chess-vision-blender:latest` image

2. **Render Phase:**
   - Imports OBJ assets (pieces + boards)
   - Creates chess scene with FEN positions
   - Sets up side-view camera (45° angle)
   - Configures HDRI lighting
   - Renders 5 sample images
   - Calculates ground truth bounding boxes
   - Exports COCO annotations

3. **Output:**
   - `output/renders/chess_render_0000.png` (640×640)
   - `output/renders/chess_render_0001.png`
   - `output/renders/annotations.json`

---

## Troubleshooting

**If build fails:**
- Check Docker daemon: `docker version`
- Ensure enough disk space: `df -h`

**If render fails:**
- Check Blender logs in container
- Verify assets exist: `ls data_generation/assets/`

**To debug inside container:**
```bash
docker run -it --rm \
  -v $(pwd)/data_generation:/workspace/data_generation \
  chess-vision-blender:latest \
  bash
```