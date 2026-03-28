#!/usr/bin/env python3
"""Batch dataset generation script for chess vision AI.

Generates multiple chess board images with random configurations.
"""

import sys
import os
import json
import random
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, '/workspace/src')

from board_generator import ChessBoardGenerator


def parse_args():
    parser = argparse.ArgumentParser(
        description='Generate chess vision training dataset'
    )
    parser.add_argument('-n', '--count', type=int, default=100,
                        help='Number of images to generate (default: 100)')
    parser.add_argument('-o', '--output', type=str,
                        default='/workspace/dataset',
                        help='Output directory')
    parser.add_argument('--resolution', type=str, default='640x480',
                        help='Image resolution (e.g., 640x480, 1920x1080)')
    parser.add_argument('--config', type=str,
                        default='/workspace/config/styles.yaml',
                        help='Styles configuration file')
    parser.add_argument('--camera-config', type=str,
                        default='/workspace/config/camera_angles.yaml',
                        help='Camera angles configuration')
    parser.add_argument('--validation', action='store_true',
                        help='Generate validation set (20% of count)')
    parser.add_argument('--seed', type=int, default=None,
                        help='Random seed for reproducibility')
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Parse resolution
    width, height = map(int, args.resolution.split('x'))
    resolution = (width, height)
    
    # Setup random seed
    if args.seed is not None:
        random.seed(args.seed)
    
    # Create output directories
    base_dir = Path(args.output)
    train_dir = base_dir / 'train'
    val_dir = base_dir / 'validation' if args.validation else None
    
    for d in [train_dir, val_dir]:
        if d:
            (d / 'images').mkdir(parents=True, exist_ok=True)
            (d / 'labels').mkdir(parents=True, exist_ok=True)
    
    # Initialize generator
    print(f"Initializing generator with config: {args.config}")
    generator = ChessBoardGenerator(
        config_path=args.config,
        camera_config_path=args.camera_config
    )
    
    # Calculate split
    if args.validation:
        val_count = max(1, args.count // 5)
        train_count = args.count - val_count
    else:
        train_count = args.count
        val_count = 0
    
    print(f"\nGenerating {train_count} training images")
    if val_count:
        print(f"Generating {val_count} validation images")
    print(f"Resolution: {width}x{height}")
    print(f"Output: {base_dir}")
    print("=" * 50)
    
    metadata = {
        'train': [],
        'validation': []
    }
    
    # Generate training images
    for i in range(train_count):
        print(f"\nGenerating training image {i+1}/{train_count}...")
        
        entry = generator.generate_dataset_entry(
            output_dir=str(train_dir),
            index=i,
            resolution=resolution
        )
        
        metadata['train'].append(entry)
        print(f"  ✓ Saved: {entry['image']}")
        
        # Save metadata periodically
        if (i + 1) % 10 == 0:
            _save_metadata(base_dir, metadata)
    
    # Generate validation images
    for i in range(val_count):
        print(f"\nGenerating validation image {i+1}/{val_count}...")
        
        entry = generator.generate_dataset_entry(
            output_dir=str(val_dir),
            index=i,
            resolution=resolution
        )
        
        metadata['validation'].append(entry)
        print(f"  ✓ Saved: {entry['image']}")
    
    # Final save
    _save_metadata(base_dir, metadata)
    
    print("\n" + "=" * 50)
    print("Dataset generation complete!")
    print(f"  Training images: {train_count}")
    if val_count:
        print(f"  Validation images: {val_count}")
    print(f"  Total: {args.count}")
    print(f"\nMetadata saved to: {base_dir / 'dataset.json'}")


def _save_metadata(base_dir: Path, metadata: dict):
    """Save dataset metadata to JSON file."""
    meta_path = base_dir / 'dataset.json'
    with open(meta_path, 'w') as f:
        json.dump(metadata, f, indent=2)


if __name__ == '__main__':
    main()
