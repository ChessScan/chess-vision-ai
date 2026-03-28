import 'chess_piece.dart';
import 'chess_position.dart';

class ChessMove {
  final int fromRow;
  final int fromCol;
  final int toRow;
  final int toCol;
  final ChessPiece piece;
  final ChessPiece? capturedPiece;
  final String? promotion;
  final DateTime timestamp;

  ChessMove({
    required this.fromRow,
    required this.fromCol,
    required this.toRow,
    required this.toCol,
    required this.piece,
    this.capturedPiece,
    this.promotion,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();

  String get algebraicNotation {
    final fromSquare = _squareNotation(fromRow, fromCol);
    final toSquare = _squareNotation(toRow, toCol);
    
    if (piece.type == PieceType.king && 
        (fromCol - toCol).abs() == 2) {
      // Castling
      return toCol > fromCol ? 'O-O' : 'O-O-O';
    }
    
    String notation = piece.notation;
    
    // Handle pawn captures (show file)
    if (piece.type == PieceType.pawn && capturedPiece != null) {
      notation = String.fromCharCode('a'.codeUnitAt(0) + fromCol);
    }
    
    // Add capture symbol
    if (capturedPiece != null) {
      notation += 'x';
    }
    
    notation += toSquare;
    
    if (promotion != null) {
      notation += '=$promotion';
    }
    
    return notation;
  }

  String get fullNotation {
    return '$algebraicNotation (${piece.unicodeSymbol} $fromRow,$fromCol → $toRow,$toCol)';
  }

  static String _squareNotation(int row, int col) {
    final file = String.fromCharCode('a'.codeUnitAt(0) + col);
    final rank = 8 - row;
    return '$file$rank';
  }

  ChessPosition applyTo(ChessPosition position) {
    final newBoard = position.board.map((row) => row.toList()).toList();
    
    newBoard[toRow][toCol] = piece;
    newBoard[fromRow][fromCol] = const ChessPiece.none();
    
    return ChessPosition(
      board: newBoard,
      turn: position.turn == PieceColor.white ? PieceColor.black : PieceColor.white,
      moveNumber: position.turn == PieceColor.black ? position.moveNumber + 1 : position.moveNumber,
      lastMoveNotation: algebraicNotation,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'fromRow': fromRow,
      'fromCol': fromCol,
      'toRow': toRow,
      'toCol': toCol,
      'piece': {
        'type': piece.type.name,
        'color': piece.color.name,
      },
      'capturedPiece': capturedPiece != null ? {
        'type': capturedPiece!.type.name,
        'color': capturedPiece!.color.name,
      } : null,
      'promotion': promotion,
      'timestamp': timestamp.toIso8601String(),
    };
  }

  factory ChessMove.fromJson(Map<String, dynamic> json) {
    return ChessMove(
      fromRow: json['fromRow'],
      fromCol: json['fromCol'],
      toRow: json['toRow'],
      toCol: json['toCol'],
      piece: ChessPiece(
        type: PieceType.values.byName(json['piece']['type']),
        color: PieceColor.values.byName(json['piece']['color']),
      ),
      capturedPiece: json['capturedPiece'] != null ? ChessPiece(
        type: PieceType.values.byName(json['capturedPiece']['type']),
        color: PieceColor.values.byName(json['capturedPiece']['color']),
      ) : null,
      promotion: json['promotion'],
      timestamp: DateTime.parse(json['timestamp']),
    );
  }
}
