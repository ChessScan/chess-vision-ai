#!/usr/bin/env python3
"""
Example: Programmatic Data Generation
Shows how to build complex generation pipelines using the Python API.
"""

from chess_data_gen import (
    Generator, Config, ExportFormat,
    CameraConfig, LightingConfig, PositionConfig,
    AugmentationConfig, ConstraintConfig
)
from pathlib import Path

def tactical_focused_dataset():
    """Generate a dataset focused on tactical positions."""
    
    config = Config()
    config.name = "tactical_specialist_v1"
    config.random_seed = 2026
    
    # Specialized positions
    config.positions = PositionConfig()
    
    # Load tactical puzzles from curated file
    config.positions.from_file(
        path="data/tactical_puzzles_500.json",
        filter_by="tactical_theme",
        themes=["pin", "fork", "skewer", "discovered_attack"],
        elo_range=(1200, 2200),
        count=100
    )
    
    # Add some random legal for variety
    config.positions.add_random(
        count=30,
        min_pieces=8,
        constraint="at_least_one_tactical_opportunity"
    )
    
    # Camera: focus on realistic phone angles
    config.camera = CameraConfig()
    config.camera.angle(30, 60).distribution("triangular", peak=45)
    config.camera.rotation(0, 360).distribution("uniform")
    config.camera.distance(25, 45).distribution("uniform")
    config.camera.focal_length = 26  # iPhone
    config.camera.depth_of_field(enabled=True, f_stop_range=(2.8, 5.6))
    
    # Add slight camera shake for realism
    config.camera.perturbations(
        tilt=(-3, 3),
        roll=(-2, 2),
        sensor_shift=(-0.5, 0.5)
    )
    
    # Varied lighting
    config.lighting = LightingConfig()
    config.lighting.add_environment(
        name="dramatic_side_light",
        hdri_path="assets/hdri/side_window_4k.hdr",
        key_light_direction=(45, 0),  # angles
        intensity_range=(0.8, 1.2),
        weight=0.4
    )
    config.lighting.add_environment(
        name="tournament_bright",
        hdri_path="assets/hdri/tournament_overhead_4k.hdr",
        intensity_range=(1.0, 1.4),
        weight=0.6
    )
    config.lighting.shadow_softness(0.3, 0.7)
    
    # Standard materials + one custom
    config.materials.board_variants = [
        ("walnut", 0.4),
        ("maple", 0.4),
        ("plastic_green", 0.2)
    ]
    config.materials.piece_variants = [
        ("tournament", 0.7),
        ("classic_wood", 0.3)
    ]
    config.materials.wear_level(0.0, 0.2)
    
    # Aggressive augmentation for robustness
    config.augmentation = AugmentationConfig()
    config.augmentation.sensor_noise(
        probability=0.7,
        intensity_range=(0.01, 0.04)
    )
    config.augmentation.jpeg_artifacts(
        probability=0.5,
        quality_range=(65, 90)
    )
    config.augmentation.color_jitter(
        hue=(-0.12, 0.12),
        saturation=(-0.08, 0.08),
        brightness=(-0.10, 0.10),
        probability=0.4
    )
    config.augmentation.motion_blur(
        probability=0.15,  # Higher for tactical dataset
        kernel_range=(3, 7)
    )
    
    # Constraints
    config.constraints = ConstraintConfig()
    config.constraints.occlusion(
        max_overlap=0.30,
        ensure_variety=True,
        probability=0.25  # More occlusion in tactical positions
    )
    config.constraints.board_rotation(
        enabled=True,
        probability=0.25
    )
    config.constraints.piece_visibility(min_partial=0.60)
    
    # Output
    config.output.resolution = (640, 640)
    config.output.format = ExportFormat.COCO
    
    # Generate
    generator = Generator(config, backend="blender")
    generator.set_progress_callback(lambda p: print(f"Progress: {p.percent:.1f}%"))
    
    dataset = generator.generate(total_images=1000)
    
    # Export
    dataset.split(train=0.8, val=0.1, test=0.1)
    dataset.export("./tactical_dataset/")
    
    # Also export to YOLO format for comparison
    dataset.export("./tactical_dataset_yolo/", format=ExportFormat.YOLO)
    
    # Generate statistics
    stats = dataset.statistics()
    print(f"""
    Dataset Generated: {config.name}
    Total images: {stats.total_images}
    Split: {stats.split_counts}
    Position categories: {stats.category_distribution}
    Avg occlusion: {stats.avg_occlusion:.2f}
    Files: {stats.files_generated}
    """)
    
    return dataset


def resume_interrupted_generation():
    """Resume a generation that was interrupted."""
    
    config = Config.from_yaml("./partial_config.yaml")
    
    generator = Generator(config, backend="blender")
    
    # Resume from checkpoint
    checkpoint_path = "./checkpoints/gen_45723.json"
    
    dataset = generator.resume_from_checkpoint(
        checkpoint_path,
        total_target=50000
    )
    
    dataset.export("./resumed_dataset/")
    
    return dataset


def generate_with_custom_callbacks():
    """Example with custom hooks for each stage."""
    
    config = Config.from_yaml("config.yaml")
    generator = Generator(config, backend="blender")
    
    # Custom pre-render hook
    def on_scene_ready(scene_info):
        """Modify scene before rendering."""
        if random.random() < 0.1:
            # 10% chance: add a coffee cup prop
            scene_info.add_prop("coffee_cup", position="random_off_board")
            print("Added random prop to scene")
    
    # Custom post-render hook
    def on_image_ready(image_info):
        """Process after each render."""
        if image_info.brightness < 50:
            print(f"Warning: Low brightness {image_info.path}")
            image_info.flag_for_review()
    
    generator.on_scene_ready(on_scene_ready)
    generator.on_image_complete(on_image_ready)
    
    dataset = generator.generate(total_images=100)
    return dataset


def benchmark_generation():
    """Benchmark different parameter combinations."""
    
    from chess_data_gen.benchmark import BenchmarkRunner
    
    runner = BenchmarkRunner()
    
    # Test different sample counts
    for samples in [32, 64, 128, 256]:
        config = Config.from_yaml("basic_config.yaml")
        config.rendering.samples = samples
        
        result = runner.bench(
            config=config,
            iterations=10,
            warmup=2
        )
        
        print(f"Samples: {samples}")
        print(f"  Time per render: {result.avg_time:.2f}s")
        print(f"  Memory: {result.peak_memory:.1f}MB")
        print(f"  Quality score: {result.quality_ssim:.3f}")


def generate_small_validation_set():
    """Generate a quick validation set for checking pipeline."""
    
    config = Config()
    config.name = "validation_quick"
    
    # Just 5 positions, 10 variations each
    config.positions.from_fen_list([
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",  # Start
        "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq -",  # Italian
        "8/8/3k4/8/4K3/8/8/8 w - - 0 1",  # King only
        "8/8/8/8/8/8/4k3/4Q3 w - - 0 1",  # Q vs K endgame
        "r1bqk2r/ppp2ppp/2n5/3pp3/1bP5/2N2N2/PPQPPPPP/R1B1KB1R w KQkq -",  # Complex
    ])
    
    config.camera.angle(40, 50).samples(2)
    config.camera.rotation(0, 270).samples(4)
    config.lighting.add_environment("studio_neutral", "assets/hdri/studio.hdr")
    
    config.output.samples = 64  # Fast
    
    generator = Generator(config)
    dataset = generator.generate(total_images=50)  # 5 pos × 10 var
    
    # Quick visual check
    dataset.generate_preview_grid(
        rows=5, cols=10, 
        output="./validation_preview.png"
    )
    
    print(f"Validation set ready: {dataset.path}")
    print(f"Preview saved to: ./validation_preview.png")
    
    return dataset


if __name__ == "__main__":
    # Run the examples
    
    print("=== Example 1: Tactical Focused Dataset ===")
    # tactical_focused_dataset()
    
    print("\n=== Example 2: Resume from Checkpoint ===")
    # resume_interrupted_generation()
    
    print("\n=== Example 3: Custom Callbacks ===")
    # generate_with_custom_callbacks()
    
    print("\n=== Example 4: Benchmark ===")
    # benchmark_generation()
    
    print("\n=== Example 5: Quick Validation ===")
    generate_small_validation_set()