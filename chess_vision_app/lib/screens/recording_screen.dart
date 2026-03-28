import 'dart:async';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:provider/provider.dart';

import '../models/chess_piece.dart';
import '../models/chess_position.dart';
import '../services/camera_service.dart';
import '../services/storage_service.dart';
import '../services/mock_detection_service.dart';
import '../widgets/chess_board.dart';

class RecordingScreen extends StatefulWidget {
  const RecordingScreen({super.key});

  @override
  State<RecordingScreen> createState() => _RecordingScreenState();
}

class _RecordingScreenState extends State<RecordingScreen> with WidgetsBindingObserver {
  final CameraService _cameraService = CameraService();
  final MockDetectionService _detectionService = MockDetectionService();
  
  bool _isInitializing = true;
  bool _hasError = false;
  String _errorMessage = '';
  bool _isRecording = false;
  DateTime? _recordingStartTime;
  Timer? _recordingTimer;
  Duration _recordingDuration = Duration.zero;
  
  ChessPosition _currentPosition = ChessPosition.initial();
  bool _isPaused = false;
  
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _initializeCamera();
    _detectionService.startAutoDetection();
    _detectionService.positionStream.listen((position) {
      if (mounted) {
        setState(() => _currentPosition = position);
      }
    });
  }

  Future<void> _initializeCamera() async {
    try {
      // Request permissions
      final cameraStatus = await Permission.camera.request();
      final micStatus = await Permission.microphone.request();
      
      if (!cameraStatus.isGranted || !micStatus.isGranted) {
        setState(() {
          _hasError = true;
          _errorMessage = 'Camera and microphone permissions required';
          _isInitializing = false;
        });
        return;
      }

      await _cameraService.initialize();
      
      if (mounted) {
        setState(() => _isInitializing = false);
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _hasError = true;
          _errorMessage = 'Error initializing camera: $e';
          _isInitializing = false;
        });
      }
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _recordingTimer?.cancel();
    _cameraService.dispose();
    _detectionService.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.inactive) {
      _cameraService.dispose();
    } else if (state == AppLifecycleState.resumed) {
      _initializeCamera();
    }
  }

  Future<void> _toggleRecording() async {
    if (_isRecording) {
      await _stopRecording();
    } else {
      await _startRecording();
    }
  }

  Future<void> _startRecording() async {
    try {
      final storage = Provider.of<StorageService>(context, listen: false);
      final videoPath = await storage.getNewVideoPath();
      
      await _cameraService.startRecording(videoPath);
      
      setState(() {
        _isRecording = true;
        _recordingStartTime = DateTime.now();
        _recordingDuration = Duration.zero;
      });
      
      _recordingTimer = Timer.periodic(
        const Duration(seconds: 1),
        (_) => setState(() {
          if (_recordingStartTime != null) {
            _recordingDuration = DateTime.now().difference(_recordingStartTime!);
          }
        }),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error starting recording: $e')),
      );
    }
  }

  Future<void> _stopRecording() async {
    _recordingTimer?.cancel();
    
    try {
      final videoPath = await _cameraService.stopRecording();
      
      if (videoPath != null && _recordingStartTime != null) {
        final storage = Provider.of<StorageService>(context, listen: false);
        await storage.saveRecording(
          videoPath: videoPath,
          duration: _recordingDuration,
          name: 'Recording ${_recordingStartTime!.toLocal()}'.split('.').first,
        );
        
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Recording saved')),
          );
          Navigator.pop(context);
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error saving recording: $e')),
        );
      }
    }
    
    setState(() {
      _isRecording = false;
      _recordingStartTime = null;
      _recordingDuration = Duration.zero;
    });
  }

  void _togglePause() {
    setState(() {
      _isPaused = !_isPaused;
      _detectionService.togglePause();
    });
  }

  void _resetBoard() {
    _detectionService.reset();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Recording Mode'),
        actions: [
          IconButton(
            icon: Icon(_isPaused ? Icons.play_arrow : Icons.pause),
            onPressed: _togglePause,
            tooltip: _isPaused ? 'Resume' : 'Pause',
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _resetBoard,
            tooltip: 'Reset board',
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isInitializing) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: const [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Initializing camera...'),
          ],
        ),
      );
    }

    if (_hasError) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: Colors.red),
            const SizedBox(height: 16),
            Text(
              _errorMessage,
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.red),
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () {
                setState(() {
                  _isInitializing = true;
                  _hasError = false;
                });
                _initializeCamera();
              },
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    return Column(
      children: [
        // Status bar
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          color: _isRecording ? Colors.red.shade900 : Colors.grey.shade900,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  if (_isRecording) ...[
                    Container(
                      width: 12,
                      height: 12,
                      decoration: const BoxDecoration(
                        color: Colors.red,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 8),
                  ],
                  Text(
                    _isRecording ? 'REC ' : '',
                    style: const TextStyle(
                      color: Colors.red,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Text(
                    _formatDuration(_recordingDuration),
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                ],
              ),
              if (_isPaused)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: Colors.orange,
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: const Text(
                    'PAUSED',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
            ],
          ),
        ),
        
        // Main content: Chess board (large) + Camera (small)
        Expanded(
          child: Row(
            children: [
              // Chess board (main focus)
              Expanded(
                flex: 3,
                child: Container(
                  color: Colors.black,
                  child: Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        ChessBoard(
                          position: _currentPosition,
                          size: MediaQuery.of(context).size.width * 0.6,
                        ),
                        const SizedBox(height: 16),
                        if (_currentPosition.lastMoveNotation != null)
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 16,
                              vertical: 8,
                            ),
                            decoration: BoxDecoration(
                              color: Colors.deepPurple.shade700,
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: Text(
                              'Last move: ${_currentPosition.lastMoveNotation}',
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
              ),
              
              // Camera preview (side panel)
              Container(
                width: 150,
                color: Colors.grey.shade900,
                child: Column(
                  children: [
                    // Camera preview
                    AspectRatio(
                      aspectRatio: _cameraService.getAspectRatio(),
                      child: Container(
                        color: Colors.black,
                        child: _cameraService.controller != null
                            ? CameraPreview(_cameraService.controller!)
                            : const Center(
                                child: CircularProgressIndicator(),
                              ),
                      ),
                    ),
                    
                    // Camera controls
                    Expanded(
                      child: SingleChildScrollView(
                        child: Padding(
                          padding: const EdgeInsets.all(8),
                          child: Column(
                            children: [
                              IconButton(
                                icon: const Icon(Icons.flip_camera_ios),
                                onPressed: () => _cameraService.switchCamera(),
                                tooltip: 'Switch camera',
                              ),
                              const SizedBox(height: 8),
                              IconButton(
                                icon: Icon(_isRecording ? Icons.stop : Icons.fiber_manual_record),
                                onPressed: _toggleRecording,
                                color: _isRecording ? Colors.red : Colors.green,
                                iconSize: 48,
                                tooltip: _isRecording ? 'Stop' : 'Record',
                              ),
                              const SizedBox(height: 16),
                              
                              // Move info
                              Container(
                                padding: const EdgeInsets.all(8),
                                decoration: BoxDecoration(
                                  color: Colors.grey.shade800,
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Column(
                                  children: [
                                    Text(
                                      'Move ${_currentPosition.moveNumber}',
                                      style: const TextStyle(
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      _currentPosition.turn == PieceColor.white ? 'White' : 'Black',
                                      style: TextStyle(
                                        color: _currentPosition.turn == PieceColor.white
                                            ? Colors.white
                                            : Colors.grey.shade400,
                                        fontSize: 12,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
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

  String _formatDuration(Duration duration) {
    final minutes = duration.inMinutes.toString().padLeft(2, '0');
    final seconds = (duration.inSeconds % 60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
  }
}
