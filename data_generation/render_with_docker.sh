#!/bin/bash
# Build and run Blender rendering container

cd "$(dirname "$0")"
REPO_ROOT="$(cd .. && pwd)"

echo "======================================"
echo "Chess Vision Blender Renderer"
echo "======================================"

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "✗ Docker not found. Install Docker to use this script."
    exit 1
fi

echo "Building Blender container..."
docker build -f Dockerfile.blender -t chess-vision-blender:latest ..

if [ $? -ne 0 ]; then
    echo "✗ Failed to build container"
    exit 1
fi

echo "✓ Container built"

# Run render
echo ""
echo "Starting render..."
echo "  Output: ./renders/"
echo "  Count: ${1:-5} images"
echo ""

docker run --rm \
    -v "$REPO_ROOT/data_generation:/workspace/data_generation" \
    -v "$REPO_ROOT/output:/workspace/output" \
    chess-vision-blender:latest \
    blender --background --python /workspace/data_generation/blender_side_view_render.py -- \
    --count "${1:-5}" \
    --output /workspace/output/renders/ \
    --assets /workspace/data_generation/assets/ \
    --samples 128

echo ""
echo "======================================"
if [ $? -eq 0 ]; then
    echo "✓ Renders complete!"
    echo "  Check: $REPO_ROOT/output/renders/"
else
    echo "✗ Render failed"
fi
echo "======================================"
