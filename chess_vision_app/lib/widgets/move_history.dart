import 'package:flutter/material.dart';

import '../models/chess_move.dart';

class MoveHistory extends StatelessWidget {
  final List<ChessMove> moves;
  final int? selectedIndex;
  final Function(int)? onMoveSelected;

  const MoveHistory({
    super.key,
    required this.moves,
    this.selectedIndex,
    this.onMoveSelected,
  });

  @override
  Widget build(BuildContext context) {
    if (moves.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.history,
              size: 48,
              color: Colors.grey.shade600,
            ),
            const SizedBox(height: 8),
            Text(
              'No moves yet',
              style: TextStyle(color: Colors.grey.shade500),
            ),
          ],
        ),
      );
    }

    return Container(
      decoration: BoxDecoration(
        color: Colors.grey.shade900,
        borderRadius: BorderRadius.circular(8),
      ),
      child: ListView.builder(
        itemCount: (moves.length / 2).ceil(),
        padding: const EdgeInsets.all(8),
        itemBuilder: (context, index) {
          return _buildMoveRow(context, index);
        },
      ),
    );
  }

  Widget _buildMoveRow(BuildContext context, int moveNumber) {
    final whiteIndex = moveNumber * 2;
    final blackIndex = whiteIndex + 1;
    
    final whiteMove = whiteIndex < moves.length ? moves[whiteIndex] : null;
    final blackMove = blackIndex < moves.length ? moves[blackIndex] : null;
    
    final moveNum = moveNumber + 1;

    return Container(
      padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
      decoration: BoxDecoration(
        color: moveNumber % 2 == 0 
            ? Colors.grey.shade800.withOpacity(0.3) 
            : Colors.transparent,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Row(
        children: [
          // Move number
          SizedBox(
            width: 40,
            child: Text(
              '$moveNum.',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: Colors.grey.shade500,
                fontSize: 13,
              ),
            ),
          ),
          
          // White move
          Expanded(
            child: _MoveButton(
              move: whiteMove,
              isSelected: selectedIndex == whiteIndex,
              onTap: () => onMoveSelected?.call(whiteIndex),
            ),
          ),
          
          const SizedBox(width: 8),
          
          // Black move
          Expanded(
            child: _MoveButton(
              move: blackMove,
              isSelected: selectedIndex == blackIndex,
              onTap: blackMove != null 
                  ? () => onMoveSelected?.call(blackIndex) 
                  : null,
            ),
          ),
        ],
      ),
    );
  }
}

class _MoveButton extends StatelessWidget {
  final ChessMove? move;
  final bool isSelected;
  final VoidCallback? onTap;

  const _MoveButton({
    required this.move,
    required this.isSelected,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    if (move == null) {
      return const SizedBox.shrink();
    }

    return Material(
      color: isSelected 
          ? Theme.of(context).colorScheme.primaryContainer 
          : Colors.transparent,
      borderRadius: BorderRadius.circular(4),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(4),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 8),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                move!.piece.unicodeSymbol,
                style: const TextStyle(fontSize: 16),
              ),
              const SizedBox(width: 4),
              Text(
                move!.algebraicNotation,
                style: TextStyle(
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                  color: isSelected 
                      ? Theme.of(context).colorScheme.onPrimaryContainer 
                      : Theme.of(context).colorScheme.onSurface,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class MoveHistoryTimeline extends StatelessWidget {
  final List<ChessMove> moves;
  final int currentMoveIndex;
  final VoidCallback onFirst;
  final VoidCallback onPrevious;
  final VoidCallback onNext;
  final VoidCallback onLast;

  const MoveHistoryTimeline({
    super.key,
    required this.moves,
    required this.currentMoveIndex,
    required this.onFirst,
    required this.onPrevious,
    required this.onNext,
    required this.onLast,
  });

  @override
  Widget build(BuildContext context) {
    final canGoBack = currentMoveIndex >= 0;
    final canGoForward = currentMoveIndex < moves.length - 1;
    
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.grey.shade900,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          IconButton(
            icon: const Icon(Icons.first_page),
            onPressed: canGoBack ? onFirst : null,
            tooltip: 'First move',
          ),
          IconButton(
            icon: const Icon(Icons.navigate_before),
            onPressed: canGoBack ? onPrevious : null,
            tooltip: 'Previous move',
          ),
          Text(
            '${currentMoveIndex + 1} / ${moves.length}',
            style: const TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 14,
            ),
          ),
          IconButton(
            icon: const Icon(Icons.navigate_next),
            onPressed: canGoForward ? onNext : null,
            tooltip: 'Next move',
          ),
          IconButton(
            icon: const Icon(Icons.last_page),
            onPressed: canGoForward ? onLast : null,
            tooltip: 'Last move',
          ),
        ],
      ),
    );
  }
}
