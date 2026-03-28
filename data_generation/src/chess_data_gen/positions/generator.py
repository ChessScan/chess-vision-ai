"""
Chess position generation and FEN handling.
"""

import random
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
from pathlib import Path
import json


@dataclass
class ChessPosition:
    """Represents a chess position."""
    fen: str
    category: str  # 'opening', 'middlegame', 'endgame', 'tactical', 'random'
    piece_count: int
    tags: List[str]
    source: Optional[str] = None
    
    def __post_init__(self):
        """Validate FEN and extract piece count if not provided."""
        if self.piece_count == 0:
            self.piece_count = self._count_pieces_from_fen(self.fen)
    
    @staticmethod
    def _count_pieces_from_fen(fen: str) -> int:
        """Count total pieces in a FEN string."""
        # FEN format: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
        board_part = fen.split()[0]
        count = 0
        for char in board_part:
            if char.isalpha():
                count += 1
        return count
    
    def get_piece_at(self, square: str) -> Optional[str]:
        """Get piece at a specific square (e.g., 'e4')."""
        return fen_to_board(self.fen).get(square)


def fen_to_board(fen: str) -> Dict[str, str]:
    """Convert FEN to dictionary mapping squares to pieces."""
    board = {}
    ranks = fen.split()[0].split('/')
    
    for rank_idx, rank in enumerate(ranks):
        file_idx = 0
        for char in rank:
            if char.isdigit():
                file_idx += int(char)
            else:
                square = chr(ord('a') + file_idx) + str(8 - rank_idx)
                board[square] = char
                file_idx += 1
    
    return board


def board_to_fen(board: Dict[str, str]) -> str:
    """Convert board dictionary to FEN."""
    ranks = []
    for rank_num in range(8, 0, -1):
        rank_str = ""
        empty_count = 0
        for file_char in 'abcdefgh':
            square = file_char + str(rank_num)
            piece = board.get(square)
            if piece:
                if empty_count > 0:
                    rank_str += str(empty_count)
                    empty_count = 0
                rank_str += piece
            else:
                empty_count += 1
        
        if empty_count > 0:
            rank_str += str(empty_count)
        
        ranks.append(rank_str)
    
    return '/'.join(ranks) + " w - - 0 1"


# Curated positions database (subset - full version would be in JSON file)
CURATED_POSITIONS = {
    'opening': [
        # Standard openings
        ("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1", "King's Pawn"),
        ("rnbqkbnr/pppp1ppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2", "French Defense"),
        ("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq -", "Italian Game"),
        ("rnbqkb1r/pppp1ppp/4pn2/8/4P3/4PN2/PPPP1PPP/RNBQKB1R b KQkq -", "English Opening"),
        ("rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq -", "Sicilian Defense"),
    ],
    'middlegame': [
        # Complex middlegame positions
        ("r1bq1rk1/ppp2ppp/2np1n2/1Bb1p3/4P3/2PP1N2/PP3PPP/RNBQ1RK1 w - -", "Open position"),
        ("r2q1rk1/1pp2ppp/p1np1n2/1Bb1p3/4P3/2PP1NPP/PP3P2/RNBQ1RK1 b - -", "Closed position"),
        ("r1bq1rk1/ppp2ppp/2n2n2/3pp3/1bPP4/2N1PN2/PP3PPP/R1BQKB1R w - -", "Isolated queen pawn"),
        ("r3kb1r/ppp2ppp/2n2n2/4p3/4P3/2N2N2/PPP2PPP/R1B1KB1R w - -", "End of opening"),
    ],
    'endgame': [
        # King and pawn endgames
        ("8/8/3k4/8/4K3/8/8/8 w - - 0 1", "King only"),
        ("8/8/3k4/3p4/4P3/3K4/8/8 w - -", "Pawn race"),
        ("8/8/8/8/8/3K4/4P3/3k4 w - -", "King and pawn vs king"),
        ("8/8/8/8/8/3K4/3P4/3R3k w - -", "Rook and pawn"),
        ("8/8/8/8/8/3K4/2Q5/4k3 w - -", "Queen vs king"),
        ("8/8/8/8/8/3K4/2N5/4k3 w - -", "Knight checkmate practice"),
    ],
    'tactical': [
        # Positions with visible tactics
        ("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq -", "Fork opportunity"),
        ("rnbqkb1r/ppp2ppp/4pn2/3p4/3P4/2PB4/PP3PPP/RNBQK1NR b KQkq -", "Pin on knight"),
        ("r2qk2r/ppp2ppp/2np1n2/1Bb1p3/4P3/2N2N2/PPP2PPP/R1BQK2R w KQkq -", "Bishop skewer"),
        ("r1bqk2r/ppp2ppp/2np1n2/1b2p3/1P2P3/P1N2N2/2PP1PPP/R1BQKB1R b - -", "Discovered attack"),
        ("4r1k1/ppp2ppp/8/3Q4/8/8/PPP2PPP/4R1K1 w - -", "Back rank mate"),
    ],
}


class PositionGenerator:
    """Generate chess positions for training data."""
    
    def __init__(self, config):
        self.config = config
        self.positions: List[ChessPosition] = []
        self.random_state = random.Random(config.random_seed)
    
    def generate(self) -> List[ChessPosition]:
        """Generate all positions according to config."""
        self.positions = []
        
        category_distribution = self.config.positions.get_category_distribution()
        
        for category, count in category_distribution.items():
            if category == 'random_legal':
                self._generate_random_positions(count)
            else:
                self._generate_curated_positions(category, count)
        
        # Shuffle positions
        self.random_state.shuffle(self.positions)
        
        return self.positions
    
    def _generate_curated_positions(self, category: str, count: int):
        """Generate positions from curated database."""
        if category not in CURATED_POSITIONS:
            return
        
        available = CURATED_POSITIONS[category]
        
        # Sample with replacement if we need more than available
        for i in range(count):
            fen, description = available[i % len(available)]
            self.positions.append(ChessPosition(
                fen=fen,
                category=category,
                piece_count=0,  # Will be calculated
                tags=[description],
                source='curated'
            ))
    
    def _generate_random_positions(self, count: int):
        """Generate random legal positions."""
        for _ in range(count):
            # Generate random position with constraints
            min_pieces = self.config.positions.constraints.get('min_pieces', 3)
            max_pieces = self.config.positions.constraints.get('max_pieces', 32)
            
            piece_count = self.random_state.randint(min_pieces, max_pieces)
            board = self._create_random_board_state(piece_count)
            
            fen = board_to_fen(board)
            
            self.positions.append(ChessPosition(
                fen=fen,
                category='random',
                piece_count=piece_count,
                tags=['random_legal'],
                source='generated'
            ))
    
    def _create_random_board_state(self, piece_count: int) -> Dict[str, str]:
        """Create a random but legal board state."""
        board = {}
        
        # Always include both kings
        board['e1'] = 'K'
        board['e8'] = 'k'
        
        pieces = ['Q', 'R', 'R', 'B', 'B', 'N', 'N'] + ['P'] * 8
        pieces += ['q', 'r', 'r', 'b', 'b', 'n', 'n'] + ['p'] * 8
        
        # Randomly sample remaining pieces
        remaining = piece_count - 2
        if remaining > 0:
            selected = self.random_state.sample(pieces, min(remaining, len(pieces)))
            
            # Place pieces randomly on empty squares
            empty_squares = [f + r for f in 'abcdefgh' for r in '12345678']
            empty_squares.remove('e1')
            empty_squares.remove('e8')
            
            self.random_state.shuffle(empty_squares)
            
            for i, piece in enumerate(selected):
                if i < len(empty_squares):
                    # Don't place pawns on first or last rank
                    square = empty_squares[i]
                    if piece.upper() == 'P' and square[1] in ['1', '8']:
                        continue
                    board[square] = piece
        
        return board
    
    def load_from_file(self, filepath: Path, count: Optional[int] = None):
        """Load positions from a file (PGN, JSON, or FEN list)."""
        suffix = filepath.suffix.lower()
        
        if suffix == '.json':
            self._load_json(filepath, count)
        elif suffix == '.pgn':
            self._load_pgn(filepath, count)
        elif suffix == '.txt':
            self._load_fen_list(filepath, count)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")
    
    def _load_json(self, filepath: Path, count: Optional[int]):
        """Load positions from JSON file."""
        with open(filepath) as f:
            data = json.load(f)
        
        positions_data = data.get('positions', [])
        if count:
            positions_data = positions_data[:count]
        
        for pos_data in positions_data:
            self.positions.append(ChessPosition(
                fen=pos_data['fen'],
                category=pos_data.get('category', 'unknown'),
                piece_count=pos_data.get('piece_count', 0),
                tags=pos_data.get('tags', []),
                source=str(filepath)
            ))
    
    def _load_pgn(self, filepath: Path, count: Optional[int]):
        """Load positions from PGN file (extract middlegame positions)."""
        # Simplified PGN parser - extract positions after 10 moves
        with open(filepath) as f:
            content = f.read()
        
        # Find games and extract positions
        # This is a simplified version - full PGN parsing would need a library
        pass
    
    def _load_fen_list(self, filepath: Path, count: Optional[int]):
        """Load positions from FEN list (one per line)."""
        with open(filepath) as f:
            lines = f.readlines()
        
        if count:
            lines = lines[:count]
        
        for line in lines:
            fen = line.strip()
            if fen and not fen.startswith('#'):
                self.positions.append(ChessPosition(
                    fen=fen,
                    category='loaded',
                    piece_count=0,
                    tags=['from_file'],
                    source=str(filepath)
                ))
    
    def save_to_json(self, filepath: Path):
        """Save positions to JSON file."""
        data = {
            'positions': [
                {
                    'fen': pos.fen,
                    'category': pos.category,
                    'piece_count': pos.piece_count,
                    'tags': pos.tags,
                }
                for pos in self.positions
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
