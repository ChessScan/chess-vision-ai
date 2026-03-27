# Asset Sourcing Guide - Direct Links & Instructions

## Step-by-Step Download Process

### Step 1: Visit These Sites

**Primary Sources (Free, Blender-compatible):**

| Site | URL | What to Search | Account Needed |
|------|-----|----------------|----------------|
| Sketchfab | https://sketchfab.com | "chess set staunton" | Free account |
| BlendSwap | https://blendswap.com | "chess" | Free account |
| Polyhaven | https://polyhaven.com | Textures + HDRIs | No account |
| AmbientCG | https://ambientcg.com | "wood floor" | No account |
| CGTrader | https://cgtrader.com | "chess free" | Free account |

### Step 2: Recommended Downloads

#### Chess Piece Sets (Get 2-3)

**Option A: Sketchfab - "Chess Set" by various**
1. Go to: https://sketchfab.com/search?q=chess+set&type=models&sort_by=-likeCount&generalCategories=models
2. Filter: "Downloadable" = ON
3. Sort by most liked
4. Look for:
   - "Wood Chess Set" (complete Staunton)
   - "Chess Pieces" (scanned, realistic)
   - "Chess Set - Tournament"
5. Download format: GLB or OBJ (convert to FBX if needed)

**Option B: BlendSwap**
1. Register at blendswap.com
2. Search "chess"
3. Look for:
   - "Chess Set" with high ratings
   - Complete .blend files
4. Download .blend directly

**Option C: CGTrader Free**
1. https://www.cgtrader.com/free-3d-models?keywords=chess
2. Filter by "Free"
3. Download OBJ or FBX

#### Wood Textures (For Boards)

From Polyhaven (CC0 - no attribution needed):

1. **Light Square Textures:**
   - https://polyhaven.com/textures (search "wood", "floor")
   - Look for: oak, maple, birch (light tones)
   - Download: 4K resolution minimum
   - Files needed: albedo/diffuse, normal, roughness

2. **Dark Square Textures:**
   - Search: walnut, mahogany, dark wood
   - Same file types

**Direct material types to get:**
- [ ] `wood_floor_oak` (light squares)
- [ ] `wood_floor_walnut` (dark squares)
- [ ] `wood_table_worn` (border)
- [ ] `fabric_felt` (optional board bottom)

#### HDRI Environments

From Polyhaven HDRIs:

**Get 5-6 of these categories:**
1. **Office:**
   - Search "office", "studio"
   - 4K resolution minimum
   - Examples: _studio_small_09, _office_** 

2. **Tournament/Indoor:**
   - Search "hall", "indoor"
   - Examples: _hotel_room, _classroom_

3. **Home:**
   - Search "apartment", "living room"
   - Examples: _living_room_4k_

4. **Neutral Studio:**
   - Search "studio", "empty"
   - Examples: _studio_small_09_

5. **Outdoor/Natural:**
   - Search "sky", "cloudy"
   - Examples: _kloetzle_blei_4k_

### Step 3: Specific Recommendations

Based on common available free assets:

| Asset Type | Expected File | Use For |
|------------|---------------|---------|
| **Set 1** | `staunton_plastic.obj` | Tournament standard |
| **Set 2** | `wood_classic.obj` | Traditional games |
| **Set 3** | `minimalist_chess.fbx` | Modern variety |
| **Board 1** | `walnut_4k_textures/` | Dark wood style |
| **Board 2** | `maple_green_textures/` | Tournament style |
| **Board 3** | `mahogany_textures/` | Classic rich |

### Step 4: Download & Organize

**Create this structure:**
```bash
cd /home/node/.openclaw/workspace/data_generation/assets/

# Create folders
mkdir -p pieces/{set_01_staunton,set_02_wood,set_03_modern}
mkdir -p boards/{walnut_4k,maple_4k,mahogany_4k}
mkdir -p hdri/{office,tournament,home,studio,outdoor}
```

**Download checklist:**
- [ ] Pieces Set 1: 12 files (6 white, 6 black)
- [ ] Pieces Set 2: 12 files
- [ ] Pieces Set 3: 12 files (optional)
- [ ] Board 1: mesh + 3 texture maps
- [ ] Board 2: mesh + 3 texture maps
- [ ] Board 3: mesh + 3 texture maps
- [ ] HDRI 1-5: .hdr files

### Step 5: License Documentation

Create `assets/LICENSES.md`:
```markdown
# Asset License Documentation

## Chess Piece Sets

### Set 1: [Name from website]
- Source: [Sketchfab/CGTrader/etc]
- Model Name: [Exact title]
- Author: [Name]
- License: [CC BY 4.0 / CC0 / etc]
- URL: [Direct link]
- Download Date: [Today's date]
- Notes: Any modifications made

### Set 2: ...

## Textures

### Wood Textures
- Source: Polyhaven
- Type: CC0 (Public Domain)
- No attribution required
- URLs: [list]

## HDRI Environments

### office_morning.hdr
- Source: Polyhaven
- License: CC0
- URL: [direct link]
```

## Alternative: If Direct Download Fails

**Create Placeholder Assets:**
We can create simple procedural chess pieces using Blender's built-in tools:
- Cylinders + cones for pieces
- Wood textures procedurally generated
- Gets us started while sourcing better assets

**Tell me:**
- "Start with procedural" → I create basic pieces in Blender now
- "I will download manually" → You collect assets, I organize
- "Help me evaluate what I have" → You upload, I check compatibility

## Validation Checklist

After downloading, verify each asset:

**Pieces:**
- [ ] Opens in Blender without errors
- [ ] All 12 types present (6 white, 6 black)
- [ ] Scale roughly correct (king ~9cm)
- [ ] Materials visible
- [ ] No missing textures

**Boards:**
- [ ] Square board (not rectangular unless intended)
- [ ] UV mapped correctly
- [ ] Textures tile seamlessly
- [ ] Scale: ~56cm across

**HDRIs:**
- [ ] 360° panoramic
- [ ] Not mirrored/reversed
- [ ] Reasonable brightness

## Expected Challenges

| Problem | Solution |
|---------|----------|
| Models too detailed (100K+ polys) | Use decimate modifier in Blender |
| Wrong scale | Scale in Blender, apply transforms |
| Missing textures | Create simple PBR materials |
| Wrong format | Import → Export as FBX from Blender |
| License unclear | Skip it, find CC-licensed alternative |

## Timeline Estimate

- Finding + downloading: 30-60 minutes
- Importing + validating: 30-45 minutes
- Organizing + documenting: 15 minutes

**Total: ~2 hours to get asset library ready**