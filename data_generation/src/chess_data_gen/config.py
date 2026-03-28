"""
Configuration system for chess data generation.
Supports YAML/JSON loading and programmatic construction.
"""

import json
import random
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple, Union, Any
from enum import Enum

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None


class ExportFormat(Enum):
    """Supported export formats."""
    COCO = "coco"
    YOLO = "yolo"
    TFRECORD = "tfrecord"
    VOC = "pascal_voc"


@dataclass
class CameraConfig:
    """Camera parameter configuration."""
    
    # Angle from horizontal (30-60 degrees)
    angle_range: Tuple[float, float] = (30.0, 60.0)
    angle_distribution: str = "uniform"  # uniform, triangular, normal
    angle_peak: Optional[float] = 45.0  # For triangular distribution
    
    # Rotation around board center (0-360 degrees)
    rotation_range: Tuple[float, float] = (0.0, 360.0)
    rotation_distribution: str = "uniform"
    
    # Distance from board center in cm (25-45cm)
    distance_range: Tuple[float, float] = (25.0, 45.0)
    distance_distribution: str = "uniform"
    
    # Focal length in mm (iPhone standard is 26mm)
    focal_length: float = 26.0
    focal_length_range: Optional[Tuple[float, float]] = (24.0, 28.0)
    
    # Lens distortion (barrel/pincushion)
    lens_distortion_range: Tuple[float, float] = (-0.02, 0.02)
    
    # Depth of field
    depth_of_field: bool = True
    f_stop_range: Tuple[float, float] = (2.8, 5.6)
    focus_variance: float = 0.02
    
    # Camera perturbations (realism)
    tilt_range: Tuple[float, float] = (-3.0, 3.0)  # degrees
    roll_range: Tuple[float, float] = (-2.0, 2.0)  # degrees
    shift_range: Tuple[float, float] = (-0.5, 0.5)  # cm
    
    def sample(self, random_state: Optional[random.Random] = None) -> Dict[str, float]:
        """Sample a random camera configuration."""
        rng = random_state or random.Random()
        
        def sample_range(range_val, dist_type="uniform", peak=None):
            if dist_type == "uniform":
                return rng.uniform(range_val[0], range_val[1])
            elif dist_type == "triangular" and peak is not None:
                return rng.triangular(range_val[0], peak, range_val[1])
            else:
                return rng.uniform(range_val[0], range_val[1])
        
        return {
            'angle': sample_range(self.angle_range, self.angle_distribution, self.angle_peak),
            'rotation': sample_range(self.rotation_range, self.rotation_distribution),
            'distance': sample_range(self.distance_range, self.distance_distribution),
            'focal_length': sample_range(self.focal_length_range) if self.focal_length_range else self.focal_length,
            'lens_distortion': sample_range(self.lens_distortion_range),
            'f_stop': sample_range(self.f_stop_range),
            'tilt': sample_range(self.tilt_range),
            'roll': sample_range(self.roll_range),
            'shift': sample_range(self.shift_range),
        }


@dataclass
class LightingEnvironment:
    """Single lighting environment configuration."""
    name: str
    hdri_path: str
    intensity_range: Tuple[float, float] = (0.8, 1.2)
    color_temp_range: Optional[Tuple[int, int]] = None
    weight: float = 1.0


@dataclass
class LightingConfig:
    """Lighting configuration."""
    
    environments: List[LightingEnvironment] = field(default_factory=list)
    shadow_softness_range: Tuple[float, float] = (0.25, 0.75)
    fill_light_ratio_range: Tuple[float, float] = (0.2, 0.4)
    
    def add_environment(self, name: str, hdri_path: str, 
                       intensity_range: Tuple[float, float] = (0.8, 1.2),
                       color_temp_range: Optional[Tuple[int, int]] = None,
                       weight: float = 1.0):
        """Add a lighting environment."""
        self.environments.append(LightingEnvironment(
            name=name,
            hdri_path=hdri_path,
            intensity_range=intensity_range,
            color_temp_range=color_temp_range,
            weight=weight
        ))
        return self
    
    def sample(self, random_state: Optional[random.Random] = None) -> Dict[str, Any]:
        """Sample a random lighting configuration."""
        rng = random_state or random.Random()
        
        # Weighted random choice of environment
        weights = [env.weight for env in self.environments]
        total = sum(weights)
        r = rng.uniform(0, total)
        cumulative = 0
        selected_env = self.environments[0]
        for env in self.environments:
            cumulative += env.weight
            if r <= cumulative:
                selected_env = env
                break
        
        return {
            'environment': selected_env.name,
            'hdri_path': selected_env.hdri_path,
            'intensity': rng.uniform(*selected_env.intensity_range),
            'color_temp': rng.uniform(*selected_env.color_temp_range) if selected_env.color_temp_range else 5500,
            'shadow_softness': rng.uniform(*self.shadow_softness_range),
            'fill_ratio': rng.uniform(*self.fill_light_ratio_range),
        }


@dataclass
class MaterialVariant:
    """Material variant for pieces or boards."""
    name: str
    path: str
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MaterialConfig:
    """Material configuration."""
    
    board_variants: List[MaterialVariant] = field(default_factory=list)
    piece_variants: List[MaterialVariant] = field(default_factory=list)
    wear_level_range: Tuple[float, float] = (0.0, 0.2)
    piece_scale_variance: Tuple[float, float] = (-0.02, 0.02)
    
    def sample_board(self, random_state: Optional[random.Random] = None) -> MaterialVariant:
        """Sample a board material variant."""
        return self._weighted_choice(self.board_variants, random_state)
    
    def sample_piece(self, random_state: Optional[random.Random] = None) -> MaterialVariant:
        """Sample a piece material variant."""
        return self._weighted_choice(self.piece_variants, random_state)
    
    def _weighted_choice(self, options: List[MaterialVariant], 
                        random_state: Optional[random.Random] = None) -> MaterialVariant:
        """Make a weighted random choice."""
        rng = random_state or random.Random()
        weights = [opt.weight for opt in options]
        total = sum(weights)
        r = rng.uniform(0, total)
        cumulative = 0
        for opt in options:
            cumulative += opt.weight
            if r <= cumulative:
                return opt
        return options[0]


@dataclass
class PositionConfig:
    """Chess position configuration."""
    
    count: int = 130
    categories: Dict[str, int] = field(default_factory=lambda: {
        'opening': 20,
        'middlegame': 40,
        'endgame': 30,
        'tactical': 25,
        'random_legal': 15
    })
    
    constraints: Dict[str, Any] = field(default_factory=lambda: {
        'min_pieces': 3,
        'max_pieces': 32,
        'enforce_kings': True,
    })
    
    def get_category_distribution(self) -> Dict[str, int]:
        """Get the distribution of position categories."""
        return self.categories


@dataclass
class AugmentationConfig:
    """Post-render augmentation configuration."""
    
    sensor_noise: Dict[str, Any] = field(default_factory=lambda: {
        'enabled': True,
        'probability': 0.7,
        'intensity_range': [0.01, 0.04]
    })
    
    jpeg_artifacts: Dict[str, Any] = field(default_factory=lambda: {
        'enabled': True,
        'probability': 0.5,
        'quality_range': [68, 92]
    })
    
    motion_blur: Dict[str, Any] = field(default_factory=lambda: {
        'enabled': True,
        'probability': 0.08,
        'kernel_range': [3, 5]
    })
    
    color_jitter: Dict[str, Any] = field(default_factory=lambda: {
        'enabled': True,
        'hue_range': [-0.12, 0.12],
        'saturation_range': [-0.08, 0.08],
        'brightness_range': [-0.10, 0.10],
        'probability': 0.35
    })


@dataclass
class ConstraintConfig:
    """Generation constraints."""
    
    occlusion: Dict[str, Any] = field(default_factory=lambda: {
        'max_overlap': 0.30,
        'ensure_variety': True,
        'probability': 0.20
    })
    
    board_rotation: Dict[str, Any] = field(default_factory=lambda: {
        'enabled': True,
        'probability': 0.25
    })
    
    piece_visibility: Dict[str, Any] = field(default_factory=lambda: {
        'min_partial': 0.60
    })


@dataclass
class OutputConfig:
    """Output configuration."""
    
    resolution: Tuple[int, int] = (640, 640)
    format: ExportFormat = ExportFormat.COCO
    additional_formats: List[ExportFormat] = field(default_factory=list)
    include_metadata: bool = True
    
    # Render quality
    samples: int = 128
    denoise: bool = True
    color_depth: str = "16bit"
    
    # Parallelization
    parallel: bool = True
    workers: int = 4
    batch_size: int = 100


@dataclass
class Config:
    """Master configuration for chess data generation."""
    
    # Identity
    name: str = "chess_vision_dataset"
    description: str = "Synthetic chess training data"
    version: str = "1.0.0"
    random_seed: int = 42
    
    # Sub-configurations
    generation: Dict[str, Any] = field(default_factory=lambda: {
        'total_images': 130000,
        'distribution': {'train': 0.8, 'val': 0.1, 'test': 0.1}
    })
    
    positions: PositionConfig = field(default_factory=PositionConfig)
    camera: CameraConfig = field(default_factory=CameraConfig)
    lighting: LightingConfig = field(default_factory=LightingConfig)
    materials: MaterialConfig = field(default_factory=MaterialConfig)
    augmentation: AugmentationConfig = field(default_factory=AugmentationConfig)
    constraints: ConstraintConfig = field(default_factory=ConstraintConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    
    # Paths
    asset_root: str = "./assets/"
    output_dir: str = "./output/"
    checkpoint_dir: str = "./checkpoints/"
    
    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> 'Config':
        """Load configuration from YAML file."""
        if not HAS_YAML:
            raise RuntimeError("PyYAML is required. Install with: pip install pyyaml")
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)
    
    @classmethod
    def from_json(cls, path: Union[str, Path]) -> 'Config':
        """Load configuration from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create configuration from dictionary."""
        # Handle nested configs
        config = cls(
            name=data.get('name', 'chess_vision_dataset'),
            description=data.get('description', ''),
            version=data.get('version', '1.0.0'),
            random_seed=data.get('random_seed', 42),
            asset_root=data.get('paths', {}).get('assets', './assets/'),
            output_dir=data.get('paths', {}).get('output', './output/'),
            checkpoint_dir=data.get('paths', {}).get('checkpoint', './checkpoints/'),
        )
        
        # Parse camera config
        if 'camera' in data:
            cam_data = data['camera']
            config.camera = CameraConfig(
                angle_range=tuple(cam_data.get('angle_range', [30, 60])),
                rotation_range=tuple(cam_data.get('rotation_range', [0, 360])),
                distance_range=tuple(cam_data.get('distance_range', [25, 45])),
                focal_length=cam_data.get('focal_length', 26),
            )
        
        # Parse lighting config
        if 'lighting' in data:
            light_data = data['lighting']
            if 'environments' in light_data:
                for env in light_data['environments']:
                    config.lighting.add_environment(
                        name=env['name'],
                        hdri_path=env.get('hdri', env.get('hdri_path')),
                        intensity_range=tuple(env.get('intensity_range', [0.8, 1.2])),
                        weight=env.get('weight', 1.0)
                    )
        
        # Parse output config
        if 'output' in data:
            out_data = data['output']
            config.output = OutputConfig(
                resolution=tuple(out_data.get('resolution', [640, 640])),
                samples=out_data.get('quality', {}).get('samples', 128),
                denoise=out_data.get('quality', {}).get('denoise', True),
            )
        
        return config
    
    def to_yaml(self, path: Union[str, Path]):
        """Save configuration to YAML file."""
        if not HAS_YAML:
            raise RuntimeError("PyYAML is required. Install with: pip install pyyaml")
        with open(path, 'w') as f:
            yaml.dump(asdict(self), f, default_flow_style=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Check asset root exists
        if not Path(self.asset_root).exists():
            errors.append(f"Asset root does not exist: {self.asset_root}")
        
        # Check lighting environments
        if not self.lighting.environments:
            errors.append("No lighting environments configured")
        
        for env in self.lighting.environments:
            hdri_path = Path(self.asset_root) / env.hdri_path
            if not hdri_path.exists():
                errors.append(f"HDRI not found: {hdri_path}")
        
        # Check camera ranges
        if self.camera.angle_range[0] >= self.camera.angle_range[1]:
            errors.append("Camera angle_range invalid")
        
        if self.camera.distance_range[0] >= self.camera.distance_range[1]:
            errors.append("Camera distance_range invalid")
        
        return errors
