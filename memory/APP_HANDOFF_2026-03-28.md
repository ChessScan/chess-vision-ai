# Chess Vision App - Development Handoff

## Current Status
UI mockups completed with chess.com Neo piece style. Ready for Flutter implementation.

## Screens Completed

### 1. Home Screen (`home_chesscom_final.png`)
- **Layout:** Portrait (390x844)
- **Header:** Purple gradient (#667eea → #764ba2) with "Chess Vision" title + settings gear
- **Stats Card:** 3 columns - 12 Recordings | 45m Total Time | 342 Moves
- **Recording List:** 4 cards with thumbnail placeholder, title, duration, move count
- **FAB:** "New Recording" button bottom right
- **Theme:** Material Design 3 Dark, purple accents

### 2. Live Detection Screen (`live_final_solid.png`)
- **Layout:** Portrait with split view
- **Left 70%:** Chess board (280x280) showing current position
- **Right 30%:** Camera preview + move counter + controls
- **Move Display:** Shows notation "1. e4 e5" with "Last detected move" label
- **Controls:** PAUSE, FLIP, STOP buttons
- **Bottom Info:** "Detection active" + Settings button
- **Pieces:** chess.com Neo set with **SOLID WHITE** pieces (not wireframes)
- **Board Colors:** Light #f0d9b5 | Dark #b58863

### 3. Analysis Screen (`analysis_chesscom_final.png`)
- **Layout:** Landscape (844x390)
- **Left:** Video player (280x340) with timeline scrubber
- **Center:** Chess board (220x220) + move notation
- **Right Sidebar:**
  - Navigation buttons (|← ← → →|)
  - FEN display with Copy button
  - Recording info (Duration, Date, Moves, Detected)
  - Export buttons (PGN, FEN)
- **Theme:** Same as Home/Live screens

## Chess Pieces
- **Source:** chess.com Neo piece set (150px PNGs)
- **Files:** `wr.png`, `wn.png`, `wb.png`, `wq.png`, `wk.png`, `wp.png`, `br.png`, `bn.png`, `bb.png`, `bq.png`, `bk.png`, `bp.png`
- **Location:** `/home/node/.openclaw/workspace/chess_pieces/`
- **White Pieces:** Solid white (tinted versions with `_solid` suffix)
- **Black Pieces:** Standard black with colored wood texture

## Colors
- **Background:** #1a1a2e (dark purple/black)
- **Header Gradient:** #667eea → #764ba2
- **Card Background:** #2d3748
- **Accent (Purple):** #a78bfa
- **Text Primary:** #ffffff
- **Text Secondary:** #9ca3af
- **Chess Board Light:** #f0d9b5
- **Chess Board Dark:** #b58863
- **Danger/Stop:** #ef4444

## Technical Stack
- **Framework:** Flutter 3.19+
- **Design:** Material Design 3, dark theme
- **State Management:** Provider (already in existing code)
- **Camera:** camera plugin
- **Video:** video_player plugin
- **Chess Logic:** chess.dart package (recommended)

## Existing Code Location
`/home/node/.openclaw/workspace/chess_vision_app/`
- `lib/screens/home_screen.dart` (needs pieces)
- `lib/screens/analysis_screen.dart` (needs pieces)
- `lib/screens/recording_screen.dart` (create)
- `lib/screens/live_detection_screen.dart` (create)
- `lib/widgets/chess_board.dart` (needs implementation with chess.com pieces)

## Flutter Widget Structure
```
ChessBoardWidget:
  - size: double (board dimension)
  - position: ChessPosition (FEN or piece array)
  - showCoordinates: bool
  - onSquareTap: callback (optional)
  
LiveDetectionScreen:
  - Camera preview (small, right side)
  - ChessBoardWidget (large, left side)
  - Move history display
  - Control buttons (Pause, Flip, Stop)
  
AnalysisScreen:
  - Video player
  - ChessBoardWidget
  - Move navigation controls
  - FEN export
```

## Next Steps
1. Integrate chess.com piece images into Flutter assets
2. Create ChessBoardWidget with proper piece rendering
3. Implement LiveDetectionScreen with camera integration
4. Complete AnalysisScreen with video sync
5. Test on device and capture screenshots

## Assets Needed
- All 12 chess piece PNGs (chess_pieces/ directory)
- Loading into Flutter ImageAssets
- Proper scaling (pieces should be ~80% of square size)

## Notes
- Solid white pieces were created by tinting the original chess.com Neo white pieces
- Board squares have no border radius inside the board (only outer corners)
- Pieces should be slightly smaller than squares (padding ~2-4px)
- Text overflow fixed: dates use "28 Mar 2026" format instead of "Mar 28, 2026"

---
**Handed off from:** jan10010 (UI/UX designer)  
**To:** App Development Agent  
**Date:** 2026-03-28