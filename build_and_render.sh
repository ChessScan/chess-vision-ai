#!/bin/bash
# Build and run Blender rendering container on dev machine
# Run this script ON THE DEV MACHINE (100.120.200.17)

cd /home/jan/.openclaw/workspace || cd ~/workspace || cd /workspace

REPO_ROOT=$(pwd)
DATA_GEN_DIR="$REPO_ROOT/data_generation"

echo "======================================"
echo "Chess Vision Blender Container Builder"
echo "======================================"
echo "Repo: $REPO_ROOT"
echo ""

# Check if running on dev machine
if [ "$(hostname -I | grep 100.120.200.17)" = "" ] && [ "$(whoami)" != "jan" ]; then
    echo "⚠ Warning: This should run on dev machine (100.120.200.17)"
    echo "Current host: $(hostname)"
    echo ""
fi

# Build the Blender container
echo "Building Blender container..."
docker build -f docker/Dockerfile.blender -t chess-vision-blender:latest .

if [ $? -ne 0 ]; then
    echo "✗ Docker build failed"
    exit 1
fi

echo "✓ Container built successfully"
echo ""

# Run sample render
echo "Starting render (5 sample images)..."
mkdir -p "$DATA_GEN_DIR/output/renders"

docker run --rm \
    --gpus all \
    -v "$DATA_GEN_DIR:/workspace/data_generation" \
    -v "$DATA_GEN_DIR/output:/workspace/output" \
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    chess-vision-blender:latest \
    blender --background --python /workspace/data_generation/blender_side_view_render.py -- \
    --count 5 \
    --output /workspace/output/renders/ \
    --assets /workspace/data_generation/assets/ \
    --samples 128

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "✓ Render Complete!"
    echo "======================================"
    echo ""
    echo "Output files:"
    ls -lh "$DATA_GEN_DIR/output/renders/*.png" 2>/dev/null | head -10
    echo ""
    echo "Annotations:"
    cat "$DATA_GEN_DIR/output/renders/annotations.json" 2>/dev/null | head -30
    echo ""
    echo "Next steps:"
    echo "1. Review the generated PNGs"
    echo "2. Check camera angle and lighting"
    echo "3. Adjust parameters if needed"
    echo "4. Scale to full dataset"
else
    echo ""
    echo "✗ Render failed"
    echo "Check logs above for errors"
    exit 1
fi
