"""
Blender rendering backend.
Interfaces with Blender's bpy API for scene construction and rendering.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import json
import tempfile

# Try to import bpy (will only work when running inside Blender)
try:
    import bpy
    import bmesh
    from mathutils import Vector, Matrix, Euler
    from bpy_extras.object_utils import world_to_camera_view
    HAS_BPY = True
except ImportError:
    HAS_BPY = False
    print("Warning: bpy not available. Blender operations will fail.")


@dataclass
class RenderResult:
    """Result of a render operation."""
    image_path: Path
    annotations: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None


@dataclass
class BoundingBox:
    """2D bounding box in image coordinates."""
    x: float
    y: float
    width: float
    height: float
    piece_class: str
    square: str
    occlusion_ratio: float = 1.0


class BlenderBackend:
    """Blender-based rendering backend."""
    
    def __init__(self, blend_template: Optional[Path] = None):
        if not HAS_BPY:
            raise RuntimeError("Blender Python API (bpy) not available. "
                             "This must be run inside Blender or with blender --python.")
        
        self.blend_template = blend_template
        self.scene = None
        self.camera = None
        self.board_collection = None
        self.pieces_collection = None
        
        # Clear default scene
        self._clear_scene()
        self._setup_collections()
    
    def _clear_scene(self):
        """Clear all mesh objects and materials from default scene."""
        # Delete all mesh objects
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.select_by_type(type='MESH')
        bpy.ops.object.delete()
        
        # Delete all materials except material slots
        for material in bpy.data.materials:
            if material.users == 0:
                bpy.data.materials.remove(material)
    
    def _setup_collections(self):
        """Set up scene collections for organization."""
        # Create collections
        if "Board" not in bpy.data.collections:
            self.board_collection = bpy.data.collections.new("Board")
            bpy.context.scene.collection.children.link(self.board_collection)
        else:
            self.board_collection = bpy.data.collections["Board"]
        
        if "Pieces" not in bpy.data.collections:
            self.pieces_collection = bpy.data.collections.new("Pieces")
            bpy.context.scene.collection.children.link(self.pieces_collection)
        else:
            self.pieces_collection = bpy.data.collections["Pieces"]
    
    def load_board(self, board_path: Path, material_config: Dict[str, Any]):
        """Load and position the chess board."""
        # Import board OBJ
        bpy.ops.import_scene.obj(filepath=str(board_path))
        
        # Get imported object
        board_obj = bpy.context.selected_objects[0]
        board_obj.name = "ChessBoard"
        
        # Move to board collection
        self._move_to_collection(board_obj, self.board_collection)
        
        # Apply material if specified
        if material_config:
            self._apply_board_material(board_obj, material_config)
        
        return board_obj
    
    def load_piece(self, piece_type: str, color: str, square: str, 
                   piece_set_path: Path, rotation: float = 0.0) -> Any:
        """Load and position a chess piece."""
        # Construct path to piece OBJ
        piece_file = piece_set_path / color.lower() / f"{piece_type.lower()}.obj"
        
        if not piece_file.exists():
            raise FileNotFoundError(f"Piece file not found: {piece_file}")
        
        # Import piece
        bpy.ops.import_scene.obj(filepath=str(piece_file))
        piece_obj = bpy.context.selected_objects[0]
        piece_obj.name = f"{color}_{piece_type}_{square}"
        
        # Calculate board position from square
        x, y = self._square_to_coords(square)
        
        # Position piece
        piece_obj.location = (x, y, 0.025)  # Slightly above board
        
        # Apply board rotation if specified
        if rotation != 0:
            piece_obj.rotation_euler = (0, 0, rotation)
        
        # Move to pieces collection
        self._move_to_collection(piece_obj, self.pieces_collection)
        
        return piece_obj
    
    def _square_to_coords(self, square: str) -> Tuple[float, float]:
        """Convert chess square (e.g., 'e4') to board coordinates."""
        file_char = square[0]
        rank_char = square[1]
        
        file_idx = ord(file_char) - ord('a')  # 0-7
        rank_idx = int(rank_char) - 1  # 0-7
        
        # Board is 56cm (0.56m), squares are 5.7cm (0.057m)
        # Origin at board center
        square_size = 0.057
        board_size = 0.56
        border = 0.02
        
        # Calculate position from board center
        x = (file_idx - 3.5) * square_size
        y = (rank_idx - 3.5) * square_size
        
        return (x, y)
    
    def _move_to_collection(self, obj, collection):
        """Move object to a specific collection."""
        # Unlink from current collections
        for coll in obj.users_collection:
            coll.objects.unlink(obj)
        
        # Link to new collection
        collection.objects.link(obj)
    
    def _apply_board_material(self, board_obj, material_config):
        """Apply PBR material to board."""
        # Create material
        mat = bpy.data.materials.new(name="BoardMaterial")
        mat.use_nodes = True
        
        # Get principled BSDF
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        bsdf = nodes.get("Principled BSDF")
        
        # Load textures if paths provided
        if 'diffuse_path' in material_config:
            tex_image = nodes.new('ShaderNodeTexImage')
            tex_image.image = bpy.data.images.load(str(material_config['diffuse_path']))
            links.new(tex_image.outputs['Color'], bsdf.inputs['Base Color'])
        
        if 'roughness_path' in material_config:
            tex_image = nodes.new('ShaderNodeTexImage')
            tex_image.image = bpy.data.images.load(str(material_config['roughness_path']))
            links.new(tex_image.outputs['Color'], bsdf.inputs['Roughness'])
        
        if 'normal_path' in material_config:
            tex_image = nodes.new('ShaderNodeTexImage')
            tex_image.image = bpy.data.images.load(str(material_config['normal_path']))
            normal_map = nodes.new('ShaderNodeNormalMap')
            links.new(tex_image.outputs['Color'], normal_map.inputs['Color'])
            links.new(normal_map.outputs['Normal'], bsdf.inputs['Normal'])
        
        # Assign material
        board_obj.data.materials.append(mat)
    
    def setup_camera(self, params: Dict[str, float]):
        """Set up camera with given parameters."""
        # Create camera if it doesn't exist
        if "Camera" not in bpy.data.objects:
            bpy.ops.object.camera_add()
        
        camera = bpy.data.objects["Camera"]
        self.camera = camera
        
        # Calculate position from angle, rotation, distance
        angle_rad = params['angle'] * 3.14159 / 180
        rotation_rad = params['rotation'] * 3.14159 / 180
        distance = params['distance'] / 100  # Convert cm to meters
        
        # Camera position in spherical coordinates
        # Angle is from horizontal, rotation is around vertical axis
        x = distance * math.cos(angle_rad) * math.cos(rotation_rad)
        y = distance * math.cos(angle_rad) * math.sin(rotation_rad)
        z = distance * math.sin(angle_rad)
        
        camera.location = (x, y, z)
        
        # Point camera at board center
        direction = Vector((0, 0, 0)) - camera.location
        rot_quat = direction.to_track_quat('-Z', 'Y')
        camera.rotation_euler = rot_quat.to_euler()
        
        # Set camera properties
        camera.data.lens = params['focal_length']
        camera.data.sensor_width = 36  # Full frame
        
        # Set as active camera
        bpy.context.scene.camera = camera
    
    def setup_lighting(self, params: Dict[str, Any]):
        """Set up lighting with HDRI and key/fill lights."""
        world = bpy.context.scene.world
        world.use_nodes = True
        nodes = world.node_tree.nodes
        links = world.node_tree.links
        
        # Clear existing nodes
        nodes.clear()
        
        # Add background node
        background = nodes.new('ShaderNodeBackground')
        output = nodes.new('ShaderNodeOutputWorld')
        
        # Load HDRI if path provided
        if 'hdri_path' in params:
            env_tex = nodes.new('ShaderNodeTexEnvironment')
            try:
                env_tex.image = bpy.data.images.load(str(params['hdri_path']))
                links.new(env_tex.outputs['Color'], background.inputs['Color'])
            except:
                # Fallback to solid color
                background.inputs['Color'].default_value = (0.5, 0.5, 0.5, 1.0)
        
        links.new(background.outputs['Background'], output.inputs['Surface'])
        
        # Set intensity
        background.inputs['Strength'].default_value = params.get('intensity', 1.0)
        
        # Add key light (sun)
        bpy.ops.object.light_add(type='SUN', location=(5, 5, 8))
        sun = bpy.context.active_object
        sun.data.energy = 3.0
        sun.rotation_euler = (0.5, 0, 0.8)
        
        # Add fill light
        bpy.ops.object.light_add(type='AREA', location=(-3, -3, 4))
        fill = bpy.context.active_object
        fill.data.energy = 1.0
    
    def render_to_file(self, output_path: Path, samples: int = 128) -> Path:
        """Render current scene to file."""
        scene = bpy.context.scene
        
        # Configure render settings
        scene.render.engine = 'CYCLES'
        scene.cycles.samples = samples
        scene.cycles.use_denoising = True
        
        # Set resolution
        scene.render.resolution_x = 640
        scene.render.resolution_y = 640
        
        # Set output path
        scene.render.filepath = str(output_path)
        scene.render.image_settings.file_format = 'PNG'
        
        # Render
        bpy.ops.render.render(write_still=True)
        
        return output_path
    
    def get_ground_truth_annotations(self) -> List[BoundingBox]:
        """Calculate 2D bounding boxes for all pieces."""
        if not self.camera:
            raise RuntimeError("Camera not set up")
        
        scene = bpy.context.scene
        camera = self.camera
        
        annotations = []
        
        for obj in self.pieces_collection.objects:
            if obj.type != 'MESH':
                continue
            
            # Get bounding box in world coordinates
            bbox_corners = [obj.matrix_world @ Vector(corner) 
                          for corner in obj.bound_box]
            
            # Project to camera space
            proj_coords = []
            for corner in bbox_corners:
                coord = world_to_camera_view(scene, camera, corner)
                proj_coords.append((coord.x, coord.y))
            
            # Calculate 2D bounding box
            min_x = min(c[0] for c in proj_coords)
            max_x = max(c[0] for c in proj_coords)
            min_y = min(c[1] for c in proj_coords)
            max_y = max(c[1] for c in proj_coords)
            
            # Convert to pixel coordinates (flip Y)
            width = scene.render.resolution_x
            height = scene.render.resolution_y
            
            x = min_x * width
            y = (1 - max_y) * height  # Flip Y
            w = (max_x - min_x) * width
            h = (max_y - min_y) * height
            
            # Extract piece info from name
            # Format: "{color}_{piece}_{square}"
            parts = obj.name.split('_')
            if len(parts) >= 3:
                color = parts[0]
                piece_type = parts[1]
                square = parts[2]
                
                annotations.append(BoundingBox(
                    x=x,
                    y=y,
                    width=w,
                    height=h,
                    piece_class=f"{color}_{piece_type}",
                    square=square,
                    occlusion_ratio=1.0  # Would need occlusion testing
                ))
        
        return annotations
    
    def clear_pieces(self):
        """Remove all pieces but keep board."""
        for obj in list(self.pieces_collection.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    
    def clear_all(self):
        """Clear board and pieces."""
        self._clear_scene()
        self._setup_collections()


import math  # For math functions used in camera setup


# Export for testing
if __name__ == "__main__":
    if HAS_BPY:
        print("Blender backend available")
    else:
        print("Blender backend not available (bpy import failed)")
