#!/usr/bin/env python3
"""Chess Board Image Generator

Generates synthetic chess board images using Blender for AI training.
"""

import bpy
import math
import random
import os
from typing import Dict, List, Tuple
import yaml


class ChessBoardGenerator:
    """Generates chess board images with configurable properties."""
    
    def __init__(self, config_path: str = "/workspace/config/styles.yaml"):
        """Initialize generator with configuration."""
        self.config = self._load_config(config_path)
        self.clean_scene()
        
    def _load_config(self, path: str) -> Dict:
        """Load YAML configuration."""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return self._default_config()
    
    def _default_config(self) -> Dict:
        """Return default configuration."""
        return {
            "board_sizes": [8],
            "piece_styles": ["classic"],
            "board_materials": ["wood_oak", "marble_white"],
            "lighting_setups": ["studio_even", "studio_dramatic"]
        }
    
    def clean_scene(self):
        """Remove all objects from current scene."""
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        
    def create_board(self, material_type: str = "wood_oak") -> bpy.types.Object:
        """Create the chess board (8x8 squares)."""
        # Create base board
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
        board = bpy.context.active_object
        board.name = "ChessBoard_Base"
        board.scale = (4, 4, 0.1)
        
        # Create squares
        squares = []
        for row in range(8):
            for col in range(8):
                is_dark = (row + col) % 2 == 1
                x = (col - 3.5) * 0.5
                y = (3.5 - row) * 0.5
                z = 0.051
                
                bpy.ops.mesh.primitive_cube_add(size=0.5, location=(x, y, z))
                square = bpy.context.active_object
                square.name = f"Square_{row}{col}"
                
                # Assign material
                if is_dark:
                    square.data.materials.append(self._get_material("dark_square"))
                else:
                    square.data.materials.append(self._get_material("light_square"))
                    
                squares.append(square)
        
        return board
    
    def create_piece(self, piece_type: str, color: str, position: Tuple[float, float, float]) -> bpy.types.Object:
        """Create a chess piece."""
        # For now, use simple placeholder geometry
        # In full version, load actual 3D models
        bpy.ops.mesh.primitive_cube_add(size=0.4, location=position)
        piece = bpy.context.active_object
        piece.name = f"{color}_{piece_type}"
        piece.scale.z = 1.5
        
        # Add material
        piece.data.materials.append(self._get_material(f"{color}_piece"))
        
        return piece
    
    def place_pieces_from_fen(self, fen: str):
        """Place pieces according to FEN notation."""
        # FEN: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR
        rows = fen.split()[0].split('/')
        
        piece_map = {
            'r': 'rook', 'n': 'knight', 'b': 'bishop', 'q': 'queen',
            'k': 'king', 'p': 'pawn',
            'R': 'rook', 'N': 'knight', 'B': 'bishop', 'Q': 'queen',
            'K': 'king', 'P': 'pawn'
        }
        
        for row_idx, row in enumerate(rows):
            col_idx = 0
            for char in row:
                if char.isdigit():
                    col_idx += int(char)
                else:
                    piece_type = piece_map[char]
                    color = 'black' if char.islower() else 'white'
                    x = (col_idx - 3.5) * 0.5
                    y = (3.5 - row_idx) * 0.5
                    z = 0.3
                    self.create_piece(piece_type, color, (x, y, z))
                    col_idx += 1
    
    def setup_camera(self, angle_preset: str = "medium"):
        """Setup camera with preset angle."""
        # Remove default camera
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.select_by_type(type='CAMERA')
        bpy.ops.object.delete()
        
        # Create new camera
        bpy.ops.object.camera_add(location=(0, 0, 5))
        camera = bpy.context.active_object
        camera.name = "Camera"
        
        # Set camera parameters based on preset
        angles = {
            "top_down": {"location": (0, 0, 6), "rotation": (0, 0, 0)},
            "medium": {"location": (2, -2, 4), "rotation": (0.7, 0, 0.8)},
            "low": {"location": (3, -3, 2), "rotation": (1.1, 0, 0.9)},
            "shallow": {"location": (3.5, -3.5, 1), "rotation": (1.4, 0, 0.8)}
        }
        
        preset = angles.get(angle_preset, angles["medium"])
        camera.location = preset["location"]
        camera.rotation_euler = preset["rotation"]
        
        # Point to board center
        direction = (0, 0, 0)
        camera.rotation_euler = (
            camera.location,
            direction,
            (0, 0, 1)
        )
        
        bpy.context.scene.camera = camera
    
    def setup_lighting(self, preset: str = "studio_even"):
        """Setup lighting configuration."""
        # Clear existing lights
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.select_by_type(type='LIGHT')
        bpy.ops.object.delete()
        
        if preset == "studio_even":
            # Three-point lighting
            self._create_light("Key", (5, -5, 5), 1000)
            self._create_light("Fill", (-3, -3, 4), 500)
            self._create_light("Back", (0, 5, 3), 300)
        elif preset == "studio_dramatic":
            self._create_light("Key", (3, -3, 5), 1500)
            self._create_light("Rim", (-2, 1, 2), 800)
        elif preset == "natural":
            self._create_light("Sun", (2, -2, 8), 1200)
    
    def _create_light(self, name: str, location: Tuple[float, float, float], energy: float):
        """Create a point light."""
        bpy.ops.object.light_add(type='POINT', location=location)
        light = bpy.context.active_object
        light.name = name
        light.data.energy = energy
    
    def _get_material(self, name: str) -> bpy.types.Material:
        """Get or create a material."""
        if name in bpy.data.materials:
            return bpy.data.materials[name]
        
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        
        # Configure based on material type
        if "dark_square" in name:
            self._setup_wood_material(mat, (0.15, 0.08, 0.04, 1))
        elif "light_square" in name:
            self._setup_wood_material(mat, (0.8, 0.65, 0.4, 1))
        elif "white_piece" in name:
            self._setup_piece_material(mat, (0.95, 0.95, 0.92, 1))
        elif "black_piece" in name:
            self._setup_piece_material(mat, (0.1, 0.1, 0.12, 1))
        
        return mat
    
    def _setup_wood_material(self, mat: bpy.types.Material, color: Tuple):
        """Configure wood-like material."""
        nodes = mat.node_tree.nodes
        nodes.clear()
        
        # Add shader nodes
        output = nodes.new('ShaderNodeOutputMaterial')
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        
        principled.inputs['Base Color'].default_value = color
        principled.inputs['Roughness'].default_value = 0.7
        
        mat.node_tree.links.new(principled.outputs[0], output.inputs[0])
    
    def _setup_piece_material(self, mat: bpy.types.Material, color: Tuple):
        """Configure piece material (plastic/resin)."""
        nodes = mat.node_tree.nodes
        nodes.clear()
        
        output = nodes.new('ShaderNodeOutputMaterial')
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        
        principled.inputs['Base Color'].default_value = color
        principled.inputs['Roughness'].default_value = 0.2
        principled.inputs['Subsurface'].default_value = 0.1
        
        mat.node_tree.links.new(principled.outputs[0], output.inputs[0])
    
    def render(self, output_path: str, resolution: Tuple[int, int] = (640, 480)):
        """Render the scene to image file."""
        # Configure render settings
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.render.resolution_x = resolution[0]
        bpy.context.scene.render.resolution_y = resolution[1]
        bpy.context.scene.render.filepath = output_path
        bpy.context.scene.render.image_settings.file_format = 'PNG'
        
        # Render
        bpy.ops.render.render(write_still=True)
    
    def generate_dataset_entry(self, output_dir: str, fen: str = None, 
                               camera_angle: str = "medium", index: int = 0) -> Dict:
        """Generate a single dataset entry."""
        # Generate random FEN if not provided
        if fen is None:
            fen = self._generate_random_fen()
        
        # Create scene
        self.clean_scene()
        self.create_board()
        self.place_pieces_from_fen(fen)
        self.setup_camera(camera_angle)
        self.setup_lighting(random.choice(["studio_even", "studio_dramatic", "natural"]))
        
        # Render
        img_path = os.path.join(output_dir, "images", f"chess_{index:06d}.png")
        self.render(img_path)
        
        # Return metadata
        return {
            "image": img_path,
            "fen": fen,
            "camera_angle": camera_angle,
            "lighting": "random",
            "index": index
        }
    
    def _generate_random_fen(self) -> str:
        """Generate a random valid chess position FEN."""
        # For now, return starting position
        # In production: use python-chess library
        return "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", "-o", default="/workspace/output")
    parser.add_argument("--count", "-n", type=int, default=10)
    parser.add_argument("--resolution", type=str, default="640x480")
    args = parser.parse_args()
    
    # Parse resolution
    res = tuple(map(int, args.resolution.split("x")))
    
    # Generate
    generator = ChessBoardGenerator()
    os.makedirs(os.path.join(args.output, "images"), exist_ok=True)
    os.makedirs(os.path.join(args.output, "labels"), exist_ok=True)
    
    for i in range(args.count):
        print(f"Generating image {i+1}/{args.count}...")
        metadata = generator.generate_dataset_entry(
            args.output,
            index=i,
            resolution=res
        )
        print(f"  Saved: {metadata['image']}")
    
    print("Dataset generation complete!")
