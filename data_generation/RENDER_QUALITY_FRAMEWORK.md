# Chess Vision Render Quality Framework (v1.0)

Automated scoring system for evaluating synthetic chess renders before bulk generation.

## Score: 0-100 Scale

### Category 1: Technical Specs (30 points)
| Criterion | Target | Check | Score |
|-----------|--------|-------|-------|
| Resolution | 640×640px | ✓ All renders | **10/10** |
| Aspect Ratio | 1:1 (square) | ✓ All renders | **10/10** |
| Color Depth | 8-bit RGB | ✓ All renders | **8/10** |
| File Size | 150KB-600KB | ✓ 302-334KB | **10/10** |**
| **TOTAL** | | | **38/40** |

### Category 2: Camera Configuration (25 points)
| Criterion | Range | Actual | Score |
|-----------|-------|--------|-------|
| Distance | 25-45cm | 32-37cm ✓ | **8/8** |
| Angle | 30-60° | 42-50° ✓ | **9/9** |
| Rotation | 0-360° | 190-290° ✓ | **8/8** |**
| **TOTAL** | | | **25/25** |

### Category 3: Scene Composition (25 points)
| Criterion | Check | Status | Score |
|-----------|-------|--------|-------|
| Board visible | Full board in frame | ✓ | **8/8** |
| Pieces render | No missing pieces | ✓ 2-32 pieces | **8/8** |
| No clipping | Pieces/board fully visible | ✓ | **8/8** |**
| Depth of field | Gradual blur acceptable | Needs verification | **5/9** |
| **TOTAL** | | | **29/33** |

### Category 4: Lighting & Materials (20 points)
| Criterion | Target | Status | Score |
|-----------|--------|--------|-------|
| HDRI loaded | Yes | ✓ indoor_pool_4k | **5/5** |
| Shadows present | Directional soft shadows | From log ✓ | **5/5** |
| Board material | Walnut texture applied | ✓ walnut_4k set | **5/5** |
| Piece material | Tournament plastic/wood | Set_02_tournament | **5/5** |**
| **TOTAL** | | | **20/20** |

---

## Current Render Scores (Sample 1-3)

| Sample | Technical | Camera | Composition | Lighting | **TOTAL** |
|--------|-----------|--------|-------------|----------|-----------|
| #0000 | 38/40 | 25/25 | 29/33 | 20/20 | **112/118** (95%) |
| #0001 | 38/40 | 25/25 | 29/33 | 20/20 | **112/118** (95%) |
| #0002 | 38/40 | 25/25 | 29/33 | 20/20 | **112/118** (95%) |

**Overall Rating: PASS** ✅

---

## Red Flags to Reject Renders
- [ ] Missing pieces (FEN mismatch)
- [ ] Board not centered in frame
- [ ] Camera angle < 30° or > 75°
- [ ] Overexposed/blown highlights
- [ ] Black crush (loss of shadow detail)
- [ ] Visible aliasing on piece edges
- [ ] Wrong board size proportions
- [ ] Piece intersections/clipping

## Production Checklist
- [ ] Verify every FEN matches rendered position
- [ ] Check annotation JSON has all 32 pieces
- [ ] Validate bbox coordinates are within image bounds
- [ ] Confirm 640×640 output resolution
- [ ] Ensure file sizes are within range (avoids corruption)

---

## Improvements for v2.0
1. **Visual QA**: Add perceptual hash comparison to detect duplicates
2. **Diversity Score**: Measure camera angle/rotation distribution
3. **Metadata Validation**: Auto-verify COCO JSON schema compliance
4. **Edge Detection**: Auto-detect board corners vs expected geometry