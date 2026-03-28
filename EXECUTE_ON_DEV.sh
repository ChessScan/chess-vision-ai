#!/bin/bash
# ============================================
# CRITICAL: RUN THIS ON DEV MACHINE (100.120.200.17)
# ============================================
#
# Copy to dev machine and execute:
#
#   ssh jan@100.120.200.17
#   cd ~/.openclaw/workspace
#   chmod +x EXECUTE_ON_DEV.sh
#   ./EXECUTE_ON_DEV.sh
#
# This will:
#   1. Build Blender container with all dependencies
#   2. Generate 5 sample chess renders (640×640)
#   3. Save to data_generation/output/renders/
#   4. Send back annotations in COCO format
#
# Expected time: 10-15 minutes
# Output: Photorealistic Blender renders with 3D perspective
# ============================================

echo "Chess Vision - Blender Rendering on Dev Machine"
echo "=================================================="
echo ""
echo "Checking environment..."

# Verify we're on dev machine
if ! hostname | grep -q "dev\|chess"; then
    echo "⚠ WARNING: This should run on dev machine (100.120.200.17)"
    echo "Current: $(hostname)"
    echo ""
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "✗ Docker not found"
    exit 1
fi

# Navigate to workspace
cd ~/.openclaw/workspace || cd ~/workspace || {
    echo "✗ Workspace not found"
    exit 1
}

# Pull latest code
echo "Pulling latest code..."
echo "git pull origin feature/blender-image-framework"
git pull origin feature/blender-image-framework

# Build Blender container
echo ""
echo "Building Blender container..."
docker build -f docker/Dockerfile.blender -t chess-vision-blender:latest .

if [ $? -ne 0 ]; then
    echo "✗ Container build failed"
    exit 1
fi

echo "✓ Container ready"

# Create output directories
mkdir -p data_generation/output/renders

# Execute render
echo ""
echo "=================================================="
echo "STARTING RENDER (5 sample images)"
echo "=================================================="
echo "This will take 10-15 minutes..."
echo ""

docker run --rm \
    --name chess-render-$$ \
    -v "$(pwd)/data_generation:/workspace/data_generation" \
    -v "$(pwd)/data_generation/output:/workspace/output" \
    -w /workspace \
    chess-vision-blender:latest \
    blender --background --python /workspace/data_generation/blender_side_view_render.py -- \
    --count 5 \
    --output /workspace/output/renders/ \
    --assets /workspace/data_generation/assets/ \
    --samples 128

RENDER_EXIT=$?

# Report results
echo ""
echo "=================================================="
if [ $RENDER_EXIT -eq 0 ] && [ -f "data_generation/output/renders/chess_render_0000.png" ]; then
    echo "✓ SUCCESS - Renders generated!"
    echo "=================================================="
    echo ""
    echo "Output files:"
    ls -lh data_generation/output/renders/*.png | head -6
    echo ""
    echo "Annotations:"
    cat data_generation/output/renders/annotations.json | head -50
    echo ""
    echo "Next step:"
    echo "  Copy renders back to your machine:"
    echo "  scp jan@100.120.200.17:~/.openclaw/workspace/data_generation/output/renders/*.png ./"
    echo ""
    echo "Then send them to the ai-training agent for review"
else
    echo "✗ RENDER FAILED"
    echo "=================================================="
    echo ""
    echo "Troubleshooting:"
    echo "  - Check Docker logs: docker logs chess-render-$$"
    echo "  - Verify assets exist: ls data_generation/assets/"
    echo "  - Check permissions"
    exit 1
fi