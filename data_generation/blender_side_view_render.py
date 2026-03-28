#!/usr/bin/env python3
"""
Blender Chess Renderer - Side View (Phone Perspective)

Designed to run INSIDE Blender:
    blender --background --python blender_side_view_render.py -- <args>

Generates photorealistic chess images from phone-propped-up perspective:
- Camera angle: 30-60° from horizontal (side view)
- Distance: 25-45cm from board center
- iPhone perspective: 26mm focal length
- Cycles ray-tracing with HDRI lighting
"""

import sys
import argparse
import json
import math
import random
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional

# Blender imports (only available when running in Blender)
try:
    import bpy
    import bmesh
    from mathutils import Vector, Matrix, Euler
    from bpy_extras.object_utils import world_to_camera_view
    HAS_BPY = True
except ImportError:
    HAS_BPY = False
    print("ERROR: This script must be run inside Blender")
    print("Usage: blender --background --python blender_side_view_render.py -- --count 10")
    sys.exit(1)


@dataclass
class CameraParams:
    """Camera configuration for phone perspective."""
    angle: float = 45.0        # Degrees from horizontal (30-60°)
    rotation: float = 120.0    # Degrees around board (0-360°)
    distance: float = 35.0     # cm from board center
    focal_length: float = 26.0 # mm (iPhone standard)
    tilt: float = 0.0          # Small random tilt
    roll: float = 0.0          # Small random roll


@dataclass
class RenderResult:
    """Result of a single render."""
    image_path: Path
    annotations: List[Dict]
    camera_params: Dict
    position_fen: str
    metadata: Dict


class ChessSceneBuilder:
    """Builds chess scene in Blender with proper materials and lighting."""
    
    def __init__(self, assets_dir: Path):
        self.assets_dir = Path(assets_dir)
        self.scene = bpy.context.scene
        self.camera = None
        self.board = None
        self.pieces = []
        
        # Clear scene
        self._clear_scene()
        
        # Create collections
        self.board_collection = bpy.data.collections.new("Board")
        self.pieces_collection = bpy.data.collections.new("Pieces")
        self.scene.collection.children.link(self.board_collection)
        self.scene.collection.children.link(self.pieces_collection)
    
    def _clear_scene(self):
        """Remove all objects from scene."""
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        
        # Clean up materials and meshes
        for material in bpy.data.materials:
            if material.users == 0:
                bpy.data.materials.remove(material)
        for mesh in bpy.data.meshes:
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)
    
    def setup_environment(self, hdri_path: Optional[Path] = None, intensity: float = 1.0):
        """Set up HDRI environment lighting."""
        world = self.scene.world
        world.use_nodes = True
        nodes = world.node_tree.nodes
        links = world.node_tree.links
        nodes.clear()
        
        # Background shader
        background = nodes.new('ShaderNodeBackground')
        output = nodes.new('ShaderNodeOutputWorld')
        
        # HDRI or fallback
        if hdri_path and hdri_path.exists():
            try:
                env_tex = nodes.new('ShaderNodeTexEnvironment')
                env_tex.image = bpy.data.images.load(str(hdri_path))
                links.new(env_tex.outputs['Color'], background.inputs['Color'])
            except:
                background.inputs['Color'].default_value = (0.6, 0.6, 0.7, 1.0)
        else:
            background.inputs['Color'].default_value = (0.6, 0.6, 0.7, 1.0)
        
        background.inputs['Strength'].default_value = intensity
        links.new(background.outputs['Background'], output.inputs['Surface'])
        
        # Add sun lamp for shadows
        bpy.ops.object.light_add(type='SUN', location=(5, 5, 8))
        sun = bpy.context.active_object
        sun.data.energy = 3.0
        sun.rotation_euler = (0.5, 0.3, 0.8)
    
    def load_board(self, board_type: str = "walnut_4k"):
        """Load chess board with proper materials."""
        board_path = self.assets_dir / "boards" / board_type / "board.obj"
        
        if not board_path.exists():
            raise FileNotFoundError(f"Board not found: {board_path}")
        
        # Import board (Blender 5.0+ compatible)
        try:
            bpy.ops.wm.obj_import(filepath=str(board_path))
        except:
            bpy.ops.import_scene.obj(filepath=str(board_path))
        
        # Get imported object
        self.board = bpy.context.selected_objects[0]
        self.board.name = "ChessBoard"
        
        # Move to board collection
        for coll in self.board.users_collection:
            coll.objects.unlink(self.board)
        self.board_collection.objects.link(self.board)
        
        print(f"✓ Loaded board: {board_type}")
    
    def load_piece(self, piece_type: str, color: str, square: str, 
                   piece_set: str = "set_02_tournament"):
        """Load and position a chess piece."""
        piece_path = self.assets_dir / "pieces" / piece_set / color.lower() / f"{piece_type}.obj"
        
        if not piece_path.exists():
            print(f"Warning: Piece not found: {piece_path}")
            return None
        
        # Import piece (Blender 5.0+ compatible)
        try:
            bpy.ops.wm.obj_import(filepath=str(piece_path))
        except:
            bpy.ops.import_scene.obj(filepath=str(piece_path))
        piece = bpy.context.selected_objects[0]
        piece.name = f"{color}_{piece_type}_{square}"
        
        # Calculate position
        x, y = self._square_to_coords(square)
        piece.location = (x, y, 0.025)  # On board surface
        
        # Move to pieces collection
        for coll in piece.users_collection:
            coll.objects.unlink(piece)
        self.pieces_collection.objects.link(piece)
        
        return piece
    
    def _square_to_coords(self, square: str) -> Tuple[float, float]:
        """Convert chess square to world coordinates (meters)."""
        file_idx = ord(square[0]) - ord('a')  # 0-7
        rank_idx = int(square[1]) - 1  # 0-7
        
        square_size = 0.057  # 5.7cm = tournament standard
        
        x = (file_idx - 3.5) * square_size
        y = (rank_idx - 3.5) * square_size
        
        return (x, y)
    
    def place_pieces_from_fen(self, fen: str, piece_set: str = "set_02_tournament"):
        """Place pieces according to FEN notation."""
        # Parse FEN board state
        board_part = fen.split()[0]
        ranks = board_part.split('/')
        
        piece_names = {
            'K': 'king', 'Q': 'queen', 'R': 'rook',
            'B': 'bishop', 'N': 'knight', 'P': 'pawn'
        }
        
        for rank_idx, rank in enumerate(ranks):
            file_idx = 0
            for char in rank:
                if char.isdigit():
                    file_idx += int(char)
                else:
                    square = chr(ord('a') + file_idx) + str(8 - rank_idx)
                    color = 'white' if char.isupper() else 'black'
                    piece_type = piece_names.get(char.upper(), 'pawn')
                    
                    self.load_piece(piece_type, color, square, piece_set)
                    file_idx += 1
        
        print(f"✓ Placed pieces from FEN: {fen[:40]}...")
    
    def setup_camera(self, params: CameraParams):
        """Set up camera for phone perspective."""
        # Create camera
        bpy.ops.object.camera_add()
        self.camera = bpy.context.active_object
        self.camera.name = "PhoneCamera"
        
        # Calculate camera position
        angle_rad = math.radians(params.angle)
        rotation_rad = math.radians(params.rotation)
        distance_m = params.distance / 100.0  # Convert cm to meters
        
        # Position in spherical coordinates
        x = distance_m * math.cos(angle_rad) * math.cos(rotation_rad)
        y = distance_m * math.cos(angle_rad) * math.sin(rotation_rad)
        z = distance_m * math.sin(angle_rad)
        
        self.camera.location = (x, y, z)
        
        # Point at board center
        direction = Vector((0, 0, 0)) - self.camera.location
        rot_quat = direction.to_track_quat('-Z', 'Y')
        self.camera.rotation_euler = rot_quat.to_euler()
        
        # Add small random tilt/roll for realism
        euler = self.camera.rotation_euler
        euler.x += math.radians(params.tilt)
        euler.z += math.radians(params.roll)
        
        # Camera settings (iPhone-like)
        self.camera.data.lens = params.focal_length
        self.camera.data.sensor_width = 36
        
        # Set as active camera
        self.scene.camera = self.camera
        
        print(f"✓ Camera: {params.distance:.0f}cm, {params.angle:.0f}°, {params.rotation:.0f}° rotation")
    
    def get_ground_truth_annotations(self) -> List[Dict]:
        """Calculate 2D bounding boxes for all pieces."""
        if not self.camera:
            return []
        
        annotations = []
        scene = self.scene
        render = scene.render
        
        for obj in self.pieces_collection.objects:
            if obj.type != 'MESH':
                continue
            
            # Get bounding box in world space
            bbox_corners = [obj.matrix_world @ Vector(corner) 
                          for corner in obj.bound_box]
            
            # Project to camera space
            min_x, min_y = float('inf'), float('inf')
            max_x, max_y = float('-inf'), float('-inf')
            
            for corner in bbox_corners:
                coord = world_to_camera_view(scene, self.camera, corner)
                x, y = coord.x, coord.y
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)
            
            # Convert to pixel coordinates
            img_w, img_h = render.resolution_x, render.resolution_y
            
            bbox_x = min_x * img_w
            bbox_y = (1 - max_y) * img_h  # Flip Y
            bbox_w = (max_x - min_x) * img_w
            bbox_h = (max_y - min_y) * img_h
            
            # Parse object name: "{color}_{type}_{square}"
            parts = obj.name.split('_')
            if len(parts) >= 3:
                color = parts[0]
                piece_type = parts[1]
                square = parts[2]
                
                annotations.append({
                    'class': f"{color}_{piece_type}",
                    'square': square,
                    'bbox': [round(bbox_x, 2), round(bbox_y, 2), 
                            round(bbox_w, 2), round(bbox_h, 2)],
                    'area': round(bbox_w * bbox_h, 2),
                    'occlusion': 1.0
                })
        
        return annotations
    
    def render(self, output_path: Path, samples: int = 256):
        """Render scene to image file."""
        render = self.scene.render
        
        # Configure Cycles
        render.engine = 'CYCLES'
        render.resolution_x = 640
        render.resolution_y = 640
        render.resolution_percentage = 100
        
        # Cycles settings
        self.scene.cycles.samples = samples
        self.scene.cycles.use_denoising = True
        self.scene.cycles.device = 'CPU'  # Change to 'GPU' if available
        
        # Output
        render.filepath = str(output_path)
        render.image_settings.file_format = 'PNG'
        render.image_settings.color_mode = 'RGB'
        render.image_settings.compression = 90
        
        # Render
        print(f"Rendering to: {output_path}")
        bpy.ops.render.render(write_still=True)
        
        return output_path
    
    def clear_pieces(self):
        """Remove all pieces, keep board."""
        for obj in list(self.pieces_collection.objects):
            bpy.data.objects.remove(obj, do_unlink=True)


def generate_single_render(scene_builder: ChessSceneBuilder, 
                          fen: str,
                          output_path: Path,
                          hdri_path: Optional[Path] = None) -> RenderResult:
    """Generate a single render with annotations."""
    
    # Random camera parameters (phone perspective)
    cam_params = CameraParams(
        angle=random.uniform(35.0, 55.0),       # 35-55° from horizontal
        rotation=random.uniform(0.0, 360.0),    # Full circle
        distance=random.uniform(30.0, 40.0),    # 30-40cm distance
        focal_length=26.0,
        tilt=random.uniform(-2.0, 2.0),         # Slight random tilt
        roll=random.uniform(-1.0, 1.0)          # Slight random roll
    )
    
    # HDRI intensity
    intensity = random.uniform(0.8, 1.2)
    
    # Build scene
    if not scene_builder.board:
        scene_builder.load_board("walnut_4k")
    
    scene_builder.setup_environment(hdri_path, intensity)
    scene_builder.place_pieces_from_fen(fen)
    scene_builder.setup_camera(cam_params)
    
    # Get annotations before render
    annotations = scene_builder.get_ground_truth_annotations()
    
    # Render
    scene_builder.render(output_path, samples=128)
    
    # Result
    result = RenderResult(
        image_path=output_path,
        annotations=annotations,
        camera_params=asdict(cam_params),
        position_fen=fen,
        metadata={
            'hdri_intensity': intensity,
            'piece_count': len(annotations),
            'render_engine': 'Cycles',
            'samples': 128
        }
    )
    
    # Clear for next render
    scene_builder.clear_pieces()
    
    return result


def main():
    parser = argparse.ArgumentParser(description='Chess Vision Blender Renderer')
    parser.add_argument('--count', type=int, default=1, help='Number of renders')
    parser.add_argument('--output', type=str, default='./renders/', help='Output directory')
    parser.add_argument('--assets', type=str, default='./assets/', help='Assets directory')
    parser.add_argument('--samples', type=int, default=128, help='Render samples')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    
    print("="*60)
    print("Chess Vision - Blender Side View Renderer")
    print("="*60)
    
    # Paths
    assets_dir = Path(args.assets)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create scene builder
    print("\nInitializing scene...")
    builder = ChessSceneBuilder(assets_dir)
    
    # Sample FEN positions
    positions = [
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq -",
        "8/8/3k4/8/4K3/8/8/8 w - - 0 1",
        "rnbqkb1r/ppp2ppp/4pn2/3p4/2PP4/2N2N2/PP2PPPP/R1BQKB1R w KQkq -",
        "r2qkb1r/ppp1pppp/2n2n2/3p1b2/3P1B2/2N2N2/PPP1PPPP/R2QKB1R w KQkq -",
    ]
    
    # Find HDRI
    hdri_paths = list(assets_dir.glob("hdri/**/*.exr")) + list(assets_dir.glob("hdri/**/*.hdr"))
    hdri_path = hdri_paths[0] if hdri_paths else None
    
    if hdri_path:
        print(f"✓ HDRI found: {hdri_path}")
    else:
        print("⚠ No HDRI found, using solid color background")
    
    # Generate renders
    results = []
    
    print(f"\nGenerating {args.count} renders...")
    print("-"*60)
    
    for i in range(args.count):
        fen = random.choice(positions)
        output_file = output_dir / f"chess_render_{i:04d}.png"
        
        try:
            result = generate_single_render(builder, fen, output_file, hdri_path)
            results.append(result)
            print(f"  ✓ Render {i+1}/{args.count}: {output_file.name} "
                  f"({len(result.annotations)} pieces)")
        except Exception as e:
            print(f"  ✗ Render {i+1}/{args.count} failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Save annotations
    annotations_file = output_dir / "annotations.json"
    with open(annotations_file, 'w') as f:
        json.dump([{
            'image': str(r.image_path),
            'position': r.position_fen,
            'camera': r.camera_params,
            'annotations': r.annotations,
            'metadata': r.metadata
        } for r in results], f, indent=2)
    
    print("\n" + "="*60)
    print("Generation Complete!")
    print("="*60)
    print(f"\nGenerated: {len(results)} images")
    print(f"Output directory: {output_dir}")
    print(f"Annotations: {annotations_file}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
