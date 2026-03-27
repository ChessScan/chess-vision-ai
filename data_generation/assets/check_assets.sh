#!/bin/bash
# Quick asset download helper
# Run this to check and organize assets

ASSETS_DIR="/home/node/.openclaw/workspace/data_generation/assets"

echo "=== Chess Vision Asset Checker ==="
echo ""

# Check directory structure
echo "Checking folder structure..."
for dir in pieces/boards/{walnut,maple,mahogany,plastic} pieces/{set_01,set_02,set_03} hdri/{office,tournament,home,studio,outdoor}; do
    if [ -d "$ASSETS_DIR/$dir" ]; then
        echo "  ✓ $dir exists"
    else
        echo "  ✗ $dir missing - creating..."
        mkdir -p "$ASSETS_DIR/$dir"
    fi
done

echo ""
echo "=== Asset Inventory ==="

# Count piece files
echo ""
echo "Piece Sets:"
for set in set_01 set_02 set_03; do
    count=$(find "$ASSETS_DIR/pieces/$set" -type f \( -name "*.obj" -o -name "*.fbx" -o -name "*.glb" -o -name "*.blend" \) 2>/dev/null | wc -l)
    echo "  $set: $count model files"
done

# Count board textures
echo ""
echo "Board Textures:"
for board in walnut maple mahogany plastic; do
    count=$(find "$ASSETS_DIR/boards/$board" -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.exr" \) 2>/dev/null | wc -l)
    echo "  $board: $count texture files"
done

# Count HDRI
echo ""
echo "HDRI Environments:"
count=$(find "$ASSETS_DIR/hdri" -name "*.hdr" -o -name "*.exr" 2>/dev/null | wc -l)
echo "  Total: $count HDRI files"

echo ""
echo "=== Quick Validation ==="

# Check for LICENSES.md
if [ -f "$ASSETS_DIR/LICENSES.md" ]; then
    echo "  ✓ LICENSES.md exists (good!)"
else
    echo "  ✗ LICENSES.md missing - document your assets!"
fi

# Check piece completeness
for piece in king queen rook bishop knight pawn; do
    found=false
    for ext in obj fbx glb blend; do
        if find "$ASSETS_DIR/pieces" -name "*white*${piece}*.$ext" -o -name "*${piece}*white*.$ext" 2>/dev/null | grep -q .; then
            found=true
            break
        fi
    done
    if [ "$found" = true ]; then
        echo "  ✓ Found white $piece"
    else
        echo "  ✗ Missing white $piece"
    fi
done

echo ""
echo "=== Next Steps ==="
echo "1. Place downloaded assets in folders above"
echo "2. Update LICENSES.md with attribution"
echo "3. Run: blender -P validate_assets.py (once created)"
echo "4. Test render one complete position"
echo ""
echo "Need procedural fallback? See procedural_pieces.py"