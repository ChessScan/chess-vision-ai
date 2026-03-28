# Chess Vision Documentation

**Single source of truth for all computer vision work on ChessScan.**

All agents working on CV tasks should reference these documents before starting work.

## Quick Navigation

| Document | Purpose | Read This If... |
|----------|---------|-----------------|
| [TECHNICAL_ARCHITECTURE.md](./TECHNICAL_ARCHITECTURE.md) | System overview, pipelines, data flow | You're new to the project |
| [BOARD_DETECTION.md](./BOARD_DETECTION.md) | Board detection algorithms & approaches | Working on board detection |
| [PIECE_CLASSIFICATION.md](./PIECE_CLASSIFICATION.md) | Piece recognition model specs | Working on piece classifier |
| [PIPELINE_SPECS.md](./PIPELINE_SPECS.md) | Input/output formats, constraints | Integrating CV components |
| [AGENT_REFERENCE.md](./AGENT_REFERENCE.md) | Quick reference for agents | Doing CV development |

## Project Overview

ChessScan automatically detects chess positions from video, enabling:
- Live game recording and move tracking
- PGN export from physical games
- Analysis and review capabilities

### Key Challenge: Perspective Distortion

Camera angle of 30-60° creates significant perspective distortion. The pipeline must:
1. Detect board corners from skewed view
2. Apply homography transform for rectification
3. Subdivide into 64 squares
4. Classify each square for piece presence/type

### System Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Raw Frames    │────▶│ Board Detection  │────▶│  Perspective    │
│  (Video Stream) │     │  (4 Corner Pts)  │     │  Rectification  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Temporal       │◄────│ Piece            │◄────│  Grid 8×8       │
│  Tracking       │     │  Classification  │     │  Subdivision    │
│  (Frame-to-frame)     │  (13-class)      │     │  (64 Squares)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
       │
       ▼
┌─────────────────┐
│   Board State   │────▶ PGN Export, Analysis, Display
│   (FEN/SAN)     │
└─────────────────┘
```

## Current Status

**Board Detection:** Planning phase - evaluating classical vs ML approaches  
**Piece Classification:** Planning phase - EfficientNet-B0 baseline defined  
**Training Data:** Blender synthetic generator in development  
**Mobile App:** Flutter MVP with mock detection complete

## Key Decisions

1. **Synthetic Training Data:** Using Blender-generated positions (130k images) rather than scraping
2. **On-Device Inference:** TFLite/Mobile target, <100ms inference time
3. **Modular Pipeline:** Board detection and piece classification as separate stages
4. **Temporal Smoothing:** Frame-to-frame tracking for stability

## Related Resources

- **Data Generation:** `../../data_generation/`
- **Mobile App:** `../../chess_vision_app/`
- **Dev Containers:** See `../../memory/dev-machine-setup.md`

---

*Last updated: 2026-03-28*  
*Maintainer: CV Team*