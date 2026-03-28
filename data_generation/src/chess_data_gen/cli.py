#!/usr/bin/env python3
"""
CLI for chess data generation.

Usage:
    # Generate from config file
    python -m chess_data_gen.cli --config examples/basic_generation.yaml --output ./dataset/
    
    # Generate specific count
    python -m chess_data_gen.cli --config config.yaml --count 100 --output ./output/
    
    # Resume from checkpoint
    python -m chess_data_gen.cli --config config.yaml --resume checkpoint_000100.json
    
    # Validate config
    python -m chess_data_gen.cli --config config.yaml --validate
"""

import argparse
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from chess_data_gen.config import Config, ExportFormat
from chess_data_gen.generator import Generator, GenerationProgress


def validate_config(config_path: Path) -> bool:
    """Validate configuration file."""
    print(f"Validating config: {config_path}")
    
    try:
        config = Config.from_yaml(config_path)
        errors = config.validate()
        
        if errors:
            print("\nValidation errors:")
            for error in errors:
                print(f"  ✗ {error}")
            return False
        else:
            print("\n✓ Configuration is valid")
            
            # Print summary
            print(f"\nConfiguration Summary:")
            print(f"  Name: {config.name}")
            print(f"  Total images: {config.generation.get('total_images', 'N/A')}")
            print(f"  Positions: {config.positions.count}")
            print(f"  Resolution: {config.output.resolution}")
            print(f"  Export format: {config.output.format.value}")
            print(f"  Asset root: {config.asset_root}")
            
            return True
            
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False


def generate_dataset(config_path: Path, output_dir: Path, count: int = None,
                    checkpoint: Path = None):
    """Generate dataset from configuration."""
    
    print(f"Loading configuration: {config_path}")
    config = Config.from_yaml(config_path)
    
    # Override output directory if specified
    if output_dir:
        config.output_dir = str(output_dir)
    
    # Override count if specified
    if count:
        config.generation['total_images'] = count
    
    print(f"\nDataset Configuration:")
    print(f"  Name: {config.name}")
    print(f"  Total images: {config.generation.get('total_images', 1000)}")
    print(f"  Output: {config.output_dir}")
    print(f"  Backend: blender")
    
    print(f"\n{'='*50}")
    print("Starting generation...")
    print(f"{'='*50}\n")
    
    # Create generator
    generator = Generator(config, backend="blender")
    
    # Set up progress callback
    def on_progress(progress: GenerationProgress):
        bar_width = 30
        filled = int(bar_width * progress.percent / 100)
        bar = '█' * filled + '░' * (bar_width - filled)
        
        elapsed_mins = int(progress.elapsed_seconds // 60)
        elapsed_secs = int(progress.elapsed_seconds % 60)
        
        eta_mins = int(progress.estimated_remaining_seconds // 60)
        eta_secs = int(progress.estimated_remaining_seconds % 60)
        
        print(f"\r[{bar}] {progress.percent:.1f}% | "
              f"{progress.current}/{progress.total} | "
              f"Elapsed: {elapsed_mins}:{elapsed_secs:02d} | "
              f"ETA: {eta_mins}:{eta_secs:02d}", end='', flush=True)
    
    generator.set_progress_callback(on_progress)
    
    try:
        # Generate or resume
        if checkpoint:
            print(f"Resuming from: {checkpoint}")
            total = config.generation.get('total_images', 1000)
            dataset = generator.resume_from_checkpoint(checkpoint, total)
        else:
            dataset = generator.generate(
                total_images=config.generation.get('total_images')
            )
        
        print("\n\n" + "="*50)
        print("Exporting dataset...")
        print("="*50)
        
        # Split and export
        split_config = config.generation.get('distribution', {'train': 0.8, 'val': 0.1, 'test': 0.1})
        dataset.split(
            train=split_config.get('train', 0.8),
            val=split_config.get('val', 0.1),
            test=split_config.get('test', 0.1)
        )
        
        # Export all formats
        formats = [config.output.format] + config.output.additional_formats
        
        for fmt in formats:
            print(f"\nExporting to {fmt.value}...")
            dataset.export(Path(config.output_dir), format=fmt)
        
        # Generate statistics
        stats = dataset.statistics()
        print(f"\n{'='*50}")
        print("Dataset Statistics:")
        print(f"{'='*50}")
        print(f"Total samples: {stats['total_samples']}")
        print(f"Total annotations: {stats['total_annotations']}")
        print(f"\nPosition categories:")
        for cat, count in stats['position_categories'].items():
            print(f"  {cat}: {count}")
        print(f"\nPiece distribution:")
        for piece, count in sorted(stats['category_distribution'].items()):
            print(f"  {piece}: {count}")
        
        print(f"\n✓ Dataset generation complete!")
        print(f"Output: {config.output_dir}")
        
    except Exception as e:
        print(f"\n\n✗ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Chess Vision Training Data Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate configuration
  %(prog)s --config config.yaml --validate
  
  # Generate 1000 images
  %(prog)s --config config.yaml --count 1000 --output ./dataset/
  
  # Resume from checkpoint
  %(prog)s --config config.yaml --resume checkpoint_000500.json
        """
    )
    
    parser.add_argument(
        '--config', '-c', 
        type=Path, 
        required=True,
        help='Configuration YAML file'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Output directory (overrides config)'
    )
    
    parser.add_argument(
        '--count', '-n',
        type=int,
        help='Number of images to generate (overrides config)'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate configuration without generating'
    )
    
    parser.add_argument(
        '--resume',
        type=Path,
        help='Resume from checkpoint file'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Validate config exists
    if not args.config.exists():
        print(f"Configuration file not found: {args.config}")
        return 1
    
    # Validate only
    if args.validate:
        success = validate_config(args.config)
        return 0 if success else 1
    
    # Generate
    return generate_dataset(
        config_path=args.config,
        output_dir=args.output,
        count=args.count,
        checkpoint=args.resume
    )


if __name__ == "__main__":
    sys.exit(main())
