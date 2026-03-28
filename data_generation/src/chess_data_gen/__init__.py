"""
Chess Vision Data Generation

A complete pipeline for generating synthetic chess training data using Blender.

Usage:
    from chess_data_gen import Generator, Config
    
    config = Config.from_yaml("config.yaml")
    generator = Generator(config, backend="blender")
    dataset = generator.generate(count=1000)
    dataset.export("./output/", format="coco")
"""

__version__ = "0.1.0"
__author__ = "Chess Vision Team"

from .config import Config, CameraConfig, LightingConfig, PositionConfig, OutputConfig
from .generator import Generator
from .dataset import Dataset

__all__ = [
    'Config',
    'CameraConfig', 
    'LightingConfig',
    'PositionConfig',
    'OutputConfig',
    'Generator',
    'Dataset',
]