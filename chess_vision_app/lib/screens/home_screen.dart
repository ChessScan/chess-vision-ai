import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/recording.dart';
import '../services/storage_service.dart';
import '../widgets/recording_list.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  List<Recording> _recordings = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadRecordings();
  }

  Future<void> _loadRecordings() async {
    setState(() => _isLoading = true);
    final storage = Provider.of<StorageService>(context, listen: false);
    final recordings = await storage.getRecordings();
    setState(() {
      _recordings = recordings;
      _isLoading = false;
    });
  }

  void _navigateToRecording() {
    Navigator.pushNamed(context, '/record').then((_) => _loadRecordings());
  }

  void _navigateToAnalysis(Recording recording) {
    Navigator.pushNamed(
      context,
      '/analysis',
      arguments: {'recordingPath': recording.videoPath},
    );
  }

  Future<void> _deleteRecording(String id) async {
    final storage = Provider.of<StorageService>(context, listen: false);
    await storage.deleteRecording(id);
    await _loadRecordings();
    
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Recording deleted')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Chess Vision'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            onPressed: _showSettings,
            tooltip: 'Settings',
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadRecordings,
              child: Column(
                children: [
                  // Stats header
                  if (_recordings.isNotEmpty) _buildStatsHeader(),
                  
                  // Recording list
                  Expanded(
                    child: RecordingList(
                      recordings: _recordings,
                      onRecordingTap: _navigateToAnalysis,
                      onDeleteTap: _deleteRecording,
                    ),
                  ),
                ],
              ),
            ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _navigateToRecording,
        icon: const Icon(Icons.videocam),
        label: const Text('New Recording'),
      ),
    );
  }

  Widget _buildStatsHeader() {
    final totalDuration = _recordings.fold(
      Duration.zero,
      (sum, r) => sum + r.duration,
    );
    final totalMoves = _recordings.fold(0, (sum, r) => sum + r.moveCount);
    
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            Theme.of(context).colorScheme.primaryContainer,
            Theme.of(context).colorScheme.primaryContainer.withOpacity(0.7),
          ],
        ),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _buildStatItem(
            icon: Icons.video_collection,
            value: '${_recordings.length}',
            label: 'Recordings',
          ),
          _buildStatItem(
            icon: Icons.schedule,
            value: '${totalDuration.inMinutes}m',
            label: 'Total Time',
          ),
          _buildStatItem(
            icon: Icons.sports_mma,
            value: '$totalMoves',
            label: 'Moves',
          ),
        ],
      ),
    );
  }

  Widget _buildStatItem({
    required IconData icon,
    required String value,
    required String label,
  }) {
    return Column(
      children: [
        Icon(icon, size: 28),
        const SizedBox(height: 4),
        Text(
          value,
          style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: Theme.of(context).colorScheme.onPrimaryContainer.withOpacity(0.7),
          ),
        ),
      ],
    );
  }

  void _showSettings() {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.delete_sweep),
              title: const Text('Clear All Recordings'),
              onTap: () async {
                Navigator.pop(context);
                final confirmed = await showDialog<bool>(
                  context: context,
                  builder: (context) => AlertDialog(
                    title: const Text('Clear All?'),
                    content: const Text('This will delete all recordings permanently.'),
                    actions: [
                      TextButton(
                        onPressed: () => Navigator.pop(context, false),
                        child: const Text('Cancel'),
                      ),
                      FilledButton(
                        onPressed: () => Navigator.pop(context, true),
                        style: FilledButton.styleFrom(
                          backgroundColor: Colors.red,
                        ),
                        child: const Text('Clear All'),
                      ),
                    ],
                  ),
                );
                
                if (confirmed == true) {
                  final storage = Provider.of<StorageService>(context, listen: false);
                  await storage.clearAllRecordings();
                  await _loadRecordings();
                }
              },
            ),
            ListTile(
              leading: const Icon(Icons.info_outline),
              title: const Text('About'),
              onTap: () {
                Navigator.pop(context);
                showAboutDialog(
                  context: context,
                  applicationName: 'Chess Vision',
                  applicationVersion: '1.0.0',
                  applicationLegalese: '© 2026 Chess Vision App',
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}
