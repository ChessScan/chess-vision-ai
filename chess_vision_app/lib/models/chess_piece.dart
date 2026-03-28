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
    switch (type) {
      case PieceType.king:
        return 'K';
      case PieceType.queen:
        return 'Q';
      case PieceType.rook:
        return 'R';
      case PieceType.bishop:
        return 'B';
      case PieceType.knight:
        return 'N';
      case PieceType.pawn:
        return '';
      case PieceType.none:
        return '';
    }
  }

  String get unicodeSymbol {
    if (color == PieceColor.white) {
      switch (type) {
        case PieceType.king:
          return '♔';
        case PieceType.queen:
          return '♕';
        case PieceType.rook:
          return '♖';
        case PieceType.bishop:
          return '♗';
        case PieceType.knight:
          return '♘';
        case PieceType.pawn:
          return '♙';
        case PieceType.none:
          return '';
      }
    } else {
      switch (type) {
        case PieceType.king:
          return '♚';
        case PieceType.queen:
          return '♛';
        case PieceType.rook:
          return '♜';
        case PieceType.bishop:
          return '♝';
        case PieceType.knight:
          return '♞';
        case PieceType.pawn:
          return '♟';
        case PieceType.none:
          return '';
      }
    }
    return '';
  }

  ChessPiece copyWith({PieceType? type, PieceColor? color}) {
    return ChessPiece(
      type: type ?? this.type,
      color: color ?? this.color,
    );
  }
}
