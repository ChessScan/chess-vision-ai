import 'chess_move.dart';

class Recording {
  final String id;
  final String videoPath;
  final DateTime createdAt;
  final Duration duration;
  final String? name;
  final List<ChessMove> moves;
  final Map<String, dynamic>? metadata;

  Recording({
    required this.id,
    required this.videoPath,
    required this.createdAt,
    required this.duration,
    this.name,
    this.moves = const [],
    this.metadata,
  });

  String get displayName => name ?? 'Recording ${createdAt.toIso8601String().split('T')[0]}';

  String get formattedDuration {
    final minutes = duration.inMinutes;
    final seconds = duration.inSeconds % 60;
    return '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
  }

  String get formattedDate {
    final now = DateTime.now();
    final diff = now.difference(createdAt);
    
    if (diff.inDays == 0) {
      if (diff.inHours == 0) {
        if (diff.inMinutes == 0) {
          return 'Just now';
        }
        return '${diff.inMinutes}m ago';
      }
      return '${diff.inHours}h ago';
    } else if (diff.inDays == 1) {
      return 'Yesterday';
    } else if (diff.inDays < 7) {
      return '${diff.inDays} days ago';
    }
    
    return '${createdAt.day}/${createdAt.month}/${createdAt.year}';
  }

  int get moveCount => moves.length;

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'videoPath': videoPath,
      'createdAt': createdAt.toIso8601String(),
      'duration': duration.inSeconds,
      'name': name,
      'moves': moves.map((m) => m.toJson()).toList(),
      'metadata': metadata,
    };
  }

  factory Recording.fromJson(Map<String, dynamic> json) {
    return Recording(
      id: json['id'],
      videoPath: json['videoPath'],
      createdAt: DateTime.parse(json['createdAt']),
      duration: Duration(seconds: json['duration']),
      name: json['name'],
      moves: (json['moves'] as List? ?? [])
          .map((m) => ChessMove.fromJson(m))
          .toList(),
      metadata: json['metadata'],
    );
  }

  Recording copyWith({
    String? id,
    String? videoPath,
    DateTime? createdAt,
    Duration? duration,
    String? name,
    List<ChessMove>? moves,
    Map<String, dynamic>? metadata,
  }) {
    return Recording(
      id: id ?? this.id,
      videoPath: videoPath ?? this.videoPath,
      createdAt: createdAt ?? this.createdAt,
      duration: duration ?? this.duration,
      name: name ?? this.name,
      moves: moves ?? this.moves,
      metadata: metadata ?? this.metadata,
    );
  }
}
