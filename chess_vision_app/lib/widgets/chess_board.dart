import 'package:flutter/material.dart';

import '../models/chess_position.dart';

class ChessBoard extends StatelessWidget {
  final ChessPosition position;
  final double size;
  final bool showCoordinates;
  final void Function(int row, int col)? onSquareTap;
  final List<String>? highlightedSquares;
  final bool flipped;

  const ChessBoard({
    super.key,
    required this.position,
    this.size = 320,
    this.showCoordinates = true,
    this.onSquareTap,
    this.highlightedSquares,
    this.flipped = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size + (showCoordinates ? 24 : 0),
      height: size + (showCoordinates ? 24 : 0),
      decoration: BoxDecoration(
        color: Colors.brown.shade800,
        borderRadius: BorderRadius.circular(4),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.3),
            blurRadius: 8,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: [
          // Rank labels (top)
          if (showCoordinates) _buildRankLabels(isTop: true),
          
          Expanded(
            child: Row(
              children: [
                // File labels (left)
                if (showCoordinates) _buildFileLabels(isLeft: true),
                
                // Board
                Expanded(
                  child: AspectRatio(
                    aspectRatio: 1,
                    child: _buildBoard(),
                  ),
                ),
                
                // File labels (right)
                if (showCoordinates) _buildFileLabels(isLeft: false),
              ],
            ),
          ),
          
          // Rank labels (bottom)
          if (showCoordinates) _buildRankLabels(isTop: false),
        ],
      ),
    );
  }

  Widget _buildBoard() {
    return Container(
      decoration: BoxDecoration(
        border: Border.all(
          color: Colors.brown.shade900,
          width: 2,
        ),
      ),
      child: Column(
        children: List.generate(8, (row) {
          return Expanded(
            child: Row(
              children: List.generate(8, (col) {
                final actualRow = flipped ? 7 - row : row;
                final actualCol = flipped ? 7 - col : col;
                return _buildSquare(actualRow, actualCol);
              }),
            ),
          );
        }),
      ),
    );
  }

  Widget _buildSquare(int row, int col) {
    final isLight = (row + col) % 2 == 0;
    final piece = position.pieceAt(row, col);
    final coord = '${String.fromCharCode('a'.codeUnitAt(0) + col)}${8 - row}';
    final isHighlighted = highlightedSquares?.contains(coord) ?? false;
    
    return Expanded(
      child: GestureDetector(
        onTap: onSquareTap != null ? () => onSquareTap!(row, col) : null,
        child: Container(
          decoration: BoxDecoration(
            color: isHighlighted
                ? Colors.yellow.withOpacity(0.5)
                : isLight
                    ? const Color(0xFFEBECD0)
                    : const Color(0xFF779556),
          ),
          child: Center(
            child: piece.isNone
                ? null
                : Text(
                    piece.unicodeSymbol,
                    style: TextStyle(
                      fontSize: size / 10,
                      height: 1,
                    ),
                  ),
          ),
        ),
      ),
    );
  }

  Widget _buildRankLabels({required bool isTop}) {
    return Container(
      height: 20,
      child: Row(
        children: [
          if (showCoordinates) const SizedBox(width: 20),
          ...List.generate(8, (index) {
            final rank = isTop == flipped ? 8 - index : index + 1;
            return Expanded(
              child: Center(
                child: Text(
                  '$rank',
                  style: TextStyle(
                    fontSize: 10,
                    color: Colors.brown.shade200,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            );
          }),
          if (showCoordinates) const SizedBox(width: 20),
        ],
      ),
    );
  }

  Widget _buildFileLabels({required bool isLeft}) {
    return Container(
      width: 20,
      child: Column(
        children: List.generate(8, (index) {
          final fileIndex = isLeft == flipped ? 7 - index : index;
          final file = String.fromCharCode('a'.codeUnitAt(0) + fileIndex);
          return Expanded(
            child: Center(
              child: Text(
                file,
                style: TextStyle(
                  fontSize: 10,
                  color: Colors.brown.shade200,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          );
        }),
      ),
    );
  }
}

class MiniChessBoard extends StatelessWidget {
  final ChessPosition position;
  final double size;

  const MiniChessBoard({
    super.key,
    required this.position,
    this.size = 120,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(4),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.2),
            blurRadius: 4,
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(4),
        child: Column(
          children: List.generate(8, (row) {
            return Expanded(
              child: Row(
                children: List.generate(8, (col) {
                  final isLight = (row + col) % 2 == 0;
                  final piece = position.pieceAt(row, col);
                  
                  return Expanded(
                    child: Container(
                      color: isLight
                          ? const Color(0xFFEBECD0)
                          : const Color(0xFF779556),
                      child: piece.isNone
                          ? null
                          : Center(
                              child: Text(
                                piece.unicodeSymbol,
                                style: TextStyle(fontSize: size / 14),
                              ),
                            ),
                    ),
                  );
                }),
              ),
            );
          }),
        ),
      ),
    );
  }
}
