# App Dev Agent Specification
**Agent:** codex-app  
**Task:** Complete Flutter app  
**Duration:** ~3 hours

---

## OBJECTIVE
Build complete Flutter mobile app with:
1. Home screen - Game history + start new game
2. Live Detection screen - Camera + real-time board detection
3. Analysis screen - Game review + PGN export

---

## REPOSITORY

**Target:** `ChessScan/chess-vision-app`
**Branch:** `feature/complete-ui`
**Workspace:** `/workspace/agents/app-agent/`

---

## DELIVERABLES

### Screen 1: Home (COMPLETE - enhance)
**File:** `lib/screens/home_screen.dart`

**Enhancements:**
- Add game import from PGN
- Add settings drawer
- Add tutorial overlay

### Screen 2: Live Detection (COMPLETE - enhance)
**File:** `lib/screens/live_detection_screen.dart`

**Enhancements:**
- Connect to real camera preview
- Integrate with CV Pipeline Agent
- Show real FEN from detection
- Add move confirmation UI

### Screen 3: Analysis (REQUIRED)
**File:** `lib/screens/analysis_screen.dart`

**Features:**
- Display detected game moves
- Chess board with move navigation
- PGN notation display
- Export PGN/FEN to clipboard/file
- Share to Lichess/Chess.com
- Engine evaluation (Stockfish integration)

---

## UI SPECIFICATIONS

**Theme:**
- Primary: #739552 (chess.com green)
- Secondary: #1a1a2e (dark blue)
- Accent: #4CAF50 (success)
- Background: Dark mode default

**Typography:**
- Primary: SF Pro / Roboto
- Chess notation: Monospace

**Board:**
- Square colors: #EBECD0 / #739552
- Pieces: chess.com Neo style (SVG)
- Drag-drop enabled

**Animations:**
- Piece movement: 200ms ease
- Screen transitions: 300ms slide

---

## CORE WIDGETS

### ChessBoardWidget
**Status:** Complete (in repo)
**Enhancements needed:**
- Connect to real game state
- Show last move indicator
- Support move takeback

### GameHistoryList
**Required:**
- Scrollable move list
- Tap to jump to position
- Current move highlight

### AnalysisController
**Required:**
- Navigate moves (prev/next/first/last)
- Flip board orientation
- Show evaluation bar
- Engine depth indicator

### ExportDialog
**Required:**
- PGN format export
- FEN format export
- Share intent integration
- Copy to clipboard

---

## STATE MANAGEMENT

**Use Provider pattern:**
```dart
class GameState extends ChangeNotifier {
  ChessGame currentGame;
  List<String> moveHistory;
  String currentFen;
  int currentMoveIndex;
  
  void addMove(String move);
  void goToMove(int index);
  void exportPGN();
}
```

---

## INTEGRATION POINTS

**Consumes:**
- Models from Train Agent (via CV Agent)
- Camera feed (device)
- Storage: SQLite for game history

**Produces:**
- APK for testing
- Complete Flutter codebase

---

## DEPENDENCIES

```yaml
dependencies:
  flutter:
    sdk: flutter
  chess: ^0.7.0
  provider: ^6.0.5
  camera: ^0.10.5
  path_provider: ^2.0.15
  share_plus: ^7.0.2
  sqflite: ^2.3.0
  flutter_svg: ^2.0.7
```

---

## CHECKPOINTS

- Analysis screen scaffold created
- Chess board navigation working
- PGN display implemented
- Export functionality complete
- Integration with Live Detection
- Full app test
- Status: complete

**On completion:**
- Push to GitHub
- Build APK for CEO review
- Update status file
