#!/usr/bin/env python3
"""
Chess Vision - Ultra-Shallow Perspective 3D Renderer
Designed for phone-at-table-edge camera angles (5-25° from horizontal)
Runs inside Blender using real 3D .obj models
"""

import bpy
import bmesh
import math
import random
import json
import argparse
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from mathutils import Vector, Euler
from bpy_extras.object_utils import world_to_camera_view

# Configuration
ASSETS_DIR = Path("/workspace/assets")
OUTPUT_DIR = Path("/workspace/output")

@dataclass 
class CameraConfig:
    """Ultra-shallow camera configuration."""
    # ANGLE FROM HORIZONTAL - this is key for phone-at-table-edge effect
    # 90° = top down, 0° = side view (impossible), 5-25° = realistic phone perspective
    angle_from_horizontal: float = 15.0  # 5-25° range
    
    # Rotation around the board (0-360°)
    azimuth: float = 45.0
    
    # Distance from board center in centimeters
    distance_cm: float = 25.0  # Phone propped ~25cm from board edge
    
    # Camera tilt (hand jitter)
    tilt_degrees: float = 0.0
    
    # Camera roll (phone rotation)
    roll_degrees: float = 0.0
    
    # Focal length (iPhone ~26mm equivalent)
    focal_length_mm: float = 26.0


class ChessScene3D:
    """Full 3D chess scene with procedural pieces or loaded models."""
    
    def __init__(self):
        self.clear_scene()
        self.materials = {}
        self.camera = None
        self.board = None
        self.pieces = []
        
    def clear_scene(self):
        """Remove all objects from scene."""
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        
        # Clean up unused data blocks
        for block in [bpy.data.meshes, bpy.data.materials, bpy.data.images]:
            for item in block:
                if item.users == 0:
                    block.remove(item)
    
    def setup_environment(self, hdri_path: Path = None):
        """Setup HDRI environment lighting."""
        world = bpy.context.scene.world
        world.use_nodes = True
        nodes = world.node_tree.nodes
        links = world.node_tree.links
        nodes.clear()
        
        output = nodes.new('ShaderNodeOutputWorld')
        background = nodes.new('ShaderNodeBackground')
        
        # Load or create HDRI environment
        if hdri_path and hdri_path.exists():
            try:
                env_tex = nodes.new('ShaderNodeTexEnvironment')
                img = bpy.data.images.load(str(hdri_path))
                env_tex.image = img
                links.new(env_tex.outputs['Color'], background.inputs['Color'])
                background.inputs['Strength'].default_value = random.uniform(0.8, 1.5)
            except Exception as e:
                print(f"HDRI load failed: {e}, using fallback")
                background.inputs['Color'].default_value = (0.6, 0.65, 0.7, 1.0)
                background.inputs['Strength'].default_value = 1.0
        else:
            # Fallback - soft blue-gray ambient
            background.inputs['Color'].default_value = (0.6, 0.65, 0.7, 1.0)
            background.inputs['Strength'].default_value = 1.0
        
        links.new(background.outputs['Background'], output.inputs['Surface'])
        
        # Add key light for shadows
        key_light = self._create_light("Key", (3, -4, 4), 'SUN', 3.0)
        key_light.rotation_euler = (0.5, 0.3, 0.8)
        
        # Add fill light
        fill_light = self._create_light("Fill", (-2, -2, 3), 'POINT', 500)
        fill_light.data.color = (1.0, 0.95, 0.9)
        
        # Add subtle back/rim light
        rim_light = self._create_light("Rim", (0, 3, 2), 'POINT', 200)
        rim_light.data.color = (0.9, 0.95, 1.0)
    
    def _create_light(self, name: str, location: tuple, light_type: str, energy: float):
        """Create a light source."""
        bpy.ops.object.light_add(type=light_type, location=location)
        light = bpy.context.active_object
        light.name = name
        light.data.energy = energy
        return light
    
    def create_board_procedural(self, material_type: str = "walnut"):
        """Create procedural 3D chess board with raised squares."""
        # Board dimensions (standard tournament size)
        board_size = 5.08  # ~20 inches
        square_size = board_size / 8
        square_height = 0.008  # ~3mm raised squares
        base_thickness = 0.025  # ~1 inch thick border
        
        # Create base
        bpy.ops.mesh.primitive_cube_add(
            size=1, 
            location=(0, 0, -base_thickness/2)
        )
        base = bpy.context.active_object
        base.name = "BoardBase"
        base.scale = (board_size/2 + 0.05, board_size/2 + 0.05, base_thickness/2)
        
        # Board material (border)
        border_mat = self._create_wood_material(f"border_{material_type}", dark=True)
        base.data.materials.append(border_mat)
        
        # Create squares (8x8 grid)
        for row in range(8):
            for col in range(8):
                is_dark = (row + col) % 2 == 1
                
                x = (col - 3.5) * square_size
                y = (row - 3.5) * square_size
                z = square_height / 2
                
                bpy.ops.mesh.primitive_cube_add(
                    size=1,
                    location=(x, y, z)
                )
                square = bpy.context.active_object
                square.name = f"Square_{chr(ord('a')+col)}{row+1}"
                square.scale = (square_size/2 - 0.002, square_size/2 - 0.002, square_height/2)
                
                # Material based on color
                mat = self._create_wood_material(
                    f"square_{is_dark}_{material_type}",
                    dark=is_dark
                )
                square.data.materials.append(mat)
        
        self.board = base
        print(f"✓ Created {material_type} chess board")
    
    def _create_wood_material(self, name: str, dark: bool = False):
        """Create realistic wood material."""
        if name in self.materials:
            return self.materials[name]
        
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        
        # Clear default
        for n in list(nodes):
            if n.type != 'OUTPUT_MATERIAL':
                nodes.remove(n)
        
        output = nodes["Material Output"]
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        
        # Wood colors
        if dark:
            base_color = (0.15, 0.08, 0.04, 1.0)  # Dark walnut
            roughness = 0.6
        else:
            base_color = (0.85, 0.75, 0.55, 1.0)  # Light maple
            roughness = 0.5
        
        principled.inputs['Base Color'].default_value = base_color
        principled.inputs['Roughness'].default_value = roughness
        principled.inputs['Specular IOR Level'].default_value = 0.3
        
        links.new(principled.outputs[0], output.inputs[0])
        
        self.materials[name] = mat
        return mat
    
    def _create_piece_material(self, name: str, is_white: bool):
        """Create piece material (plastic/polished wood)."""
        if name in self.materials:
            return self.materials[name]
        
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        
        for n in list(nodes):
            if n.type != 'OUTPUT_MATERIAL':
                nodes.remove(n)
        
        output = nodes["Material Output"]
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        
        if is_white:
            base_color = (0.95, 0.94, 0.9, 1.0)
            roughness = 0.15
            specular = 0.4
        else:
            base_color = (0.08, 0.08, 0.1, 1.0)
            roughness = 0.2
            specular = 0.5
        
        principled.inputs['Base Color'].default_value = base_color
        principled.inputs['Roughness'].default_value = roughness
        principled.inputs['Specular IOR Level'].default_value = specular
        
        links.new(principled.outputs[0], output.inputs[0])
        
        self.materials[name] = mat
        return mat
    
    def create_piece_procedural(self, piece_type: str, is_white: bool, square: str):
        """Create procedural 3D chess piece."""
        file_idx = ord(square[0]) - ord('a')
        rank_idx = int(square[1]) - 1
        
        # Calculate world position (board center is 0,0)
        square_size = 5.08 / 8
        x = (file_idx - 3.5) * square_size
        y = (rank_idx - 3.5) * square_size
        z = 0.038  # On top of squares
        
        color = "white" if is_white else "black"
        piece_height = {
            'pawn': 0.045,
            'rook': 0.065,
            'knight': 0.070,
            'bishop': 0.075,
            'queen': 0.085,
            'king': 0.095
        }.get(piece_type, 0.06)
        
        # Create base group
        bpy.ops.object.empty_add(location=(x, y, z))
        piece_root = bpy.context.active_object
        piece_root.name = f"{color}_{piece_type}_{square}"
        
        # Base cylinder
        base_z = z + piece_height * 0.15
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.022,
            depth=0.025,
            location=(x, y, base_z)
        )
        base = bpy.context.active_object
        base.parent = piece_root
        
        # Main body (varies by piece type)
        body_z = z + piece_height * 0.55
        
        if piece_type == 'pawn':
            # Cylinder with sphere head
            bpy.ops.mesh.primitive_cylinder_add(
                radius=0.018,
                depth=piece_height * 0.6,
                location=(x, y, body_z - 0.01)
            )
            
            bpy.ops.mesh.primitive_uv_sphere_add(
                radius=0.022,
                location=(x, y, z + piece_height * 0.85)
            )
            
        elif piece_type == 'rook':
            # Cylinder with crenellations
            bpy.ops.mesh.primitive_cylinder_add(
                radius=0.020,
                depth=piece_height * 0.7,
                location=(x, y, body_z)
            )
            
            # Top with 4 crenellations
            top_z = z + piece_height * 0.9
            for dx, dy in [(0.012, 0.012), (-0.012, 0.012), (0.012, -0.012), (-0.012, -0.012)]:
                bpy.ops.mesh.primitive_cube_add(
                    size=0.015,
                    location=(x + dx, y + dy, top_z)
                )
        
        elif piece_type == 'knight':
            # Base with angled 'head'
            bpy.ops.mesh.primitive_cylinder_add(
                radius=0.019,
                depth=piece_height * 0.55,
                location=(x, y, body_z - 0.01)
            )
            # Stylized head block
            bpy.ops.mesh.primitive_cube_add(
                size=0.028,
                location=(x + 0.008, y, z + piece_height * 0.82)
            )
            
        elif piece_type == 'bishop':
            # Tall cylinder with mitre (cone + sphere)
            bpy.ops.mesh.primitive_cylinder_add(
                radius=0.016,
                depth=piece_height * 0.7,
                location=(x, y, body_z)
            )
            # Mitre
            bpy.ops.mesh.primitive_cone_add(
                radius1=0.010,
                radius2=0.005,
                depth=0.015,
                location=(x, y, z + piece_height * 0.92)
            )
            
        elif piece_type == 'queen':
            # Elongated body with crown
            bpy.ops.mesh.primitive_cylinder_add(
                radius=0.018,
                depth=piece_height * 0.75,
                location=(x, y, body_z)
            )
            # Crown points
            top_z = z + piece_height * 0.93
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                bx = x + 0.020 * math.cos(rad)
                by = y + 0.020 * math.sin(rad)
                bpy.ops.mesh.primitive_uv_sphere_add(
                    radius=0.004,
                    location=(bx, by, top_z)
                )
                
        elif piece_type == 'king':
            # Tall with cross top
            bpy.ops.mesh.primitive_cylinder_add(
                radius=0.019,
                depth=piece_height * 0.75,
                location=(x, y, body_z)
            )
            # Cross
            cross_z = z + piece_height * 0.92
            bpy.ops.mesh.primitive_cube_add(
                size=(0.004, 0.024, 0.012),
                location=(x, y, cross_z)
            )
            bpy.ops.mesh.primitive_cube_add(
                size=(0.020, 0.004, 0.004),
                location=(x, y, cross_z + 0.006)
            )
        
        # Apply material
        for obj in piece_root.children:
            if obj.type == 'MESH':
                mat = self._create_piece_material(f"piece_{color}", is_white)
                if len(obj.data.materials) == 0:
                    obj.data.materials.append(mat)
                else:
                    obj.data.materials[0] = mat
        
        self.pieces.append(piece_root)
        return piece_root
    
    def load_piece_model(self, piece_type: str, color: str, square: str, asset_dir: Path):
        """Load piece from .obj model file."""
        file_idx = ord(square[0]) - ord('a')
        rank_idx = int(square[1]) - 1
        square_size = 5.08 / 8
        
        # Calculate position
        x = (file_idx - 3.5) * square_size
        y = (rank_idx - 3.5) * square_size
        z = 0.038  # On board surface
        
        # Try to load model
        obj_path = asset_dir / "pieces" / "set_03_classic" / color / f"{piece_type}.obj"
        if not obj_path.exists():
            print(f"Model not found: {obj_path}, using procedural")
            return self.create_piece_procedural(piece_type, color == "white", square)
        
        # Import OBJ
        bpy.ops.import_scene.obj(filepath=str(obj_path))
        imported = bpy.context.selected_objects[0]
        
        # Position and scale
        imported.location = (x, y, z)
        imported.scale = (0.5, 0.5, 0.5)  # Scale to board
        
        # Name and material
        imported.name = f"{color}_{piece_type}_{square}"
        
        # Apply material
        is_white = color == "white"
        mat = self._create_piece_material(f"piece_{color}", is_white)
        
        # Replace or add material
        if len(imported.data.materials) > 0:
            imported.data.materials[0] = mat
        else:
            imported.data.materials.append(mat)
        
        self.pieces.append(imported)
        return imported
    
    def place_pieces_from_fen(self, fen: str, use_models: bool = False):
        """Place pieces according to FEN notation."""
        # Clear existing pieces
        for p in self.pieces:
            bpy.data.objects.remove(p, do_unlink=True)
        self.pieces = []
        
        # Parse FEN
        board_part = fen.split()[0]
        ranks = board_part.split('/')
        
        piece_map = {
            'k': 'king', 'q': 'queen', 'r': 'rook',
            'b': 'bishop', 'n': 'knight', 'p': 'pawn'
        }
        
        for rank_idx, rank in enumerate(ranks):
            file_idx = 0
            for char in rank:
                if char.isdigit():
                    file_idx += int(char)
                else:
                    square = f"{chr(ord('a') + file_idx)}{8 - rank_idx}"
                    color = "white" if char.isupper() else "black"
                    piece_type = piece_map.get(char.lower())
                    
                    if use_models:
                        self.load_piece_model(piece_type, color, square, ASSETS_DIR)
                    else:
                        self.create_piece_procedural(
                            piece_type, 
                            char.isupper(), 
                            square
                        )
                    
                    file_idx += 1
        
        print(f"✓ Placed {len(self.pieces)} pieces from FEN")
    
    def setup_ultra_shallow_camera(self, config: CameraConfig):
        """Setup camera for ultra-shallow phone perspective."""
        # Remove existing camera
        for obj in bpy.data.objects:
            if obj.type == 'CAMERA':
                bpy.data.objects.remove(obj, do_unlink=True)
        
        # Create new camera
        bpy.ops.object.camera_add()
        camera = bpy.context.active_object
        self.camera = camera
        camera.name = "PhoneCamera"
        
        # Key insight: angle_from_horizontal = angle from table surface
        # Small angles = camera almost on table = phone perspective
        # Convert to radians
        angle_rad = math.radians(config.angle_from_horizontal)
        azimuth_rad = math.radians(config.azimuth)
        
        # Distance in meters
        distance_m = config.distance_cm / 100.0
        
        # Calculate camera position
        # x = horizontal distance, y = side distance, z = height
        # z = distance * sin(angle)
        horizontal_dist = distance_m * math.cos(angle_rad)
        
        x = horizontal_dist * math.cos(azimuth_rad)
        y = horizontal_dist * math.sin(azimuth_rad)
        z = distance_m * math.sin(angle_rad)
        
        camera.location = (x, y, z)
        
        # Point at board center
        direction = Vector((0, 0, 0.1)) - camera.location  # Aim slightly above center
        rot_quat = direction.to_track_quat('-Z', 'Y')
        camera.rotation_euler = rot_quat.to_euler()
        
        # Add hand jitter (tilt/pitch + roll)
        if config.tilt_degrees:
            camera.rotation_euler.x += math.radians(config.tilt_degrees)
        if config.roll_degrees:
            camera.rotation_euler.z += math.radians(config.roll_degrees)
        
        # Camera settings - iPhone-like
        camera.data.lens = config.focal_length_mm
        camera.data.sensor_width = 32  # APS-C-ish but phone-like
        camera.data.sensor_height = 24
        
        # Set as active camera
        bpy.context.scene.camera = camera
        
        print(f"✓ Camera: {config.distance_cm:.0f}cm, "
              f"{config.angle_from_horizontal:.1f}° from horizontal, "
              f"azimuth {config.azimuth:.0f}°")
    
    def render(self, output_path: Path, samples: int = 256):
        """Render to image file."""
        scene = bpy.context.scene
        render = scene.render
        
        # Configure Cycles for quality
        render.engine = 'CYCLES'
        scene.cycles.device = 'GPU' if scene.cycles.available_devices else 'CPU'
        
        # Resolution - phone camera aspect ratio
        render.resolution_x = 640
        render.resolution_y = 640
        render.resolution_percentage = 100
        
        # Cycles settings
        scene.cycles.samples = samples
        scene.cycles.use_denoising = True
        
        # Output settings
        render.filepath = str(output_path)
        render.image_settings.file_format = 'PNG'
        render.image_settings.color_mode = 'RGB'
        render.image_settings.compression = 90
        
        print(f"Rendering: {output_path}")
        bpy.ops.render.render(write_still=True)
        
        return output_path
    
    def get_ground_truth_data(self, fen: str, config: CameraConfig):
        """Get ground truth annotations for ML training."""
        scene = bpy.context.scene
        render = scene.render
        camera = self.camera
        
        annotations = []
        img_w = render.resolution_x
        img_h = render.resolution_y
        
        for piece in self.pieces:
            # Get bounding box from mesh
            bbox_corners = [piece.matrix_world @ Vector(corner)
                          for corner in piece.bound_box]
            
            min_x, min_y = float('inf'), float('inf')
            max_x, max_y = float('-inf'), float('-inf')
            
            for corner in bbox_corners:
                coord = world_to_camera_view(scene, camera, corner)
                min_x = min(min_x, coord.x)
                max_x = max(max_x, coord.x)
                min_y = min(min_y, coord.y)
                max_y = max(max_y, coord.y)
            
            # Convert to pixel coordinates
            px = min_x * img_w
            py = (1 - max_y) * img_h  # Flip Y
            pw = (max_x - min_x) * img_w
            ph = (max_y - min_y) * img_h
            
            # Parse piece info from name: "{color}_{type}_{square}"
            parts = piece.name.split('_')
            if len(parts) >= 3:
                annotations.append({
                    'class': f"{parts[0]}_{parts[1]}",  # e.g., "white_king"
                    'square': parts[2],
                    'bbox': [round(px, 2), round(py, 2), round(pw, 2), round(ph, 2)]
                })
        
        return {
            'fen': fen,
            'camera': asdict(config),
            'annotations': annotations,
            'image_resolution': [img_w, img_h]
        }


# Sample FEN positions
SAMPLE_POSITIONS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",  # Standard
    "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",  # 1.e4
    "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq -",  # Italian
    "8/8/3k4/8/4K3/8/8/8 w - - 0 1",  # King endgame
    "r1bqk2r/ppp2ppp/2n5/3Pp3/1bP5/5N2/PP2BPPP/RN1QK2R w KQkq -",  # Complex
]


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Ultra-Shallow Chess Renderer')
    parser.add_argument('--count', type=int, default=10, help='Number of renders')
    parser.add_argument('--output', type=str, default=str(OUTPUT_DIR), help='Output directory')
    parser.add_argument('--samples', type=int, default=128, help='Cycles samples')
    parser.add_argument('--procedural', action='store_true', help='Use procedural pieces')
    
    # Parse args (handle Blender's arg format)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    
    print("="*60)
    print("Chess Vision - Ultra-Shallow 3D Renderer v2")
    print("="*60)
    print(f"Output: {args.output}")
    print(f"Count: {args.count}")
    print(f"Camera: 5-25° from horizontal (phone perspective)")
    print(f"Distance: 15-35cm from board edge")
    print("="*60)
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    images_dir = output_dir / "images"
    images_dir.mkdir(exist_ok=True)
    
    # Find HDRI
    hdri_files = list(ASSETS_DIR.glob("hdri/**/*.exr")) + list(ASSETS_DIR.glob("hdri/**/*.hdr"))
    hdri_path = random.choice(hdri_files) if hdri_files else None
    
    if hdri_path:
        print(f"Using HDRI: {hdri_path}")
    
    # Create scene builder
    scene = ChessScene3D()
    scene.create_board_procedural("walnut")
    scene.setup_environment(hdri_path)
    
    results = []
    
    for i in range(args.count):
        fen = random.choice(SAMPLE_POSITIONS)
        
        # Ultra-shallow camera config
        camera_config = CameraConfig(
            angle_from_horizontal=random.uniform(5.0, 25.0),  # VERY shallow!
            azimuth=random.uniform(0.0, 360.0),
            distance_cm=random.uniform(15.0, 35.0),
            tilt_degrees=random.uniform(-3.0, 3.0),  # Hand shake
            roll_degrees=random.uniform(-2.0, 2.0)   # Phone tilt
        )
        
        output_path = images_dir / f"chess_{i:04d}.png"
        
        scene.place_pieces_from_fen(fen, use_models=not args.procedural)
        scene.setup_ultra_shallow_camera(camera_config)
        scene.render(output_path, samples=args.samples)
        
        # Get ground truth
        gt_data = scene.get_ground_truth_data(fen, camera_config)
        gt_data['image_path'] = str(output_path)
        results.append(gt_data)
        
        print(f"  ✓ {i+1}/{args.count}: angle={camera_config.angle_from_horizontal:.1f}°, "
              f"dist={camera_config.distance_cm:.0f}cm, {fen[:30]}...")
    
    # Save metadata
    metadata_path = output_dir / "ground_truth.json"
    with open(metadata_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*60)
    print("Complete!")
    print(f"Generated: {len(results)} images")
    print(f"Output: {output_dir}")
    print(f"Metadata: {metadata_path}")
    print("="*60)


if __name__ == "__main__":
    main()
