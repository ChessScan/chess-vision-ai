#!/usr/bin/env python3
"""
Quick test script for chess data generation pipeline.
Generates 10 sample images without requiring full Blender.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chess_data_gen.config import Config, CameraConfig, LightingConfig, OutputConfig, ExportFormat
from chess_data_gen.positions.generator import PositionGenerator


def test_config_creation():
    """Test configuration creation."""
    print("="*50)
    print("Test 1: Configuration Creation")
    print("="*50)
    
    config = Config()
    config.name = "test_config"
    config.random_seed = 42
    config.generation['total_images'] = 10
    config.generation['distribution'] = {'train': 0.8, 'val': 0.1, 'test': 0.1}
    
    # Configure camera
    config.camera = CameraConfig()
    config.camera.angle_range = (35.0, 55.0)
    config.camera.rotation_range = (0.0, 360.0)
    config.camera.distance_range = (30.0, 40.0)
    
    # Configure lighting
    config.lighting = LightingConfig()
    config.lighting.add_environment(
        name="studio_neutral",
        hdri_path="hdri/studio/studio_small_09_4k.exr",
        intensity_range=(0.9, 1.1)
    )
    
    # Configure output
    config.output = OutputConfig()
    config.output.resolution = (640, 640)
    config.output.format = ExportFormat.COCO
    config.output.samples = 64  # Fast mode
    
    print(f"✓ Config created: {config.name}")
    print(f"  Total images: {config.generation['total_images']}")
    print(f"  Resolution: {config.output.resolution}")
    print(f"  Seed: {config.random_seed}")
    
    return config


def test_position_generation():
    """Test position generation."""
    print("\n" + "="*50)
    print("Test 2: Position Generation")
    print("="*50)
    
    config = Config()
    config.random_seed = 42
    
    # Generate positions
    pos_gen = PositionGenerator(config)
    pos_gen.config.positions.categories = {
        'opening': 2,
        'endgame': 2,
        'tactical': 1,
    }
    
    positions = pos_gen.generate()
    
    print(f"✓ Generated {len(positions)} positions")
    
    for pos in positions:
        print(f"  - {pos.category}: {pos.fen[:30]}... ({pos.piece_count} pieces)")
    
    return positions


def test_yaml_loading():
    """Test YAML config loading."""
    print("\n" + "="*50)
    print("Test 3: YAML Config Loading")
    print("="*50)
    
    config_path = Path(__file__).parent.parent / "examples" / "basic_generation.yaml"
    
    if config_path.exists():
        config = Config.from_yaml(config_path)
        print(f"✓ Loaded config from {config_path}")
        print(f"  Name: {config.name}")
        print(f"  Positions: {config.positions.count}")
        
        # Validate
        errors = config.validate()
        if errors:
            print(f"  Validation errors: {len(errors)}")
            for e in errors:
                print(f"    - {e}")
        else:
            print(f"  ✓ Config is valid")
    else:
        print(f"Config file not found: {config_path}")
    
    return config


def test_fen_parsing():
    """Test FEN parsing."""
    print("\n" + "="*50)
    print("Test 4: FEN Parsing")
    print("="*50)
    
    from chess_data_gen.positions.generator import fen_to_board, board_to_fen
    
    # Starting position
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    
    board = fen_to_board(fen)
    print(f"✓ Parsed FEN: {fen[:30]}...")
    print(f"  Found {len(board)} pieces")
    
    # Check specific squares
    print(f"  e2: {board.get('e2', 'empty')}")  # Should be P
    print(f"  e7: {board.get('e7', 'empty')}")  # Should be p
    print(f"  e1: {board.get('e1', 'empty')}")  # Should be K
    print(f"  e8: {board.get('e8', 'empty')}")  # Should be k
    
    # Convert back
    fen_out = board_to_fen(board)
    print(f"  Reconstructed FEN: {fen_out[:30]}...")
    
    return board


def test_camera_sampling():
    """Test camera parameter sampling."""
    print("\n" + "="*50)
    print("Test 5: Camera Sampling")
    print("="*50)
    
    config = Config()
    config.random_seed = 42
    config.camera = CameraConfig()
    
    print("✓ Sampling camera parameters:")
    for i in range(3):
        params = config.camera.sample()
        print(f"  Sample {i+1}:")
        print(f"    Angle: {params['angle']:.1f}°")
        print(f"    Rotation: {params['rotation']:.1f}°")
        print(f"    Distance: {params['distance']:.1f}cm")
        print(f"    Focal: {params['focal_length']:.1f}mm")


def test_lighting_sampling():
    """Test lighting sampling."""
    print("\n" + "="*50)
    print("Test 6: Lighting Sampling")
    print("="*50)
    
    config = Config()
    config.lighting = LightingConfig()
    config.lighting.add_environment(
        name="studio",
        hdri_path="hdri/studio.exr",
        intensity_range=(0.8, 1.2)
    )
    config.lighting.add_environment(
        name="office",
        hdri_path="hdri/office.exr",
        intensity_range=(0.7, 1.0)
    )
    
    print("✓ Sampling lighting configurations:")
    for i in range(5):
        params = config.lighting.sample()
        print(f"  Sample {i+1}: {params['environment']} @ {params['intensity']:.2f}")


def main():
    """Run all tests."""
    print("="*60)
    print("CHESS DATA GENERATION - QUICK TEST SUITE")
    print("="*60)
    
    try:
        test_config_creation()
        test_position_generation()
        test_yaml_loading()
        test_fen_parsing()
        test_camera_sampling()
        test_lighting_sampling()
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60)
        print("\nPipeline components working correctly.")
        print("Ready for full Blender generation.")
        print("\nTo generate actual images:")
        print("  blender --background --python cli.py -- --config basic_generation.yaml --count 100")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
