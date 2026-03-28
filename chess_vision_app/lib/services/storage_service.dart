import 'dart:convert';
import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as path;

import '../models/recording.dart';

class StorageService {
  static const String _recordingsDir = 'recordings';
  static const String _metadataFile = 'recordings.json';
  
  Directory? _appDir;
  List<Recording> _recordings = [];

  Future<Directory> get _appDirectory async {
    _appDir ??= await getApplicationDocumentsDirectory();
    return _appDir!;
  }

  Future<Directory> get _recordingsDirectory async {
    final appDir = await _appDirectory;
    final recordingsDir = Directory(path.join(appDir.path, _recordingsDir));
    if (!await recordingsDir.exists()) {
      await recordingsDir.create(recursive: true);
    }
    return recordingsDir;
  }

  Future<File> get _metadataFilePath async {
    final appDir = await _appDirectory;
    return File(path.join(appDir.path, _metadataFile));
  }

  Future<void> _loadRecordings() async {
    try {
      final file = await _metadataFilePath;
      if (await file.exists()) {
        final content = await file.readAsString();
        final List<dynamic> jsonList = jsonDecode(content);
        _recordings = jsonList.map((json) => Recording.fromJson(json)).toList();
      }
    } catch (e) {
      _recordings = [];
    }
  }

  Future<void> _saveRecordings() async {
    final file = await _metadataFilePath;
    final jsonList = _recordings.map((r) => r.toJson()).toList();
    await file.writeAsString(jsonEncode(jsonList));
  }

  Future<List<Recording>> getRecordings() async {
    await _loadRecordings();
    return List.unmodifiable(_recordings..sort((a, b) => 
      b.createdAt.compareTo(a.createdAt)));
  }

  Future<String> getNewVideoPath() async {
    final recordingsDir = await _recordingsDirectory;
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    final id = 'recording_$timestamp';
    return path.join(recordingsDir.path, '$id.mp4');
  }

  Future<Recording> saveRecording({
    required String videoPath,
    required Duration duration,
    String? name,
  }) async {
    await _loadRecordings();
    
    final id = DateTime.now().millisecondsSinceEpoch.toString();
    final recording = Recording(
      id: id,
      videoPath: videoPath,
      createdAt: DateTime.now(),
      duration: duration,
      name: name,
    );
    
    _recordings.add(recording);
    await _saveRecordings();
    
    return recording;
  }

  Future<void> updateRecording(Recording recording) async {
    await _loadRecordings();
    final index = _recordings.indexWhere((r) => r.id == recording.id);
    if (index != -1) {
      _recordings[index] = recording;
      await _saveRecordings();
    }
  }

  Future<void> deleteRecording(String id) async {
    await _loadRecordings();
    final recording = _recordings.firstWhere((r) => r.id == id);
    
    // Delete video file
    final videoFile = File(recording.videoPath);
    if (await videoFile.exists()) {
      await videoFile.delete();
    }
    
    _recordings.removeWhere((r) => r.id == id);
    await _saveRecordings();
  }

  Future<Recording?> getRecording(String id) async {
    await _loadRecordings();
    try {
      return _recordings.firstWhere((r) => r.id == id);
    } catch (e) {
      return null;
    }
  }

  Future<void> clearAllRecordings() async {
    final recordingsDir = await _recordingsDirectory;
    if (await recordingsDir.exists()) {
      await recordingsDir.delete(recursive: true);
    }
    
    final metadataFile = await _metadataFilePath;
    if (await metadataFile.exists()) {
      await metadataFile.delete();
    }
    
    _recordings = [];
  }
}
