#!/usr/bin/env python3
"""
ChessVision Synthetic Data Generator
Generates photorealistic chess board images at shallow (30°) camera angles
"""

import bpy
import math
import random
import os
import json
import mathutils
from pathlib import Path

# Configuration
OUTPUT_DIR = "/workspace/chess-vision-ai/data/synthetic_renders"
TOTAL_IMAGES = 1000
CAMERA_ANGLE = 30  # degrees from horizontal - shallow angle for phone view
BOARD_SIZE = 0.5  # meters

class ChessBoardGenerator:
    def __init__(self):
        self.setup_scene()
        self.create_materials()
        
    def setup_scene(self):
        """Configure Blender scene for photorealistic rendering"""
        # Clear existing mesh objects
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        
        # Scene settings
        scene = bpy.context.scene
        scene.render.engine = 'CYCLES'
        scene.cycles.samples = 128  # Quality vs speed balance
        scene.cycles.device = 'GPU' if bpy.context.preferences.addons['cycles'].preferences.devices:
        scene.render.resolution_x = 1280
        scene.render.resolution_y = 720
        scene.render.resolution_percentage = 100
        
        # Enable GPU if available
        bpy.context.preferences.addons['cycles'].preferences.get_devices()
        for device in bpy.context.preferences.addons['cycles'].preferences.devices:
            if device.type == 'CUDA' or device.type == 'HIP':
                device.use = True
        
        # Create output directory
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
    def create_materials(self):
        """Create realistic materials for board and pieces"""
        # Light Square Material (off-white wood)
        light_wood = bpy.data.materials.new(name="LightWood")
        light_wood.use_nodes = True
        nodes = light_wood.node_tree.nodes
        principled = nodes['Principled BSDF']
        principled.inputs['Base Color'].default_value = (0.95, 0.85, 0.75, 1)
        principled.inputs['Roughness'].default_value = 0.4
        principled.inputs['Specular'].default_value = 0.2
        
        # Dark Square Material (dark wood)
        dark_wood = bpy.data.materials.new(name="DarkWood")
        dark_wood.use_nodes = True
        nodes = dark_wood.node_tree.nodes
        principled = nodes['Principled BSDF']
        principled.inputs['Base Color'].default_value = (0.3, 0.2, 0.15, 1)
        principled.inputs['Roughness'].default_value = 0.4
        principled.inputs['Specular'].default_value = 0.2
        
        self.light_wood = light_wood
        self.dark_wood = dark_wood
    
    def create_board(self):
        """Create chess board with realistic wood texture"""
        # Board base
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
        board_base = bpy.context.active_object
        board_base.scale = (0.35, 0.35, 0.015)  # Standard tournament size
        board_base.name = "ChessBoard"
        
        # Create squares
        square_size = BOARD_SIZE / 8
        for row in range(8):
            for col in range(8):
                x = (col - 3.5) * square_size
                y = (row - 3.5) * square_size
                is_light = (row + col) % 2 == 0
                
                bpy.ops.mesh.primitive_cube_add(
                    size=1, 
                    location=(x, y, 0.008)
                )
                square = bpy.context.active_object
                square.scale = (square_size * 0.5 - 0.002, square_size * 0.5 - 0.002, 0.001)
                square.data.materials.append(
                    self.light_wood if is_light else self.dark_wood
                )
                square.name = f"Square_{row}_{col}"
                
        return board_base
    
    def create_pieces(self, board_state=None):
        """Create chess pieces for rendering"""
        if board_state is None:
            # Default starting position
            board_state = self.generate_random_position()
        
        pieces = []
        square_size = BOARD_SIZE / 8
        
        for pos, piece_info in board_state.items():
            row, col = pos
            piece_type, color = piece_info
            
            x = (col - 3.5) * square_size
            y = (row - 3.5) * square_size
            z = 0.025  # Slightly above board
            
            # Create primitive piece (simplified geometry for speed)
            bpy.ops.mesh.primitive_cylinder_add(
                location=(x, y, z),
                radius=0.02,
                depth=0.05
            )
            piece = bpy.context.active_object
            
            # Assign material based on color
            mat = bpy.data.materials.new(name=f"Piece_{color}")
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            principled = nodes['Principled BSDF']
            if color == 'white':
                principled.inputs['Base Color'].default_value = (0.95, 0.95, 0.9, 1)
            else:
                principled.inputs['Base Color'].default_value = (0.15, 0.15, 0.15, 1)
            
            piece.data.materials.append(mat)
            pieces.append(piece)
        
        return pieces
    
    def generate_random_position(self):
        """Generate random valid chess position"""
        pieces_by_type = ['K', 'Q', 'R', 'R', 'B', 'B', 'N', 'N', 'P'] * 2
        colors = ['white'] * 16 + ['black'] * 16
        
        board = {}
        positions = random.sample([(r, c) for r in range(8) for c in range(8)], 
                                   min(32, random.randint(4, 20)))
        
        for pos in positions:
            piece_type = random.choice(['P', 'N', 'B', 'R', 'Q', 'K'])
            color = random.choice(['white', 'black'])
            board[pos] = (piece_type, color)
        
        return board
    
    def setup_camera(self, angle_deg=30, distance=0.6):
        """Setup camera at shallow angle for phone-camera-like view"""
        # Convert angle to radians
        elevation_rad = math.radians(angle_deg)
        
        # Calculate camera position
        x = distance * math.cos(elevation_rad) * math.cos(math.radians(random.uniform(-30, 30)))
        y = distance * math.cos(elevation_rad) * math.sin(math.radians(random.uniform(-30, 30)))
        z = distance * math.sin(elevation_rad)
        
        # Add random rotation variation
        x += random.uniform(-0.1, 0.1)
        y += random.uniform(-0.1, 0.1)
        
        bpy.ops.object.camera_add(location=(x, y, z))
        camera = bpy.context.active_object
        camera.data.lens = 35  # Standard lens
        camera.data.sensor_width = 36
        
        # Point camera at board center
        direction = mathutils.Vector((0, 0, 0)) - camera.location
        rot_quat = direction.to_track_quat('-Z', 'Y')
        camera.rotation_euler = rot_quat.to_euler()
        
        bpy.context.scene.camera = camera
        
        return camera
    
    def setup_lighting(self):
        """Setup realistic lighting conditions"""
        # Clear existing lights
        for obj in bpy.data.objects:
            if obj.type == 'LIGHT':
                bpy.data.objects.remove(obj)
        
        # Main light (soft fill)
        bpy.ops.object.light_add(type='AREA', location=(0.5, 0.5, 0.8))
        main_light = bpy.context.active_object
        main_light.data.energy = random.uniform(30, 80)
        main_light.data.size = 0.5
        
        # Secondary light (directional)
        bpy.ops.object.light_add(type='SUN', location=(-1, -1, 2))
        sun = bpy.context.active_object
        sun.data.energy = random.uniform(1, 3)
        
        # Fill light
        bpy.ops.object.light_add(type='AREA', location=(-0.5, 0.5, 0.5))
        fill = bpy.context.active_object
        fill.data.energy = random.uniform(10, 30)
    
    def setup_background(self):
        """Setup realistic table background"""
        # Table plane
        bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, -0.02))
        table = bpy.context.active_object
        
        # Wood material
        mat = bpy.data.materials.new(name="TableWood")
        mat.use_nodes = True
        principled = mat.node_tree.nodes['Principled BSDF']
        principled.inputs['Base Color'].default_value = (0.4, 0.3, 0.2, 1)
        principled.inputs['Roughness'].default_value = 0.6
        table.data.materials.append(mat)
    
    def render_sample(self, idx=0):
        """Generate and render a single training image"""
        # Randomize camera angle slightly
        camera = self.setup_camera(
            angle_deg=random.uniform(20, 45),
            distance=random.uniform(0.5, 0.8)
        )
        
        # Random lighting
        self.setup_lighting()
        
        # Render
        scene = bpy.context.scene
        output_path = os.path.join(OUTPUT_DIR, f"chess_render_{idx:04d}.png")
        scene.render.filepath = output_path
        bpy.ops.render.render(write_still=True)
        
        # Save metadata
        meta_path = os.path.join(OUTPUT_DIR, f"chess_render_{idx:04d}.json")
        metadata = {
            "camera_angle": camera.rotation_euler,
            "camera_location": list(camera.location),
            "render_idx": idx
        }
        with open(meta_path, 'w') as f:
            json.dump(metadata, f)
        
        return output_path
    
    def generate_batch(self, start_idx=0, count=10):
        """Generate batch of training images"""
        output_files = []
        for i in range(start_idx, start_idx + count):
            # Clear scene except camera/light
            bpy.ops.object.select_all(action='DESELECT')
            for obj in bpy.data.objects:
                if obj.type in ['MESH', 'LIGHT']:
                    obj.select_set(True)
            
            # Create fresh scene
            self.create_board()
            self.create_pieces()
            self.setup_background()
            
            # Render
            path = self.render_sample(i)
            output_files.append(path)
            
            # Cleanup
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete(use_global=False)
        
        return output_files

# Main execution
if __name__ == "__main__":
    print("Starting ChessVision Synthetic Data Generator...")
    print(f"Output directory: {OUTPUT_DIR}")
    
    generator = ChessBoardGenerator()
    
    # Generate first batch
    files = generator.generate_batch(start_idx=0, count=10)
    
    print(f"Generated {len(files)} images:")
    for f in files:
        print(f"  - {f}")
    
    print("\nDone! Check output directory for renders.")
