# Chess Vision Assets

Free 3D chess assets for synthetic data generation.

## Directory Structure

```
assets/
├── pieces/              # Chess piece 3D models
│   ├── tournament_plastic/    # Staunton plastic style
│   ├── classic_wood/          # Traditional wooden
│   └── modern_minimal/        # Contemporary designs
├── boards/              # Chess board models + textures
│   ├── walnut_4k/
│   ├── maple_green/
│   └── mahogany/
├── hdri/                # Environment lighting
│   ├── office/
│   ├── home/
│   └── outdoors/
└── reference/           # Documentation, previews
```

## Asset Requirements

### Chess Pieces (Per Set)
- [ ] White King
- [ ] White Queen  
- [ ] White Rook (×2)
- [ ] White Bishop (×2)
- [ ] White Knight (×2)
- [ ] White Pawn (×8)
- [ ] Black King
- [ ] Black Queen
- [ ] Black Rook (×2)
- [ ] Black Bishop (×2)
- [ ] Black Knight (×2)
- [ ] Black Pawn (×8)

**Formats (best to acceptable):**
1. `.blend` (Blender native)
2. `.fbx` (Universal, materials included)
3. `.obj` + `.mtl` (Widely supported)
4. `.glb`/`.gltf` (Modern web standard)

**Specs:**
- Poly count: 1K-10K per piece (higher for hero pieces)
- Scale: Normalized to fit standard board
- Origin: Base of piece at (0,0,0)
- Materials: PBR (metallic/roughness workflow)

### Chess Boards
- [ ] Board mesh (square or rectangular)
- [ ] Light square texture/albedo
- [ ] Dark square texture/albedo
- [ ] Normal map (wood grain)
- [ ] Roughness map
- [ ] Optional: Border/frame mesh

**Dimensions:**
- Tournament standard: 56cm × 56cm outer
- Square size: 5.7cm × 5.7cm
- Thickness: 2-3cm
- Border: 2cm

## Sourcing Guide

### Free Model Sites (Checked, CC Licensed)

#### 1. **Sketchfab** (https://sketchfab.com)
Search: "chess set", "staunton chess", "tournament chess"
Filters: Downloadable + CC licenses

**Recommended models to check:**
- "Wood Chess Set" by [various artists]
- "Chess Pieces" by [scanned collections]
- "Staunton Chess Set" (look for OBJ/FBX)

**License:** CC Attribution (give credit in dataset docs)

#### 2. **BlendSwap** (https://blendswap.com)
Search: "chess"
Requires free account

**Advantages:**
- Native .blend files
- Blender materials ready
- Community rated

#### 3. **CGTrader** (https://cgtrader.com)
Search: "chess"
Filter: Free

**Look for:**
- Low poly game-ready sets
- PBR textured collections
- Complete sets (not single pieces)

#### 4. **Free3D** (https://free3d.com)
Search: "chess pieces"
Filter: Free + OBJ/FBX format

#### 5. **Turbosquid** (https://turbosquid.com)
Search: "chess"
Filter: Free

Often lower quality but usable for variety.

### Specific Known Free Assets

#### Complete Sets (Download Immediately)

**A. Staunton Tournament Set**
- Source: Sketchfab "Wooden Chess Set"
- Artist: Varies (search latest)
- License: CC Attribution
- Format: Usually GLB/OBJ
- Note: Download all 6 piece types

**B. Basic Plastic Set**
- Source: Free3D or CGTrader
- Search: "plastic chess pieces"
- Style: Tournament regulation
- Color: White/Black or Natural wood

**C. Classic Wood Set**
- Source: BlendSwap
- Search: "chess set"
- Look for: Detailed wood materials

#### Boards & Textures

**Wood Textures (CC0):**
- https://ambientcg.com (search "wood", "floor")
- https://polyhaven.com/textures (formerly HDRI Haven)
- https://cc0textures.com

**Seamless wood textures needed:**
- [ ] Light oak/maple (for light squares)
- [ ] Dark walnut (for dark squares)
- [ ] Mahogany reddish tone
- [ ] Tournament green (plastic)

**HDRI Environments (CC0):**
- https://polyhaven.com/hdris
- Categories: indoor, studio, office

Download ~5 different:
- Office with windows
- Tournament hall
- Home warm lighting
- Studio neutral
- Outdoor/indoor mix

### Asset Selection Criteria

**Priority 1: Tournament Standard (Must Have)**
- [ ] Staunton design pieces, plastic or wood
- [ ] Standard tournament board (green/buff or wood)
- [ ] Clean, recognizable silhouettes

**Priority 2: Classic Wood (High Value)**
- [ ] Detailed wood grain
- [ ] Traditional turned design
- [ ] Warm color tones

**Priority 3: Variety/Distinct (Medium Value)**
- [ ] Modern minimalist designs
- [ ] 3D printed aesthetic
- [ ] Different proportions

**Avoid:**
- Fantasy themed (dragons, etc.)
- Non-standard proportions
- Excessively ornate
- Copyrighted designs (e.g., LEGO)

## Download Checklist

### Immediate Actions
- [ ] Download 2-3 complete piece sets from Sketchfab
- [ ] Get 3+ wood texture sets from Polyhaven
- [ ] Download 5 HDRI environments
- [ ] Save all license attribution info

### File Organization
```
pieces/
  set_01_staunton/
    README.txt (license info)
    white_king.fbx
    white_queen.fbx
    ...
    black_pawn.fbx
    preview.png
  set_02_classic/
    ...
  set_03_modern/
    ...

boards/
  board_01_walnut/
    board.obj
    light_square_albedo.png
    dark_square_albedo.png
    normal.png
    roughness.png
    README.txt
  board_02_maple/
    ...

hdri/
  office_morning_4k.hdr
  tournament_hall_4k.hdr
  home_evening_4k.hdr
  studio_neutral_4k.hdr
  outdoor_cloudy_4k.hdr
```

## License Tracking

Create `LICENSES.md` with:
```markdown
# Asset Licenses

## Set 1: Staunton Tournament
- Source: Sketchfab
- Model: "[Exact Name]"
- Author: [Name]
- License: CC BY 4.0
- URL: [Direct link]
- Downloaded: [Date]
- Modifications: None / Scaled to cm

## Textures
- Source: Polyhaven
- License: CC0
- ...
```
**Critical:** Track licenses for dataset documentation and legal compliance.

## Quick Start Commands

Since web search is limited, here's what to do:

1. **Open browser, go to:**
   - https://sketchfab.com/search?q=chess+set&type=models downloadable=true
   - https://polyhaven.com/hdris (download 5 indoor)
   - https://polyhaven.com/textures (download wood)

2. **Download criteria:**
   - OBJ, FBX, or GLB format
   - CC license (not NC if commercial use planned)
   - Complete sets preferred

3. **Organize into folders above**

4. **Test in Blender:**
   - Import → Check scale
   - Verify materials
   - Render test image

## Next Steps After Download

1. Import all pieces into Blender
2. Normalize scales (kings ~9cm tall)
3. Create material variants
4. Export as `.blend` collection
5. Test render one complete position

See `../IMPLEMENTATION.md` for technical import/scaling process.