#!/bin/bash
set -e

echo "=== ChessVision Blender Synthetic Data Generator ==="
echo "Blender version: $(blender --version | head -2)"
echo ""

# Validate assets exist
if [ ! -d "/workspace/assets/models" ]; then
    echo "ERROR: Chess piece models not found in /workspace/assets/models"
    exit 1
fi

MODEL_COUNT=$(ls /workspace/assets/models | wc -l)
echo "Loaded $MODEL_COUNT chess model sets"

# Support different run modes
if [ "$1" = "batch" ]; then
    shift
    echo "Running batch render generation..."
    exec python3 /workspace/generate_dataset.py "$@"
elif [ "$1" = "single" ]; then
    shift
    FEN="${1:-rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR}"
    echo "Rendering single FEN: $FEN"
    blender -b /workspace/chess_board.blend --python /workspace/render_fen.py -- --fen "$FEN" --output /workspace/output/
elif [ "$1" = "daemon" ]; then
    echo "Running in daemon mode. Waiting for FEN tasks..."
    exec python3 /workspace/daemon.py
else
    echo "Usage:"
    echo "  docker run chess-vision/blender-synth batch [count]    - Generate dataset"
    echo "  docker run chess-vision/blender-synth single [FEN]       - Render single position"
    echo "  docker run chess-vision/blender-synth daemon             - Task queue daemon"
    echo ""
    echo "Output directory: /workspace/output/"
    bash
fi
