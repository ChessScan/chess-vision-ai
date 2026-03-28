# Data Synthesis Agent Specification
**Agent:** codex-data  
**Task:** Generate 1000 synthetic training images  
**Duration:** ~2 hours

---

## OBJECTIVE
Generate photorealistic chess board images from shallow camera angles (15-45°) for training the board detection and piece classification models.

---

## OUTPUT REQUIREMENTS

**Location:** `/workspace/shared/datasets/synthetic_renders/`

**Files per image:**
- `chess_render_{nnnn}.png` - RGB image (1280x720)
- `chess_render_{nnnn}_depth.png` - Depth map (optional)
- `chess_render_{nnnn}.json` - Metadata

**Metadata format:**
```json
{
  "id": "0001",
  "camera_angle": 32.5,
  "camera_distance": 0.6,
  "lighting": "natural_room",
  "board_texture": "walnut_walnut",
  "piece_style": "neo",
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "board_bbox": [120, 80, 600, 480],
  "pieces": [
    {"type": "P", "color": "white", "bbox": [150, 400, 180, 430]},
    ...
  ]
}
```

---

## TECHNICAL SPECS

**Camera:**
- Angle: random 15-45° from horizontal (NOT top-down)
- Distance: random 0.5-0.8m from board edge
- Lens: 35mm equivalent
- Position: random ±30° rotation around board

**Board:**
- Size: Tournament standard (500x500mm)
- Textures: Mix of walnut, maple, cherry, plastic
- Square size: ~62mm
- Border: Include board edge in frame

**Pieces:**
- Styles: chess.com Neo (primary), Classic Staunton (secondary)
- Materials: Matte plastic, polished wood
- Colors: White/Black contrast

**Lighting:**
- Primary: Window natural light (soft shadows)
- Secondary: Ceiling ambient
- Avoid: Harsh direct light, uniform studio lighting

**Environment:**
- Background: Table surface continuation
- Random variations: Wood grain, cloth, glass

---

## SCENE VARIATIONS

Generate diverse positions:
1. **Starting position** (50 images)
2. **Random mid-game** (300 images)
3. **Endgame positions** (100 images)
4. **Pawn structures** (100 images)
5. **Tactical positions** (150 images)
6. **Piece scattered** (150 images)
7. **Board edge cases** (150 images)

**Board edge cases:**
- Partial board in frame
- Extreme angle (>40°)
- Cluttered background
- Multiple boards
- Moving pieces (blur)

---

## QUALITY CHECKLIST

Each image must:
- ✅ Show board at shallow angle (not top-down)
- ✅ Include natural lighting with shadows
- ✅ Have realistic perspective
- ✅ Be at least 720p resolution
- ✅ Include proper metadata with FEN + bboxes

**Reject if:**
- Flat/2D appearance
- Top-down (90°) view
- Uniform lighting (no shadows)
- Missing metadata

---

## WORKFLOW

1. Set up Blender scene with configurable camera rig
2. Generate random position (Python-Chess library)
3. Render with randomized parameters
4. Save image + metadata
5. Update progress in `/workspace/coordinator/status/codex-data.json`
6. Repeat until 1000 images

---

## CHECKPOINTS

Report to coordinator at:
- First 10 images (validation)
- 100 images (25% complete)
- 250 images (50% complete)
- 500 images (75% complete)
- 750 images (90% complete)
- 1000 images (DONE)

**On completion:**
- Merge datasets to shared location
- Update status file: `"status": "complete"`
- Await next assignment
