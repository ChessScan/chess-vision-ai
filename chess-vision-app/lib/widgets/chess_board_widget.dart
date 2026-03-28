"""
Flutter ChessBoardWidget for ChessVision App
Interactive chess board with chess.com Neo piece style
"""

import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

class ChessBoardWidget extends StatefulWidget {
  final Function(String move)? onMove;
  final List<String>? initialPosition;
  final bool showLastMove;
  
  const ChessBoardWidget({
    Key? key,
    this.onMove,
    this.initialPosition,
    this.showLastMove = true,
  }) : super(key: key);

  @override
  _ChessBoardWidgetState createState() => _ChessBoardWidgetState();
}

class _ChessBoardWidgetState extends State<ChessBoardWidget> {
  late List<List<String?>> board;
  String? selectedSquare;
  List<String> possibleMoves = [];
  String? lastMoveFrom;
  String? lastMoveTo;
  
  // chess.com Neo piece colors
  final Color lightSquare = const Color(0xFFEBECD0);
  final Color darkSquare = const Color(0xFF739552);
  final Color lastMoveHighlight = const Color(0xFFF7EC5E);
  final Color selectedHighlight = const Color(0xFFBBD534);
  final Color possibleMoveIndicator = const Color(0x7A000000);
  
  @override
  void initState() {
    super.initState();
    _initializeBoard();
  }
  
  void _initializeBoard() {
    // Standard starting position
    board = [
      ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
      ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
      [null, null, null, null, null, null, null, null],
      [null, null, null, null, null, null, null, null],
      [null, null, null, null, null, null, null, null],
      [null, null, null, null, null, null, null, null],
      ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
      ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R'],
    ];
  }
  
  String _getPieceAsset(String piece) {
    // Map pieces to chess.com Neo style SVG assets
    final pieceMap = {
      'P': 'assets/pieces/w_pawn.svg',
      'N': 'assets/pieces/w_knight.svg',
      'B': 'assets/pieces/w_bishop.svg',
      'R': 'assets/pieces/w_rook.svg',
      'Q': 'assets/pieces/w_queen.svg',
      'K': 'assets/pieces/w_king.svg',
      'p': 'assets/pieces/b_pawn.svg',
      'n': 'assets/pieces/b_knight.svg',
      'b': 'assets/pieces/b_bishop.svg',
      'r': 'assets/pieces/b_rook.svg',
      'q': 'assets/pieces/b_queen.svg',
      'k': 'assets/pieces/b_king.svg',
    };
    return pieceMap[piece] ?? 'assets/pieces/w_pawn.svg';
  }
  
  void _onSquareTap(int row, int col) {
    final square = '${String.fromCharCode('a'.codeUnitAt(0) + col)}${8 - row}';
    final piece = board[row][col];
    
    setState(() {
      if (selectedSquare == null && piece != null) {
        // Select piece
        selectedSquare = square;
        _calculatePossibleMoves(row, col);
      } else if (selectedSquare != null) {
        // Move piece
        if (selectedSquare != square) {
          _movePiece(selectedSquare!, square);
          lastMoveFrom = selectedSquare;
          lastMoveTo = square;
        }
        selectedSquare = null;
        possibleMoves = [];
      }
    });
  }
  
  void _calculatePossibleMoves(int row, int col) {
    // Simplified move calculation - just adjacent squares for demo
    possibleMoves = [];
    final piece = board[row][col];
    if (piece == null) return;
    
    // Basic moves based on piece type
    if (piece.toLowerCase() == 'p') {
      // Pawn moves
      int direction = piece == 'p' ? 1 : -1;
      if (row + direction >= 0 && row + direction < 8) {
        if (board[row + direction][col] == null) {
          possibleMoves.add('${String.fromCharCode('a'.codeUnitAt(0) + col)}${8 - (row + direction)}');
        }
      }
    }
    // Add more piece logic here...
  }
  
  void _movePiece(String from, String to) {
    final fromCol = from[0].codeUnitAt(0) - 'a'.codeUnitAt(0);
    final fromRow = 8 - int.parse(from[1]);
    final toCol = to[0].codeUnitAt(0) - 'a'.codeUnitAt(0);
    final toRow = 8 - int.parse(to[1]);
    
    setState(() {
      board[toRow][toCol] = board[fromRow][fromCol];
      board[fromRow][fromCol] = null;
    });
    
    widget.onMove?.call('$from$to');
  }
  
  Widget _buildPiece(String piece) {
    final isWhite = piece == piece.toUpperCase();
    return Container(
      padding: const EdgeInsets.all(2),
      child: SvgPicture.asset(
        _getPieceAsset(piece),
        placeholderBuilder: (context) => _buildPiecePlaceholder(piece),
      ),
    );
  }
  
  Widget _buildPiecePlaceholder(String piece) {
    // Fallback if SVG not loaded
    final isWhite = piece == piece.toUpperCase();
    return Container(
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: isWhite ? Colors.white : Colors.black54,
        border: Border.all(color: Colors.black26, width: 1),
      ),
    );
  }
  
  Color _getSquareColor(int row, int col) {
    final square = '${String.fromCharCode('a'.codeUnitAt(0) + col)}${8 - row}';
    
    // Last move highlight
    if (widget.showLastMove && (square == lastMoveFrom || square == lastMoveTo)) {
      return lastMoveHighlight.withOpacity(0.6);
    }
    
    // Selected square
    if (square == selectedSquare) {
      return selectedHighlight;
    }
    
    // Base square colors
    return (row + col) % 2 == 0 ? lightSquare : darkSquare;
  }
  
  @override
  Widget build(BuildContext context) {
    return AspectRatio(
      aspectRatio: 1,
      child: Container(
        decoration: BoxDecoration(
          border: Border.all(color: Colors.black38, width: 2),
          borderRadius: BorderRadius.circular(4),
        ),
        child: GridView.builder(
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 8,
          ),
          itemCount: 64,
          physics: const NeverScrollableScrollPhysics(),
          itemBuilder: (context, index) {
            final row = index ~/ 8;
            final col = index % 8;
            final piece = board[row][col];
            final square = '${String.fromCharCode('a'.codeUnitAt(0) + col)}${8 - row}';
            
            return GestureDetector(
              onTap: () => _onSquareTap(row, col),
              child: Container(
                decoration: BoxDecoration(
                  color: _getSquareColor(row, col),
                  border: Border.all(
                    color: possibleMoves.contains(square) 
                        ? Colors.black54 
                        : Colors.transparent,
                    width: 2,
                  ),
                ),
                child: piece != null ? _buildPiece(piece) : null,
              ),
            );
          },
        ),
      ),
    );
  }
}

// Usage example widget for testing
class ChessBoardDemo extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('ChessVision Board')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: ChessBoardWidget(
          onMove: (move) {
            print('Move played: $move');
          },
        ),
      ),
    );
  }
}
