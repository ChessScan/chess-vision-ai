import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../models/recording.dart';

class RecordingList extends StatelessWidget {
  final List<Recording> recordings;
  final Function(Recording) onRecordingTap;
  final Function(String) onDeleteTap;

  const RecordingList({
    super.key,
    required this.recordings,
    required this.onRecordingTap,
    required this.onDeleteTap,
  });

  @override
  Widget build(BuildContext context) {
    if (recordings.isEmpty) {
      return const _EmptyRecordingList();
    }

    return ListView.builder(
      itemCount: recordings.length,
      padding: const EdgeInsets.all(8),
      itemBuilder: (context, index) {
        final recording = recordings[index];
        return _RecordingListItem(
          recording: recording,
          onTap: () => onRecordingTap(recording),
          onDelete: () => _showDeleteConfirmation(context, recording),
        );
      },
    );
  }

  void _showDeleteConfirmation(BuildContext context, Recording recording) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Recording?'),
        content: Text('Are you sure you want to delete "${recording.displayName}"?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () {
              Navigator.pop(context);
              onDeleteTap(recording.id);
            },
            style: FilledButton.styleFrom(
              backgroundColor: Colors.red,
            ),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }
}

class _RecordingListItem extends StatelessWidget {
  final Recording recording;
  final VoidCallback onTap;
  final VoidCallback onDelete;

  const _RecordingListItem({
    required this.recording,
    required this.onTap,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              // Thumbnail/Icon
              Container(
                width: 60,
                height: 60,
                decoration: BoxDecoration(
                  color: Colors.deepPurple.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(
                  Icons.videocam,
                  size: 32,
                  color: Colors.deepPurple,
                ),
              ),
              const SizedBox(width: 16),
              
              // Info
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      recording.displayName,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Icon(
                          Icons.schedule,
                          size: 14,
                          color: Colors.grey.shade400,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          recording.formattedDuration,
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey.shade400,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Icon(
                          Icons.calendar_today,
                          size: 14,
                          color: Colors.grey.shade400,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          recording.formattedDate,
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey.shade400,
                          ),
                        ),
                      ],
                    ),
                    if (recording.moveCount > 0) ...[
                      const SizedBox(height: 4),
                      Text(
                        '${recording.moveCount} moves',
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.green.shade400,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              
              // Actions
              IconButton(
                icon: const Icon(Icons.analytics_outlined),
                onPressed: onTap,
                tooltip: 'Analyze',
              ),
              IconButton(
                icon: const Icon(Icons.delete_outline),
                onPressed: onDelete,
                color: Colors.red.shade300,
                tooltip: 'Delete',
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _EmptyRecordingList extends StatelessWidget {
  const _EmptyRecordingList();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.video_library_outlined,
            size: 80,
            color: Colors.grey.shade600,
          ),
          const SizedBox(height: 16),
          Text(
            'No recordings yet',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  color: Colors.grey.shade400,
                ),
          ),
          const SizedBox(height: 8),
          Text(
            'Tap the + button to start recording',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Colors.grey.shade600,
                ),
          ),
        ],
      ),
    );
  }
}
