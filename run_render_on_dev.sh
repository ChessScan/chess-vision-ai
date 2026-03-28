#!/bin/bash
# Run this on the DEV MACHINE: 100.120.200.17

cd ~/.openclaw/workspace || cd ~/workspace || exit 1

echo "======================================"
echo "Building Blender Container on Dev Machine"
echo "======================================"

# Ensure we're on dev machine (check hostname)
if [[ "$HOSTNAME" != *"dev"* ]] && [[ "$HOSTNAME" != *"chess"* ]]; then
    echo "⚠ Warning: This should run on dev machine (100.120.200.17)"
fi

# Build the Blender container
echo ""
echo "Building chess-vision-blender container..."
docker build -f docker/Dockerfile.blender -t chess-vision-blender:latest .

if [ $? -ne 0 ]; then
    echo "✗ Build failed"
    exit 1
fi

echo "✓ Container built"

# Run the render
echo ""
echo "Starting rendering (5 sample images)..."
mkdir -p data_generation/output/renders

docker run --rm \
    --name chess-render \
    -v "$(pwd)/data_generation:/workspace/data_generation" \
    -v "$(pwd)/data_generation/output:/workspace/output" \
    chess-vision-blender:latest \
    blender --background --python /workspace/data_generation/blender_side_view_render.py -- \
    --count 5 \
    --output /workspace/output/renders/ \
    --assets /workspace/data_generation/assets/

# Check results
if [ -f "data_generation/output/renders/chess_render_0000.png" ]; then
    echo ""
    echo "======================================"
    echo "✓ RENDERS COMPLETE!"
    echo "======================================"
    echo ""
    echo "Files generated:"
    ls -lh data_generation/output/renders/*.png
    echo ""
    echo "Annotations:"
    ls -lh data_generation/output/renders/annotations.json
    echo ""
else
    echo "✗ Render failed - check logs above"
    exit 1
fi
