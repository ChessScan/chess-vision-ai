"""
Main generator class that orchestrates the data generation pipeline.
"""

import os
import json
import random
from pathlib import Path
from typing import List, Dict, Optional, Callable, Any
from dataclasses import dataclass
import time

from chess_data_gen.config import Config, ExportFormat
from chess_data_gen.positions.generator import PositionGenerator, ChessPosition
from chess_data_gen.dataset import Dataset, DatasetSplit


@dataclass
class GenerationProgress:
    """Progress information for generation."""
    current: int
    total: int
    percent: float
    elapsed_seconds: float
    estimated_remaining_seconds: float
    current_position: Optional[str] = None
    current_status: str = ""


class Generator:
    """Main generator for chess training data."""
    
    def __init__(self, config: Config, backend: str = "blender"):
        self.config = config
        self.backend_name = backend
        self.backend = None
        self.random_state = random.Random(config.random_seed)
        
        # Progress callback
        self.progress_callback: Optional[Callable[[GenerationProgress], None]] = None
        
        # Statistics
        self.stats = {
            'total_renders': 0,
            'successful_renders': 0,
            'failed_renders': 0,
            'start_time': None,
        }
    
    def initialize_backend(self):
        """Initialize the rendering backend."""
        if self.backend_name == "blender":
            try:
                from .blender import BlenderBackend
                self.backend = BlenderBackend()
                print("✓ Blender backend initialized")
            except ImportError as e:
                raise RuntimeError(f"Failed to initialize Blender backend: {e}")
        else:
            raise ValueError(f"Unknown backend: {self.backend_name}")
    
    def set_progress_callback(self, callback: Callable[[GenerationProgress], None]):
        """Set callback for progress updates."""
        self.progress_callback = callback
    
    def generate(self, total_images: Optional[int] = None) -> Dataset:
        """Generate complete dataset."""
        self.stats['start_time'] = time.time()
        
        # Initialize backend
        if self.backend is None:
            self.initialize_backend()
        
        # Generate positions
        print("Generating chess positions...")
        position_gen = PositionGenerator(self.config)
        positions = position_gen.generate()
        
        print(f"Generated {len(positions)} unique positions")
        
        # Calculate variations per position
        if total_images is None:
            total_images = self.config.generation.get('total_images', 1000)
        
        variations_per_position = total_images // len(positions)
        
        # Create output directories
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        (output_dir / "images").mkdir(exist_ok=True)
        (output_dir / "annotations").mkdir(exist_ok=True)
        
        # Generate renders
        dataset = Dataset(config=self.config)
        
        for pos_idx, position in enumerate(positions):
            print(f"\nPosition {pos_idx + 1}/{len(positions)}: {position.category}")
            
            # Generate variations for this position
            for var_idx in range(variations_per_position):
                global_idx = pos_idx * variations_per_position + var_idx
                
                # Report progress
                self._report_progress(global_idx, total_images, position.fen[:20])
                
                # Generate single render
                try:
                    result = self._generate_single(
                        position=position,
                        variation_idx=var_idx,
                        global_idx=global_idx,
                        output_dir=output_dir
                    )
                    
                    if result:
                        dataset.add_sample(result)
                        self.stats['successful_renders'] += 1
                    else:
                        self.stats['failed_renders'] += 1
                        
                except Exception as e:
                    print(f"  ✗ Failed: {e}")
                    self.stats['failed_renders'] += 1
                
                self.stats['total_renders'] += 1
                
                # Save checkpoint periodically
                if global_idx % 100 == 0 and global_idx > 0:
                    self._save_checkpoint(global_idx, dataset)
        
        # Final report
        elapsed = time.time() - self.stats['start_time']
        print(f"\n{'='*50}")
        print(f"Generation Complete!")
        print(f"{'='*50}")
        print(f"Total renders: {self.stats['total_renders']}")
        print(f"Successful: {self.stats['successful_renders']}")
        print(f"Failed: {self.stats['failed_renders']}")
        print(f"Time: {elapsed:.1f}s ({self.stats['total_renders']/elapsed:.2f} renders/sec)")
        
        return dataset
    
    def _generate_single(self, position: ChessPosition, variation_idx: int, 
                         global_idx: int, output_dir: Path) -> Optional[Dict[str, Any]]:
        """Generate a single render."""
        
        # Sample random parameters
        camera_params = self.config.camera.sample(self.random_state)
        lighting_params = self.config.lighting.sample(self.random_state)
        board_material = self.config.materials.sample_board(self.random_state)
        piece_material = self.config.materials.sample_piece(self.random_state)
        
        # Check board rotation (flip 180 for variety)
        board_rotation = 0
        if self.config.constraints.board_rotation.get('enabled', False):
            if self.random_state.random() < self.config.constraints.board_rotation.get('probability', 0.25):
                board_rotation = 180
        
        # Set up scene
        self._setup_scene(
            position=position,
            camera_params=camera_params,
            lighting_params=lighting_params,
            board_material=board_material,
            piece_material=piece_material,
            board_rotation=board_rotation
        )
        
        # Render
        image_filename = f"render_{global_idx:06d}.png"
        image_path = output_dir / "images" / image_filename
        
        self.backend.render_to_file(
            image_path,
            samples=self.config.output.samples
        )
        
        # Get ground truth annotations
        annotations = self.backend.get_ground_truth_annotations()
        
        # Build result
        result = {
            'image_path': str(image_path),
            'image_filename': image_filename,
            'position_fen': position.fen,
            'position_category': position.category,
            'variation_idx': variation_idx,
            'global_idx': global_idx,
            'camera_params': camera_params,
            'lighting_params': {
                'environment': lighting_params['environment'],
                'intensity': lighting_params['intensity'],
            },
            'board_rotation': board_rotation,
            'annotations': [
                {
                    'class': ann.piece_class,
                    'square': ann.square,
                    'bbox': [ann.x, ann.y, ann.width, ann.height],
                    'occlusion': ann.occlusion_ratio,
                }
                for ann in annotations
            ],
        }
        
        # Clean up for next render
        self.backend.clear_pieces()
        
        return result
    
    def _setup_scene(self, position: ChessPosition, camera_params: Dict, 
                     lighting_params: Dict, board_material: Any, 
                     piece_material: Any, board_rotation: float):
        """Set up the complete scene."""
        
        # Load board (only once, or reload if needed)
        asset_root = Path(self.config.asset_root)
        board_path = asset_root / "boards" / board_material.name / "board.obj"
        
        # Note: In a full implementation, we'd cache the board
        self.backend.load_board(board_path, {})
        
        # Load pieces from FEN
        from ..positions.generator import fen_to_board
        board_state = fen_to_board(position.fen)
        
        piece_set = asset_root / "pieces" / "set_01_basic"  # Could vary
        
        for square, piece_char in board_state.items():
            # Determine piece type and color
            if piece_char.isupper():
                color = "white"
            else:
                color = "black"
            
            piece_type = self._piece_char_to_name(piece_char.upper())
            
            self.backend.load_piece(
                piece_type=piece_type,
                color=color,
                square=square,
                piece_set_path=piece_set,
                rotation=board_rotation * 3.14159 / 180 if board_rotation else 0
            )
        
        # Set up camera and lighting
        self.backend.setup_camera(camera_params)
        self.backend.setup_lighting(lighting_params)
    
    def _piece_char_to_name(self, char: str) -> str:
        """Convert piece character to full name."""
        mapping = {
            'K': 'king',
            'Q': 'queen',
            'R': 'rook',
            'B': 'bishop',
            'N': 'knight',
            'P': 'pawn',
        }
        return mapping.get(char, 'pawn')
    
    def _report_progress(self, current: int, total: int, current_position: str):
        """Report generation progress."""
        if self.progress_callback:
            elapsed = time.time() - self.stats['start_time']
            percent = (current / total) * 100
            
            # Estimate remaining
            if current > 0:
                rate = current / elapsed
                remaining = (total - current) / rate
            else:
                remaining = 0
            
            progress = GenerationProgress(
                current=current,
                total=total,
                percent=percent,
                elapsed_seconds=elapsed,
                estimated_remaining_seconds=remaining,
                current_position=current_position,
                current_status=f"Rendering {current}/{total}"
            )
            
            self.progress_callback(progress)
    
    def _save_checkpoint(self, idx: int, dataset: Dataset):
        """Save checkpoint for resuming."""
        checkpoint_dir = Path(self.config.checkpoint_dir)
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        checkpoint_file = checkpoint_dir / f"checkpoint_{idx:06d}.json"
        
        # Save minimal state
        checkpoint = {
            'last_completed_idx': idx,
            'random_state': self.random_state.getstate(),
            'config': self.config.to_dict(),
        }
        
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        print(f"  → Checkpoint saved: {checkpoint_file}")
    
    def resume_from_checkpoint(self, checkpoint_path: Path, total_target: int) -> Dataset:
        """Resume generation from checkpoint."""
        with open(checkpoint_path) as f:
            checkpoint = json.load(f)
        
        # Restore state
        self.random_state.setstate(checkpoint['random_state'])
        start_idx = checkpoint['last_completed_idx'] + 1
        
        print(f"Resuming from checkpoint: {checkpoint_path}")
        print(f"Starting from index: {start_idx}")
        
        # Adjust generation to start from checkpoint
        # ... implementation details ...
        
        return self.generate(total_images=total_target)
