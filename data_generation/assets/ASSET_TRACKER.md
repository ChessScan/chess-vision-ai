# Asset Collection Tracker

Track what you download here as you collect assets.

## Download Sources

### High Priority Downloads

#### Site: Sketchfab (sketchfab.com)
- [ ] **Model 1:** _______________
  - URL: _______________
  - Author: _______________
  - License: _______________
  - Pieces included: _______________
  - Format: _______________
  - Downloaded to: _______________
  
- [ ] **Model 2:** _______________
  - URL: _______________
  - Author: _______________
  - License: _______________
  - Pieces included: _______________
  - Format: _______________
  - Downloaded to: _______________

#### Site: BlendSwap (blendswap.com)
- [ ] **Model 1:** _______________
  - URL: _______________
  - Author: _______________
  - License: _______________
  - Pieces included: _______________
  - Format: _______________
  - Downloaded to: _______________

#### Site: Polyhaven (polyhaven.com)
**Wood Textures:**
- [ ] Texture set 1: _______________
  - Type: Light / Dark / Both
  - Resolution: _______________
  - Maps: Albedo / Normal / Roughness / AO
  - URL: _______________
  
- [ ] Texture set 2: _______________
  - Type: Light / Dark / Both
  - Resolution: _______________
  - Maps: _______________
  - URL: _______________

**HDRI Environments:**
- [ ] HDRI 1: _______________
  - Category: Office / Tournament / Home / Outdoor
  - URL: _______________
  
- [ ] HDRI 2: _______________
  - Category: Office / Tournament / Home / Outdoor
  - URL: _______________

- [ ] HDRI 3: _______________
  - Category: Office / Tournament / Home / Outdoor
  - URL: _______________

- [ ] HDRI 4: _______________
  - Category: Office / Tournament / Home / Outdoor
  - URL: _______________

- [ ] HDRI 5: _______________
  - Category: Office / Tournament / Home / Outdoor
  - URL: _______________

### Downloaded Assets Summary

| Asset Type | Count | Location | Status |
|------------|-------|----------|--------|
| Piece sets | ___ | pieces/set_*/ | ☐ Good ☐ Needs work |
| Board textures | ___ | boards/*/ | ☐ Good ☐ Needs work |
| HDRI | ___ | hdri/ | ☐ Good ☐ Needs work |

## Quality Check Results

### Set 1: _______________
- [ ] All 12 piece types present (6 white, 6 black)
- [ ] Scale correct (king ~9cm)
- [ ] Materials import correctly
- [ ] No missing textures
- [ ] License documented

### Set 2: _______________
- [ ] All 12 piece types present
- [ ] Scale correct
- [ ] Materials import correctly
- [ ] No missing textures
- [ ] License documented

### Set 3: _______________
- [ ] All 12 piece types present
- [ ] Scale correct
- [ ] Materials import correctly
- [ ] No missing textures
- [ ] License documented

## Issues Found

| Asset | Problem | Workaround |
|-------|---------|------------|
| ___ | ___ | ___ |
| ___ | ___ | ___ |

## Next Actions

1. ___________________________________
2. ___________________________________
3. ___________________________________

## Command Reference

**Check what you have:**
```bash
bash /home/node/.openclaw/workspace/data_generation/assets/check_assets.sh
```

**Generate procedural fallback:**
```bash
blender --background --python procedural_pieces.py
blender --background --python procedural_board.py
```

**Test import:**
```bash
blender --background --python -c "import bpy; bpy.ops.import_scene.obj(filepath='/path/to/piece.obj')"
```