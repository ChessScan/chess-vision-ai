#!/bin/bash
# Entry point for dataset generation container

set -e

echo "Chess Vision Dataset Generator"
echo "=========================================="
echo ""

case "${1:-generate}" in
    generate)
        echo "Running generation workflow..."
        python3 /workspace/scripts/batch_generate.py "${@:2}"
        ;;
    test|verify)
        echo "Running GPU verification..."
        python3 -c "import bpy; print('Blender API OK')"
        nvidia-smi || echo "Note: nvidia-smi may require GPU runtime"
        ;;
    shell|bash)
        exec /bin/bash
        ;;
    *)
        echo "Usage: ${0} {generate|test|shell}"
        exit 1
        ;;
esac
