import 'dart:async';
import 'dart:math';

import '../models/chess_position.dart';
import '../models/chess_move.dart';

class MockDetectionService {
  ChessPosition _currentPosition = ChessPosition.initial();
  final List<ChessMove> _moveHistory = [];
  Timer? _autoMoveTimer;
  bool _isPaused = false;
  final Random _random = Random();

  final _positionController = StreamController<ChessPosition>.broadcast();
  Stream<ChessPosition> get positionStream => _positionController.stream;

  ChessPosition get currentPosition => _currentPosition;
  List<ChessMove> get moveHistory => List.unmodifiable(_moveHistory);
  bool get isPaused => _isPaused;

  void startAutoDetection() {
    _autoMoveTimer?.cancel();
    _autoMoveTimer = Timer.periodic(
      const Duration(seconds: 3),
      (_) => _generateRandomMove(),
    );
  }

  void stopAutoDetection() {
    _autoMoveTimer?.cancel();
    _autoMoveTimer = null;
  }

  void pause() {
    _isPaused = true;
  }

  void resume() {
    _isPaused = false;
  }

  void togglePause() {
    _isPaused = !_isPaused;
  }

  void reset() {
    _currentPosition = ChessPosition.initial();
    _moveHistory.clear();
    _positionController.add(_currentPosition);
  }

  void setPosition(ChessPosition position) {
    _currentPosition = position;
    _positionController.add(_currentPosition);
  }

  void _generateRandomMove() {
    if (_isPaused) return;

    final moves = _getAllLegalMoves(_currentPosition);
    if (moves.isEmpty) {
      // Reset if no moves (checkmate or stalemate)
      reset();
      return;
    }

    final move = moves[_random.nextInt(moves.length)];
    _applyMove(move);
  }

  List<ChessMove> _getAllLegalMoves(ChessPosition position) {
    final moves = <ChessMove>[];
    final turn = position.turn;

    for (int fromRow = 0; fromRow < 8; fromRow++) {
      for (int fromCol = 0; fromCol < 8; fromCol++) {
        final piece = position.pieceAt(fromRow, fromCol);
        if (piece.isNone || piece.color != turn) continue;

        final possibleMoves = _getPossibleMovesForPiece(
          position, fromRow, fromCol, piece,
        );
        moves.addAll(possibleMoves);
      }
    }

    return moves;
  }

  List<ChessMove> _getPossibleMovesForPiece(
    ChessPosition position,
    int row,
    int col,
    ChessPiece piece,
  ) {
    final moves = <ChessMove>[];
    
    switch (piece.type) {
      case PieceType.pawn:
        moves.addAll(_getPawnMoves(position, row, col, piece));
        break;
      case PieceType.knight:
        moves.addAll(_getKnightMoves(position, row, col, piece));
        break;
      case PieceType.bishop:
        moves.addAll(_getBishopMoves(position, row, col, piece));
        break;
      case PieceType.rook:
        moves.addAll(_getRookMoves(position, row, col, piece));
        break;
      case PieceType.queen:
        moves.addAll(_getQueenMoves(position, row, col, piece));
        break;
      case PieceType.king:
        moves.addAll(_getKingMoves(position, row, col, piece));
        break;
      default:
        break;
    }
    
    return moves;
  }

  List<ChessMove> _getPawnMoves(ChessPosition position, int row, int col, ChessPiece piece) {
    final moves = <ChessMove>[];
    final direction = piece.color == PieceColor.white ? -1 : 1;
    final startRow = piece.color == PieceColor.white ? 6 : 1;
    
    // Forward move
    final newRow = row + direction;
    if (_isValidSquare(newRow, col) && position.pieceAt(newRow, col).isNone) {
      moves.add(ChessMove(
        fromRow: row, fromCol: col,
        toRow: newRow, toCol: col,
        piece: piece,
      ));
      
      // Double move from start
      if (row == startRow) {
        final doubleRow = row + 2 * direction;
        if (position.pieceAt(doubleRow, col).isNone) {
          moves.add(ChessMove(
            fromRow: row, fromCol: col,
            toRow: doubleRow, toCol: col,
            piece: piece,
          ));
        }
      }
    }
    
    // Captures
    for (final dc in [-1, 1]) {
      final captureCol = col + dc;
      if (_isValidSquare(newRow, captureCol)) {
        final target = position.pieceAt(newRow, captureCol);
        if (!target.isNone && target.color != piece.color) {
          moves.add(ChessMove(
            fromRow: row, fromCol: col,
            toRow: newRow, toCol: captureCol,
            piece: piece,
            capturedPiece: target,
          ));
        }
      }
    }
    
    // Promotion (simplified: at last rank)
    if ((piece.color == PieceColor.white && newRow == 0) ||
        (piece.color == PieceColor.black && newRow == 7)) {
      // Replace pawn moves with promotion moves
      return moves.map((m) => ChessMove(
        fromRow: m.fromRow, fromCol: m.fromCol,
        toRow: m.toRow, toCol: m.toCol,
        piece: piece, capturedPiece: m.capturedPiece,
        promotion: 'Q',
      )).toList();
    }
    
    return moves;
  }

  List<ChessMove> _getKnightMoves(ChessPosition position, int row, int col, ChessPiece piece) {
    final moves = <ChessMove>[];
    final offsets = [
      [-2, -1], [-2, 1], [-1, -2], [-1, 2],
      [1, -2], [1, 2], [2, -1], [2, 1],
    ];
    
    for (final offset in offsets) {
      final newRow = row + offset[0];
      final newCol = col + offset[1];
      
      if (_isValidSquare(newRow, newCol)) {
        final target = position.pieceAt(newRow, newCol);
        if (target.isNone || target.color != piece.color) {
          moves.add(ChessMove(
            fromRow: row, fromCol: col,
            toRow: newRow, toCol: newCol,
            piece: piece,
            capturedPiece: target.isNone ? null : target,
          ));
        }
      }
    }
    
    return moves;
  }

  List<ChessMove> _getBishopMoves(ChessPosition position, int row, int col, ChessPiece piece) {
    return _getSlidingMoves(position, row, col, piece, [
      [-1, -1], [-1, 1], [1, -1], [1, 1],
    ]);
  }

  List<ChessMove> _getRookMoves(ChessPosition position, int row, int col, ChessPiece piece) {
    return _getSlidingMoves(position, row, col, piece, [
      [-1, 0], [1, 0], [0, -1], [0, 1],
    ]);
  }

  List<ChessMove> _getQueenMoves(ChessPosition position, int row, int col, ChessPiece piece) {
    return _getSlidingMoves(position, row, col, piece, [
      [-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1],
    ]);
  }

  List<ChessMove> _getKingMoves(ChessPosition position, int row, int col, ChessPiece piece) {
    final moves = <ChessMove>[];
    
    for (int dr = -1; dr <= 1; dr++) {
      for (int dc = -1; dc <= 1; dc++) {
        if (dr == 0 && dc == 0) continue;
        
        final newRow = row + dr;
        final newCol = col + dc;
        
        if (_isValidSquare(newRow, newCol)) {
          final target = position.pieceAt(newRow, newCol);
          if (target.isNone || target.color != piece.color) {
            moves.add(ChessMove(
              fromRow: row, fromCol: col,
              toRow: newRow, toCol: newCol,
              piece: piece,
              capturedPiece: target.isNone ? null : target,
            ));
          }
        }
      }
    }
    
    return moves;
  }

  List<ChessMove> _getSlidingMoves(
    ChessPosition position,
    int row, int col, ChessPiece piece,
    List<List<int>> directions,
  ) {
    final moves = <ChessMove>[];
    
    for (final dir in directions) {
      int newRow = row + dir[0];
      int newCol = col + dir[1];
      
      while (_isValidSquare(newRow, newCol)) {
        final target = position.pieceAt(newRow, newCol);
        
        if (target.isNone) {
          moves.add(ChessMove(
            fromRow: row, fromCol: col,
            toRow: newRow, toCol: newCol,
            piece: piece,
          ));
        } else {
          if (target.color != piece.color) {
            moves.add(ChessMove(
              fromRow: row, fromCol: col,
              toRow: newRow, toCol: newCol,
              piece: piece,
              capturedPiece: target,
            ));
          }
          break;
        }
        
        newRow += dir[0];
        newCol += dir[1];
      }
    }
    
    return moves;
  }

  bool _isValidSquare(int row, int col) {
    return row >= 0 && row < 8 && col >= 0 && col < 8;
  }

  void _applyMove(ChessMove move) {
    _currentPosition = move.applyTo(_currentPosition);
    _moveHistory.add(move);
    _positionController.add(_currentPosition);
  }

  void dispose() {
    stopAutoDetection();
    _positionController.close();
  }
}
