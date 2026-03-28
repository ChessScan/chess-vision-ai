import 'dart:async';
import 'package:camera/camera.dart';
import 'package:flutter/material.dart';

class CameraService {
  CameraController? _controller;
  bool _isRecording = false;
  String? _currentVideoPath;
  
  CameraController? get controller => _controller;
  bool get isRecording => _isRecording;
  bool get isInitialized => _controller?.value.isInitialized ?? false;

  List<CameraDescription> _cameras = [];
  int _selectedCameraIndex = 0;

  Future<void> initialize() async {
    _cameras = await availableCameras();
    if (_cameras.isEmpty) {
      throw Exception('No cameras available');
    }
    
    // Prefer back camera if available
    _selectedCameraIndex = _cameras.indexWhere(
      (c) => c.lensDirection == CameraLensDirection.back,
    );
    if (_selectedCameraIndex == -1) _selectedCameraIndex = 0;
    
    await _initializeController();
  }

  Future<void> _initializeController() async {
    if (_controller != null) {
      await _controller!.dispose();
    }
    
    _controller = CameraController(
      _cameras[_selectedCameraIndex],
      ResolutionPreset.medium,
      enableAudio: true,
    );
    
    await _controller!.initialize();
  }

  Future<void> switchCamera() async {
    if (_cameras.length < 2) return;
    
    _selectedCameraIndex = (_selectedCameraIndex + 1) % _cameras.length;
    await _initializeController();
  }

  Future<String?> startRecording(String videoPath) async {
    if (_controller == null || !_controller!.value.isInitialized) {
      throw Exception('Camera not initialized');
    }
    
    if (_isRecording) {
      throw Exception('Already recording');
    }
    
    await _controller!.startVideoRecording();
    _isRecording = true;
    _currentVideoPath = videoPath;
    
    return videoPath;
  }

  Future<String?> stopRecording() async {
    if (!_isRecording || _controller == null) {
      return null;
    }
    
    final XFile videoFile = await _controller!.stopVideoRecording();
    _isRecording = false;
    
    return videoFile.path;
  }

  Future<XFile?> takePicture() async {
    if (_controller == null || !_controller!.value.isInitialized) {
      throw Exception('Camera not initialized');
    }
    
    return await _controller!.takePicture();
  }

  Future<void> dispose() async {
    if (_isRecording) {
      await stopRecording();
    }
    await _controller?.dispose();
    _controller = null;
  }

  Widget buildPreview() {
    if (_controller == null || !_controller!.value.isInitialized) {
      return Container(
        color: Colors.black,
        child: const Center(
          child: CircularProgressIndicator(),
        ),
      );
    }
    
    return CameraPreview(_controller!);
  }

  Future<CameraDescription?> get currentCamera async {
    if (_cameras.isEmpty) return null;
    return _cameras[_selectedCameraIndex];
  }

  Future<void> setFlashMode(FlashMode mode) async {
    await _controller?.setFlashMode(mode);
  }

  Future<void> setZoom(double zoom) async {
    await _controller?.setZoomLevel(zoom);
  }

  double getAspectRatio() {
    if (_controller == null || !_controller!.value.isInitialized) {
      return 16 / 9;
    }
    return _controller!.value.aspectRatio;
  }
}
