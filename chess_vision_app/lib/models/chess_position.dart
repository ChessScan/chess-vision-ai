import 'chess_move.dart';

enum PieceType { king, queen, rook, bishop, knight, pawn, none }

enum PieceColor { white, black, none }

class ChessPiece {
  final PieceType type;
  final PieceColor color;

  const ChessPiece({required this.type, required this.color});

  const ChessPiece.none() : type = PieceType.none, color = PieceColor.none;

  bool get isNone => type == PieceType.none;

  String get notation {
    if (isNone) return '';
    final typeChar = switch (type) {
      PieceType.king => 'K',
      PieceType.queen => 'Q',
      PieceType.rook => 'R',
      PieceType.bishop => 'B',
      PieceType.knight => 'N',
      PieceType.pawn => '',
      PieceType.none => '',
    };
    return typeChar;
  }

  String get unicodeSymbol {
    if (color == PieceColor.white) {
      return switch (type) {
        PieceType.king => '♔',
        PieceType.queen => '♕',
        PieceType.rook => '♖',
        PieceType.bishop => '♗',
        PieceType.knight => '♘',
        PieceType.pawn => '♙',
        PieceType.none => '',
      };
    } else {
      return switch (type) {
        PieceType.king => '♚',
        PieceType.queen => '♛',
        PieceType.rook => '♜',
        PieceType.bishop => '♝',
        PieceType.knight => '♞',
        PieceType.pawn => '♟',
        PieceType.none => '',
      };
    }
  }

  ChessPiece copyWith({PieceType? type, PieceColor? color}) {
    return ChessPiece(
      type: type ?? this.type,
      color: color ?? this.color,
    );
  }
}

class ChessPosition {
  final List<List<ChessPiece>> board;
  final PieceColor turn;
  final int moveNumber;
  final String? lastMoveNotation;

  ChessPosition({
    required this.board,
    this.turn = PieceColor.white,
    this.moveNumber = 1,
    this.lastMoveNotation,
  });

  factory ChessPosition.initial() {
    return ChessPosition(
      board: _createInitialBoard(),
      turn: PieceColor.white,
      moveNumber: 1,
    );
  }

  factory ChessPosition.fromFEN(String fen) {
    final parts = fen.split(' ');
    final boardPart = parts[0];
    final turnPart = parts.length > 1 ? parts[1] : 'w';
    
    final board = List.generate(8, (_) => List.generate(8, (_) => const ChessPiece.none()));
    
    final rows = boardPart.split('/');
    for (int row = 0; row < 8; row++) {
      int col = 0;
      for (final char in rows[row].split('')) {
        if (RegExp(r'[1-8]').hasMatch(char)) {
          col += int.parse(char);
        } else {
          final color = char == char.toUpperCase() ? PieceColor.white : PieceColor.black;
          final type = switch (char.toLowerCase()) {
            'k' => PieceType.king,
            'q' => PieceType.queen,
            'r' => PieceType.rook,
            'b' => PieceType.bishop,
            'n' => PieceType.knight,
            'p' => PieceType.pawn,
            _ => PieceType.none,
          };
          board[row][col] = ChessPiece(type: type, color: color);
          col++;
        }
      }
    }
    
    return ChessPosition(
      board: board,
      turn: turnPart == 'w' ? PieceColor.white : PieceColor.black,
    );
  }

  static List<List<ChessPiece>> _createInitialBoard() {
    return [
      // Black back rank
      [
        const ChessPiece(type: PieceType.rook, color: PieceColor.black),
        const ChessPiece(type: PieceType.knight, color: PieceColor.black),
        const ChessPiece(type: PieceType.bishop, color: PieceColor.black),
        const ChessPiece(type: PieceType.queen, color: PieceColor.black),
        const ChessPiece(type: PieceType.king, color: PieceColor.black),
        const ChessPiece(type: PieceType.bishop, color: PieceColor.black),
        const ChessPiece(type: PieceType.knight, color: PieceColor.black),
        const ChessPiece(type: PieceType.rook, color: PieceColor.black),
      ],
      // Black pawns
      List.generate(8, (_) => const ChessPiece(type: PieceType.pawn, color: PieceColor.black)),
      // Empty rows
      List.generate(8, (_) => const ChessPiece.none()),
      List.generate(8, (_) => const ChessPiece.none()),
      List.generate(8, (_) => const ChessPiece.none()),
      List.generate(8, (_) => const ChessPiece.none()),
      // White pawns
      List.generate(8, (_) => const ChessPiece(type: PieceType.pawn, color: PieceColor.white)),
      // White back rank
      [
        const ChessPiece(type: PieceType.rook, color: PieceColor.white),
        const ChessPiece(type: PieceType.knight, color: PieceColor.white),
        const ChessPiece(type: PieceType.bishop, color: PieceColor.white),
        const ChessPiece(type: PieceType.queen, color: PieceColor.white),
        const ChessPiece(type: PieceType.king, color: PieceColor.white),
        const ChessPiece(type: PieceType.bishop, color: PieceColor.white),
        const ChessPiece(type: PieceType.knight, color: PieceColor.white),
        const ChessPiece(type: PieceType.rook, color: PieceColor.white),
      ],
    ];
  }

  ChessPiece pieceAt(int row, int col) {
    if (row < 0 || row > 7 || col < 0 || col > 7) {
      return const ChessPiece.none();
    }
    return board[row][col];
  }

  String toFEN() {
    final buffer = StringBuffer();
    for (int row = 0; row < 8; row++) {
      int emptyCount = 0;
      for (int col = 0; col < 8; col++) {
        final piece = board[row][col];
        if (piece.isNone) {
          emptyCount++;
        } else {
          if (emptyCount > 0) {
            buffer.write(emptyCount);
            emptyCount = 0;
          }
          String char = switch (piece.type) {
            PieceType.king => 'k',
            PieceType.queen => 'q',
            PieceType.rook => 'r',
            PieceType.bishop => 'b',
            PieceType.knight => 'n',
            PieceType.pawn => 'p',
            PieceType.none => '',
          };
          if (piece.color == PieceColor.white) {
            char = char.toUpperCase();
          }
          buffer.write(char);
        }
      }
      if (emptyCount > 0) {
        buffer.write(emptyCount);
      }
      if (row < 7) buffer.write('/');
    }
    buffer.write(turn == PieceColor.white ? ' w' : ' b');
    buffer.write(' - - 0 $moveNumber');
    return buffer.toString();
  }

  ChessPosition copyWith({
    List<List<ChessPiece>>? board,
    PieceColor? turn,
    int? moveNumber,
    String? lastMoveNotation,
  }) {
    return ChessPosition(
      board: board ?? this.board.map((row) => row.toList()).toList(),
      turn: turn ?? this.turn,
      moveNumber: moveNumber ?? this.moveNumber,
      lastMoveNotation: lastMoveNotation ?? this.lastMoveNotation,
    );
  }
}
