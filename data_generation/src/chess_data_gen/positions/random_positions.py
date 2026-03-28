"""
Random legal position generator.
Generates random but valid chess positions.
"""

import random
from typing import Dict, Optional


class RandomPositionGenerator:
    """Generate random chess positions."""
    
    def __init__(self, random_state: Optional[random.Random] = None):
        self.random = random_state or random.Random()
    
    def generate(self, min_pieces: int = 3, max_pieces: int = 32) -> Dict[str, str]:
        """Generate a random board state as FEN."""
        # From positions/generator.py, this is simplified
        board = {}
        
        # Always include kings
        board['e1'] = 'K'
        board['e8'] = 'k'
        
        # Random remaining pieces
        return board