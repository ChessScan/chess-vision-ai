# Flutter Chess Vision App

A Flutter MVP for automatic chess board detection and game recording.

## Features

- **Recording Mode**: Record chess games with camera
- **Live Detection View**: Large chess board display with small camera preview
- **Analysis Mode**: Review recordings with move navigation
- **Mock Detection**: Simulates chess moves for testing

## Screenshots

*(Screenshots will be added once the app is running)*

## Development Setup

### Prerequisites

1. Install Docker and Docker Compose
2. Clone this repository

### Running with Docker

```bash
# Build the development container
docker build -t chess-vision-dev .

# Run the development container
docker run -it --rm \
  -v $(pwd):/app \
  -p 8080:8080 \
  -p 5037:5037 \
  chess-vision-dev

# Inside container - get dependencies
flutter pub get

# Run on web (for development)
flutter run -d web-server --web-port 8080
```

### Local Development (without Docker)

1. Install Flutter SDK (3.0.0+)
2. Install Android Studio + Android SDK (for Android development)
3. Install Xcode (for iOS development - macOS only)

```bash
# Get dependencies
flutter pub get

# Run on connected device
flutter run

# Or specify device
flutter devices
flutter run -d <device_id>
```

## Project Structure

```
lib/
├── main.dart              # App entry point
├── screens/
│   ├── home_screen.dart       # Recording list
│   ├── recording_screen.dart  # Camera + chess board
│   └── analysis_screen.dart   # Replay + analysis
├── widgets/
│   ├── chess_board.dart       # Chess board widget
│   ├── recording_list.dart    # Recording list item
│   └── move_history.dart      # Move history display
├── models/
│   ├── chess_position.dart   # Chess position model
│   ├── chess_move.dart       # Move model
│   └── recording.dart        # Recording model
└── services/
    ├── camera_service.dart     # Camera operations
    ├── storage_service.dart    # File persistence
    └── mock_detection.dart     # Mock CV detection
```

## Dependencies

- `camera`: Camera access and video recording
- `video_player`: Video playback in analysis mode
- `path_provider`: File system access
- `permission_handler`: Runtime permissions
- `provider`: State management
- `intl`: Date/number formatting

## Usage

1. **Home Screen**: View existing recordings or start a new one
2. **Recording Mode**: 
   - Place phone next to chess board
   - Tap record button to start
   - Watch the chess board update as "moves" are detected
   - Tap pause to stop auto-detection
   - Tap stop to save recording
3. **Analysis Mode**:
   - Select a recording from home screen
   - Navigate through moves using timeline controls
   - View position and FEN notation
   - Video playback (if recording exists)

## Mock Detection

The MVP uses a mock detection service that generates random but valid chess moves. This simulates the CV detection for UI/UX testing before the actual AI model is integrated.

To replace with real detection:
1. Implement `DetectionService` interface
2. Replace `MockDetectionService` with real implementation
3. Connect to TFLite model

## Known Limitations

- Mock detection generates random moves (not from actual video)
- Video playback in analysis mode is basic
- No actual chess logic validation
- No user authentication

## Roadmap

- [x] Basic UI structure
- [x] Camera recording
- [x] Mock detection service
- [x] Analysis mode
- [ ] Integrate TFLite model
- [ ] Real board detection from video
- [ ] PGN export
- [ ] Settings page
- [ ] User preferences

## License

MIT
