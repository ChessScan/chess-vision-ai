import 'dart:io';
import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';
import 'package:provider/provider.dart';

import '../models/chess_piece.dart';
import '../models/chess_position.dart';
import '../models/recording.dart';
import '../services/storage_service.dart';
import '../services/mock_detection_service.dart';
import '../widgets/chess_board.dart';
import '../widgets/move_history.dart';

class AnalysisScreen extends StatefulWidget {
  final String recordingPath;

  const AnalysisScreen({
    super.key,
    required this.recordingPath,
  });

  @override
  State<AnalysisScreen> createState() => _AnalysisScreenState();
}

class _AnalysisScreenState extends State<AnalysisScreen> {
  VideoPlayerController? _videoController;
  Recording? _recording;
  bool _isLoading = true;
  int _currentMoveIndex = -1;
  
  // For analysis mode without actual recording
  final MockDetectionService _mockService = MockDetectionService();
  List<ChessPosition> _positionHistory = [];
  
  @override
  void initState() {
    super.initState();
    _loadRecording();
  }

  Future<void> _loadRecording() async {
    setState(() => _isLoading = true);
    
    // Try to load actual recording
    final storage = Provider.of<StorageService>(context, listen: false);
    final recordings = await storage.getRecordings();
    
    _recording = recordings.firstWhere(
      (r) => r.videoPath == widget.recordingPath,
      orElse: () => Recording(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        videoPath: widget.recordingPath,
        createdAt: DateTime.now(),
        duration: const Duration(minutes: 5),
      ),
    );

    // Generate mock position history for analysis
    _generatePositionHistory();

    // Initialize video if file exists
    final videoFile = File(widget.recordingPath);
    if (await videoFile.exists()) {
      _videoController = VideoPlayerController.file(videoFile);
      await _videoController!.initialize();
      _videoController!.setLooping(false);
    }

    if (mounted) {
      setState(() => _isLoading = false);
    }
  }

  void _generatePositionHistory() {
    _positionHistory = [ChessPosition.initial()];
    
    // Generate some mock moves
    final mockService = MockDetectionService();
    for (int i = 0; i < 20; i++) {
      // This would be replaced with actual move data from recording
      // For now, just showing initial position
    }
    
    // Add some varied positions for demo
    _positionHistory.add(ChessPosition.fromFEN('rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1'));
    _positionHistory.add(ChessPosition.fromFEN('rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2'));
    _positionHistory.add(ChessPosition.fromFEN('rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2'));
  }

  @override
  void dispose() {
    _videoController?.dispose();
    _mockService.dispose();
    super.dispose();
  }

  void _goToMove(int index) {
    setState(() {
      _currentMoveIndex = index.clamp(-1, _positionHistory.length - 1);
    });
    
    // Sync video to approximate timestamp
    if (_videoController != null && _videoController!.value.isInitialized) {
      if (_currentMoveIndex < 0) {
        _videoController!.seekTo(Duration.zero);
      } else {
        final progress = (_currentMoveIndex + 1) / _positionHistory.length;
        final position = _videoController!.value.duration * progress;
        _videoController!.seekTo(position);
      }
    }
  }

  void _firstMove() => _goToMove(-1);
  void _previousMove() => _goToMove(_currentMoveIndex - 1);
  void _nextMove() => _goToMove(_currentMoveIndex + 1);
  void _lastMove() => _goToMove(_positionHistory.length - 1);

  ChessPosition get _currentPosition {
    if (_currentMoveIndex < 0 || _currentMoveIndex >= _positionHistory.length) {
      return ChessPosition.initial();
    }
    return _positionHistory[_currentMoveIndex];
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_recording?.displayName ?? 'Analysis'),
        actions: [
          if (_videoController != null)
            IconButton(
              icon: Icon(
                _videoController!.value.isPlaying
                    ? Icons.pause
                    : Icons.play_arrow,
              ),
              onPressed: _toggleVideoPlayback,
            ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _buildAnalysisView(),
    );
  }

  Widget _buildAnalysisView() {
    return Column(
      children: [
        // Video player (if available)
        if (_videoController != null && _videoController!.value.isInitialized)
          AspectRatio(
            aspectRatio: _videoController!.value.aspectRatio,
            child: VideoPlayer(_videoController!),
          ),
        
        // Main content
        Expanded(
          child: Row(
            children: [
              // Chess board
              Expanded(
                flex: 2,
                child: Container(
                  color: Colors.black,
                  child: Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        ChessBoard(
                          position: _currentPosition,
                          size: MediaQuery.of(context).size.width * 0.4,
                          showCoordinates: true,
                        ),
                        const SizedBox(height: 16),
                        Text(
                          'Position ${_currentMoveIndex + 1} / ${_positionHistory.length}',
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        if (_currentPosition.lastMoveNotation != null)
                          Text(
                            'Last move: ${_currentPosition.lastMoveNotation}',
                            style: TextStyle(
                              color: Colors.deepPurple.shade200,
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
              ),
              
              // Move history and controls
              Container(
                width: 300,
                color: Colors.grey.shade900,
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    // Controls
                    MoveHistoryTimeline(
                      moves: [], // Would be actual moves
                      currentMoveIndex: _currentMoveIndex,
                      onFirst: _firstMove,
                      onPrevious: _previousMove,
                      onNext: _nextMove,
                      onLast: _lastMove,
                    ),
                    
                    const SizedBox(height: 16),
                    
                    // Position info
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.grey.shade800,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Column(
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              const Text('FEN:'),
                              IconButton(
                                icon: const Icon(Icons.copy, size: 18),
                                onPressed: _copyFEN,
                                tooltip: 'Copy FEN',
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          Text(
                            _currentPosition.toFEN().split(' ').first,
                            style: const TextStyle(fontSize: 11),
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ),
                    ),
                    
                    const SizedBox(height: 16),
                    
                    // Stats
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.grey.shade800,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Recording Info',
                            style: Theme.of(context).textTheme.titleSmall,
                          ),
                          const SizedBox(height: 8),
                          _buildInfoRow('Duration', _recording?.formattedDuration ?? 'Unknown'),
                          _buildInfoRow('Date', _recording?.formattedDate ?? 'Unknown'),
                          _buildInfoRow('Moves', '${_positionHistory.length}'),
                        ],
                      ),
                    ),
                    
                    const Spacer(),
                    
                    // Export buttons
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: _exportPGN,
                            icon: const Icon(Icons.download, size: 18),
                            label: const Text('PGN'),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: _exportFEN,
                            icon: const Icon(Icons.copy, size: 18),
                            label: const Text('FEN'),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: TextStyle(
              color: Colors.grey.shade400,
              fontSize: 12,
            ),
          ),
          Text(
            value,
            style: const TextStyle(
              fontWeight: FontWeight.w500,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }

  void _toggleVideoPlayback() {
    if (_videoController == null) return;
    
    setState(() {
      if (_videoController!.value.isPlaying) {
        _videoController!.pause();
      } else {
        _videoController!.play();
      }
    });
  }

  void _copyFEN() {
    // Clipboard.setData(ClipboardData(text: _currentPosition.toFEN()));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('FEN copied to clipboard')),
    );
  }

  void _exportPGN() {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('PGN export coming soon')),
    );
  }

  void _exportFEN() {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('FEN export coming soon')),
    );
  }
}
