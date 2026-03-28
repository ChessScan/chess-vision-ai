import bpy
import json
import random
import os
import sys
import argparse
import time
import threading
from queue import Queue
from math import radians, sin, cos, pi
from mathutils import Vector, Euler
from bpy_extras.object_utils import world_to_camera_view

# ================================================================
# CONFIG
# ================================================================

BOARD_NAME = "Board"
CAMERA_NAME = "Camera"

# base mesh models for pieces
# (later swap these for real models!)
PIECE_PREFIX = "inst_"
PIECE_MODEL_MAP = {
    "P": "WhitePawn",
    "N": "WhiteKnight",
    "B": "WhiteBishop",
    "R": "WhiteRook",
    "Q": "WhiteQueen",
    "K": "WhiteKing",

    "p": "BlackPawn",
    "n": "BlackKnight",
    "b": "BlackBishop",
    "r": "BlackRook",
    "q": "BlackQueen",
    "k": "BlackKing",
}

OUTPUT_DIR = "//renders"
IMG_RES_X = 712
IMG_RES_Y = 712

# camera randomization params (defaults)
# Side view angles: -60 to 60 degrees for phone-like side perspective
# Avoid back angles (around 180/-180) for natural side view
DEFAULT_CAMERA_RADIUS = 18.0
DEFAULT_ELEVATION_MIN = radians(5)
DEFAULT_ELEVATION_MAX = radians(15)
DEFAULT_AZIMUTH_MIN   = radians(-60)  # Left side
DEFAULT_AZIMUTH_MAX   = radians(60)   # Right side (avoid back at 180/-180)

# Global camera settings (can be overridden by command line)
CAMERA_RADIUS = DEFAULT_CAMERA_RADIUS
ELEVATION_MIN = DEFAULT_ELEVATION_MIN
ELEVATION_MAX = DEFAULT_ELEVATION_MAX
AZIMUTH_MIN   = DEFAULT_AZIMUTH_MIN
AZIMUTH_MAX   = DEFAULT_AZIMUTH_MAX

# EEVEE settings cache
_eevee_settings_configured = False

# Segmentation colors for different object types
# Base segmentation colors (for board, background, and captured pieces)
SEGMENTATION_COLORS = {
    "board": (1.0, 0.0, 0.0, 1.0),  # Red
    "background": (0.0, 0.0, 0.0, 1.0),  # Black
    "captured_pieces": (0.5, 0.5, 0.5, 1.0),  # Gray for all captured pieces
}

# Generate unique colors for each square (64 squares total)
# Colors are generated deterministically based on square index
def generate_square_colors():
    """Generate unique colors for each of the 64 chess squares.
    
    Returns:
        Dictionary mapping square names (e.g., "a1", "e4") to RGBA tuples
    """
    square_colors = {}
    files = "abcdefgh"
    # Generate colors using a deterministic algorithm
    # Each square gets a unique color in RGB space
    for rank in range(1, 9):
        for file_idx, file_char in enumerate(files):
            square = f"{file_char}{rank}"
            # Calculate unique index for this square (0-63)
            square_idx = (rank - 1) * 8 + file_idx
            
            # Generate color using HSV to get evenly distributed colors
            # Hue cycles through full spectrum, S and V vary for distinction
            hue = (square_idx / 64.0)  # 0 to 1
            saturation = 0.6 + (square_idx % 3) * 0.13  # 0.6 to 0.99
            value = 0.5 + (square_idx % 2) * 0.4  # 0.5 or 0.9
            
            # Convert HSV to RGB
            # Manual HSV to RGB conversion (colorsys might not be available in Blender)
            import math
            c = value * saturation
            x = c * (1 - abs((hue * 6) % 2 - 1))
            m = value - c
            
            if hue < 1/6:
                r, g, b = c, x, 0
            elif hue < 2/6:
                r, g, b = x, c, 0
            elif hue < 3/6:
                r, g, b = 0, c, x
            elif hue < 4/6:
                r, g, b = 0, x, c
            elif hue < 5/6:
                r, g, b = x, 0, c
            else:
                r, g, b = c, 0, x
            
            r, g, b = r + m, g + m, b + m
            
            square_colors[square] = (r, g, b, 1.0)
    
    return square_colors

# Cache square colors
_SQUARE_COLORS = None

def get_square_colors():
    """Get cached square colors, generating them if needed."""
    global _SQUARE_COLORS
    if _SQUARE_COLORS is None:
        _SQUARE_COLORS = generate_square_colors()
    return _SQUARE_COLORS

# Periodic cleanup tracking
_render_count = 0
CLEANUP_INTERVAL = 50  # Periodic cleanup to prevent progressive slowdown (increased from 25 for better performance)

# Cache template piece objects to avoid iterating all objects repeatedly
_template_pieces = None

# Batch I/O settings
JSON_BATCH_SIZE = 20  # Write JSON files in batches of this size
_json_write_queue = Queue()
_json_write_thread = None
_json_write_stop = False


# ================================================================
# BATCH FILE I/O SYSTEM
# ================================================================

def _json_writer_worker():
    """Background thread worker for writing JSON files."""
    global _json_write_stop
    batch = []
    
    while not _json_write_stop or not _json_write_queue.empty():
        try:
            # Get item with timeout to allow checking stop flag
            item = _json_write_queue.get(timeout=0.1)
            batch.append(item)
            
            # Write batch when it reaches size or queue is empty and stopped
            if len(batch) >= JSON_BATCH_SIZE or (_json_write_stop and _json_write_queue.empty() and batch):
                for json_path, data in batch:
                    try:
                        with open(json_path, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2)
                    except Exception as e:
                        print(f"Error writing JSON {json_path}: {e}", file=sys.stderr)
                batch.clear()
            
            _json_write_queue.task_done()
        except:
            # Timeout - check if we should flush batch
            if batch and _json_write_stop and _json_write_queue.empty():
                for json_path, data in batch:
                    try:
                        with open(json_path, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2)
                    except Exception as e:
                        print(f"Error writing JSON {json_path}: {e}", file=sys.stderr)
                batch.clear()
            continue

def start_json_writer():
    """Start the background JSON writer thread."""
    global _json_write_thread, _json_write_stop
    _json_write_stop = False
    if _json_write_thread is None or not _json_write_thread.is_alive():
        _json_write_thread = threading.Thread(target=_json_writer_worker, daemon=True)
        _json_write_thread.start()

def stop_json_writer():
    """Stop the background JSON writer thread and flush remaining writes."""
    global _json_write_stop
    _json_write_stop = True
    if _json_write_thread and _json_write_thread.is_alive():
        _json_write_queue.join()  # Wait for all items to be processed

def queue_json_write(json_path, data):
    """Queue a JSON file to be written asynchronously."""
    _json_write_queue.put((json_path, data))


# ================================================================
# GPU INITIALIZATION
# ================================================================

def initialize_gpu():
    """Initialize GPU device for rendering. Returns True if GPU is available."""
    try:
        # Try to configure Cycles for GPU (if Cycles addon is available)
        if hasattr(bpy.context.preferences.addons, 'cycles'):
            prefs = bpy.context.preferences.addons['cycles'].preferences
            if hasattr(prefs, 'compute_device_type'):
                # Enable GPU devices
                for device in prefs.devices:
                    if device.type in ['CUDA', 'OPENCL', 'OPTIX', 'HIP', 'METAL']:
                        device.use = True
                        print(f"Enabled GPU device: {device.name} ({device.type})")
        
        # EEVEE uses GPU automatically if available, but we can verify
        scene = bpy.context.scene
        if scene.render.engine == 'BLENDER_EEVEE':
            # EEVEE will use GPU if available
            print("EEVEE engine configured (will use GPU if available)")
        
        return True
    except Exception as e:
        print(f"Warning: Could not initialize GPU: {e}")
        print("Falling back to CPU rendering")
        return False

_gpu_initialized = False

def ensure_gpu_initialized():
    """Ensure GPU is initialized (only once)."""
    global _gpu_initialized
    if not _gpu_initialized:
        _gpu_initialized = initialize_gpu()
    return _gpu_initialized


# ================================================================
# UTILITIES
# ================================================================

def get_square_names():
    files = "abcdefgh"
    ranks = "12345678"
    return [f"sq_{f}{r}" for r in ranks for f in files]


# ================================================================
# OBJECT POOLING SYSTEM
# ================================================================

# Maximum pieces to keep in pool per type (prevents unbounded growth)
MAX_POOL_SIZE_PER_TYPE = 32

class PiecePool:
    """Pool for reusing piece objects to avoid creation/deletion overhead."""
    
    def __init__(self):
        # Map: piece_type -> list of available (hidden) objects
        self.available_pieces = {}
        # Map: piece_name -> active object
        self.active_pieces = {}
        # Track all created pieces for cleanup
        self.all_pieces = []
        # Maximum pieces we might need (32 pieces max on board)
        self.max_pieces_per_type = 8
    
    def _get_piece_type(self, piece_code):
        """Get the model name for a piece code."""
        return PIECE_MODEL_MAP.get(piece_code)
    
    def _create_piece(self, piece_code, square_name, board_z):
        """Create a new piece object.
        
        CRITICAL: Share mesh data instead of copying to prevent memory accumulation.
        All pieces of the same type share the same mesh data block.
        """
        model_name = self._get_piece_type(piece_code)
        if not model_name:
            return None
        
        src = bpy.data.objects[model_name]
        files = "abcdefgh"
        
        # Extract square coordinates
        file_char = square_name[3]
        rank_char = square_name[4]
        file_index = files.index(file_char)
        rank_number = int(rank_char)
        
        sq = bpy.data.objects[square_name]
        
        # Create new object - SHARE mesh data instead of copying to prevent memory leak
        new_obj = src.copy()
        # CRITICAL FIX: Don't copy mesh data - share it to prevent unbounded mesh accumulation
        # new_obj.data = src.data.copy()  # REMOVED - this was causing memory leak
        new_obj.data = src.data  # Share the mesh data block
        new_obj.name = f"{PIECE_PREFIX}{piece_code}_{square_name}"
        bpy.context.collection.objects.link(new_obj)
        
        # Materials are already on the shared mesh data, no need to copy
        
        # Set position
        new_obj.location = sq.location
        
        self.all_pieces.append(new_obj)
        return new_obj
    
    def get_piece(self, piece_code, square_name, board_z):
        """Get a piece object from pool or create new one."""
        piece_name = f"{PIECE_PREFIX}{piece_code}_{square_name}"
        piece_type = self._get_piece_type(piece_code)
        
        if not piece_type:
            return None
        
        # Check if we already have this piece active
        if piece_name in self.active_pieces:
            return self.active_pieces[piece_name]
        
        # Check if a piece with this name already exists in the scene (duplicate prevention)
        if piece_name in bpy.data.objects:
            existing_obj = bpy.data.objects[piece_name]
            # If it's not in our active pieces, it's a leftover - delete it to prevent duplicates
            if piece_name not in self.active_pieces:
                # Remove from all tracking
                if existing_obj in self.all_pieces:
                    self.all_pieces.remove(existing_obj)
                # Remove from available_pieces if it's there
                for pt in self.available_pieces:
                    if existing_obj in self.available_pieces[pt]:
                        self.available_pieces[pt].remove(existing_obj)
                # Delete the duplicate
                bpy.data.objects.remove(existing_obj, do_unlink=True)
        
        # Try to get from available pool
        if piece_type in self.available_pieces and self.available_pieces[piece_type]:
            obj = self.available_pieces[piece_type].pop()
            # Update name and position
            old_name = obj.name
            
            # Check if new name already exists (shouldn't after above check, but double-check)
            if piece_name in bpy.data.objects and bpy.data.objects[piece_name] != obj:
                # There's a duplicate with the new name - delete it
                dup = bpy.data.objects[piece_name]
                if dup in self.all_pieces:
                    self.all_pieces.remove(dup)
                bpy.data.objects.remove(dup, do_unlink=True)
            
            obj.name = piece_name
            # Remove old name from active_pieces if it exists
            if old_name in self.active_pieces:
                del self.active_pieces[old_name]
            files = "abcdefgh"
            file_char = square_name[3]
            rank_char = square_name[4]
            sq = bpy.data.objects[square_name]
            obj.location = sq.location
            obj.hide_render = False
            obj.hide_viewport = False
        else:
            # Create new piece
            # Double-check no duplicate exists before creating
            if piece_name in bpy.data.objects:
                # Delete any existing duplicate
                dup = bpy.data.objects[piece_name]
                if dup in self.all_pieces:
                    self.all_pieces.remove(dup)
                bpy.data.objects.remove(dup, do_unlink=True)
            
            obj = self._create_piece(piece_code, square_name, board_z)
            if not obj:
                return None
        
        self.active_pieces[piece_name] = obj
        return obj
    
    def hide_all(self):
        """Hide all active pieces and return them to pool."""
        # First, hide any pieces in all_pieces that might not be in active_pieces
        # This catches any orphaned pieces efficiently (only checks our tracked pieces)
        for obj in self.all_pieces:
            if obj.name.startswith(PIECE_PREFIX) and obj.name not in self.active_pieces:
                if obj.name in bpy.data.objects:
                    obj.hide_render = True
                    obj.hide_viewport = True
        
        # Only iterate over tracked pieces (much faster than iterating all Blender objects)
        for piece_name, obj in list(self.active_pieces.items()):
            if obj.name not in bpy.data.objects:
                continue  # Object was deleted, skip
                
            piece_code = piece_name.split('_')[1]  # Extract piece code
            piece_type = self._get_piece_type(piece_code)
            
            if piece_type:
                obj.hide_render = True
                obj.hide_viewport = True
                
                # Return to pool
                if piece_type not in self.available_pieces:
                    self.available_pieces[piece_type] = []
                self.available_pieces[piece_type].append(obj)
                
                # Limit pool size to prevent unbounded growth
                if len(self.available_pieces[piece_type]) > MAX_POOL_SIZE_PER_TYPE:
                    excess = self.available_pieces[piece_type][MAX_POOL_SIZE_PER_TYPE:]
                    for excess_obj in excess:
                        # Delete excess pieces and their mesh data if not shared
                        if excess_obj.name in bpy.data.objects:
                            # Check if mesh is shared before removing
                            mesh = excess_obj.data
                            bpy.data.objects.remove(excess_obj, do_unlink=True)
                            # If mesh has no users left, remove it
                            if mesh.users == 0:
                                try:
                                    bpy.data.meshes.remove(mesh)
                                except:
                                    pass
                        # Remove from tracking
                        if excess_obj in self.all_pieces:
                            self.all_pieces.remove(excess_obj)
                    # Keep only the max allowed
                    self.available_pieces[piece_type] = self.available_pieces[piece_type][:MAX_POOL_SIZE_PER_TYPE]
        
        self.active_pieces.clear()
    
    def periodic_cleanup(self):
        """Periodically clean up orphaned pieces and mesh data blocks."""
        # Remove pieces that no longer exist in Blender scene
        # Use list comprehension for speed
        self.all_pieces = [obj for obj in self.all_pieces if obj.name in bpy.data.objects]
        
        # Also clean up any pieces in available_pieces that no longer exist
        for piece_type in list(self.available_pieces.keys()):
            self.available_pieces[piece_type] = [
                obj for obj in self.available_pieces[piece_type] 
                if obj.name in bpy.data.objects
            ]
        
        # Aggressively limit pool size to prevent unbounded growth
        if len(self.all_pieces) > 400:
            # Keep only most recent 400 pieces
            excess = self.all_pieces[:-400]
            for obj in excess:
                if obj.name in bpy.data.objects:
                    bpy.data.objects.remove(obj, do_unlink=True)
            self.all_pieces = self.all_pieces[-400:]
        
        # CRITICAL: Clean up orphaned mesh data blocks that are no longer used
        # This prevents Blender's bpy.data.meshes from growing unbounded
        self._cleanup_orphaned_meshes()
    
    def _cleanup_orphaned_meshes(self):
        """Remove mesh data blocks that are no longer used by any objects."""
        # Get all meshes used by our pieces
        used_meshes = set()
        for obj in self.all_pieces:
            if obj.name in bpy.data.objects and obj.data and hasattr(obj.data, 'name'):
                used_meshes.add(obj.data.name)
        
        # Also include template piece meshes
        template_pieces = get_template_pieces()
        for obj in template_pieces:
            if obj.name in bpy.data.objects and obj.data and hasattr(obj.data, 'name'):
                used_meshes.add(obj.data.name)
        
        # Find and remove orphaned meshes (meshes not used by any object)
        # Only check meshes that start with our piece prefix to avoid affecting other meshes
        meshes_to_remove = []
        for mesh in bpy.data.meshes:
            # Only clean up meshes that look like they're from our pieces
            # Check if mesh is only used by deleted/non-existent objects
            if mesh.users == 0:
                meshes_to_remove.append(mesh)
            elif mesh.name.startswith(PIECE_PREFIX) and mesh.name not in used_meshes:
                # This mesh is from our pieces but not in use - check if it's truly orphaned
                # Count how many objects actually use this mesh
                users = [obj for obj in bpy.data.objects if obj.data == mesh]
                if not users:
                    meshes_to_remove.append(mesh)
        
        # Remove orphaned meshes
        for mesh in meshes_to_remove:
            try:
                bpy.data.meshes.remove(mesh)
            except:
                pass  # Mesh might already be removed
    
    def cleanup(self):
        """Remove all pieces (for final cleanup)."""
        for obj in self.all_pieces:
            if obj.name in bpy.data.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
        self.available_pieces.clear()
        self.active_pieces.clear()
        self.all_pieces.clear()


# Global piece pool instance
_piece_pool = None

def get_piece_pool():
    """Get or create the global piece pool."""
    global _piece_pool
    if _piece_pool is None:
        _piece_pool = PiecePool()
    return _piece_pool

def get_template_pieces():
    """Get cached list of template piece objects (only computed once)."""
    global _template_pieces
    if _template_pieces is None:
        _template_pieces = [obj for obj in bpy.data.objects if obj.name in PIECE_MODEL_MAP.values()]
    return _template_pieces

def hide_template_pieces():
    """Efficiently hide all template pieces using cached list."""
    template_pieces = get_template_pieces()
    for obj in template_pieces:
        if obj.name in bpy.data.objects:  # Check it still exists
            obj.hide_render = True
            obj.hide_viewport = True
            # Only update active view layer for speed
            try:
                if obj.name in bpy.context.view_layer.objects:
                    bpy.context.view_layer.objects[obj.name].hide_render = True
            except:
                pass

def clear_old_instances():
    """Legacy function - now uses pooling."""
    pool = get_piece_pool()
    pool.hide_all()


# ================================================================
# MODEL LOADING
# ================================================================

# Cache for loaded models to avoid reloading
_loaded_models = {}

def get_model_paths():
    """Get paths to model files in assets directory."""
    blend_dir = os.path.dirname(bpy.data.filepath)
    assets_dir = os.path.join(blend_dir, "assets", "models")
    
    if not os.path.exists(assets_dir):
        # Fallback: try relative to script location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(script_dir, "assets", "models")
    
    models = {}
    if os.path.exists(assets_dir):
        for model_dir in os.listdir(assets_dir):
            model_path = os.path.join(assets_dir, model_dir)
            if os.path.isdir(model_path):
                # Look for .blend files in this directory
                for file in os.listdir(model_path):
                    if file.endswith('.blend'):
                        # Use directory name as identifier
                        identifier = model_dir.split('_')[0] if '_' in model_dir else model_dir
                        models[identifier] = os.path.join(model_path, file)
                        break
    
    return models


def load_board_model(model_id=None):
    """Load board model from assets directory.
    
    Args:
        model_id: Identifier for model (e.g., "wooden", "elegant"). 
                  If None or "default", uses existing board.
    
    Returns:
        True if successful, False otherwise
    """
    if not model_id or model_id == "default":
        return True  # Use existing board
    
    # Try to load from assets
    # Note: Full model loading/switching requires appending from .blend files
    # This is a placeholder - actual implementation depends on Blender file structure
    # For now, assume board models are already in the scene
    
    return True


def load_piece_set(set_id=None):
    """Load piece set and update PIECE_MODEL_MAP.
    
    Args:
        set_id: Identifier for piece set (e.g., "wooden", "elegant").
                If None or "default", uses existing pieces.
    
    Returns:
        True if successful, False otherwise
    """
    global PIECE_MODEL_MAP
    
    if not set_id or set_id == "default":
        return True  # Use existing piece mapping
    
    # Try to load from assets
    # Note: Full piece set loading requires appending from .blend files
    # This is a placeholder - actual implementation depends on Blender file structure
    # For now, assume piece sets use consistent naming in scene
    
    # If pieces are loaded with different names, update PIECE_MODEL_MAP here
    # Example: PIECE_MODEL_MAP = {...} with new model names
    
    return True


# ================================================================
# OFF-BOARD CAPTURED PIECES
# ================================================================

def place_captured_pieces(captured_pieces_config, board_obj, cam=None):
    """Place captured pieces off-board on the board surface, opposite to camera.
    
    Args:
        captured_pieces_config: List of captured piece configs, each with:
            - type: str, piece code (e.g., "R", "p")
            - position: [x, y] or [x, y, z] (Z is ignored, set to board surface)
            OR
            - type: str, piece code
            - zone: str, "left" | "right" | "both" (relative to camera position)
            - layout: str, "rows" | "stacks" | "scattered"
        board_obj: Board object to get surface Z coordinate
        cam: Camera object (optional, used to determine opposite side)
    """
    if not captured_pieces_config:
        return
    
    pool = get_piece_pool()
    board_z = board_obj.location.z
    corners = get_board_corners_world(board_obj)
    
    if len(corners) < 4:
        return  # Can't place pieces without board corners
    
    # Get board dimensions for zone-based placement
    min_x = min(c.x for c in corners)
    max_x = max(c.x for c in corners)
    min_y = min(c.y for c in corners)
    max_y = max(c.y for c in corners)
    square_size = get_square_size(board_obj)
    board_center = board_obj.location
    
    # Offset from board edge
    capture_offset = square_size * 1.2  # 1.2 squares away from board
    
    # Determine which side is opposite to camera
    camera_side = None  # "left" or "right"
    if cam:
        cam_pos = cam.location
        # Determine camera side relative to board center
        if cam_pos.x < board_center.x:
            camera_side = "left"  # Camera is on left, place pieces on right
        else:
            camera_side = "right"  # Camera is on right, place pieces on left
    
    # Track placed pieces for organized layouts
    placed_positions = []
    
    for piece_config in captured_pieces_config:
        piece_type = piece_config.get("type")
        if not piece_type or piece_type not in PIECE_MODEL_MAP:
            continue
        
        # Determine position
        if "position" in piece_config:
            # Explicit position [x, y]
            pos = piece_config["position"]
            if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                x, y = pos[0], pos[1]
                # Z is automatically set to board surface
                z = board_z
        elif "zone" in piece_config:
            # Zone-based placement (relative to camera if camera_side is known)
            zone = piece_config.get("zone", "left")
            layout = piece_config.get("layout", "rows")
            
            # Map zone relative to camera position
            if camera_side:
                # If camera side is known, map zones to opposite side
                if zone == "left":
                    # Left relative to camera means right side of board (opposite camera)
                    x = max_x + capture_offset if camera_side == "left" else min_x - capture_offset
                elif zone == "right":
                    # Right relative to camera means left side of board (opposite camera)
                    x = min_x - capture_offset if camera_side == "right" else max_x + capture_offset
                else:  # "both"
                    # Place on opposite side of camera
                    x = max_x + capture_offset if camera_side == "left" else min_x - capture_offset
            else:
                # No camera info, use absolute zones
                if zone == "left":
                    x = min_x - capture_offset
                elif zone == "right":
                    x = max_x + capture_offset
                else:  # "both" - alternate
                    x = random.choice([min_x - capture_offset, max_x + capture_offset])
            
            # Determine Y position based on layout
            if layout == "rows":
                # Place in rows, spaced by piece height
                y = min_y + (len(placed_positions) % 8) * square_size * 0.8
            elif layout == "stacks":
                # Stack pieces
                y = min_y + square_size * (len(placed_positions) // 4)
            else:  # "scattered"
                # Random Y within capture area
                y = random.uniform(min_y - square_size, max_y + square_size)
            
            z = board_z
        else:
            continue  # Skip invalid config
        
        # Create piece name for off-board piece
        off_board_name = f"{PIECE_PREFIX}{piece_type}_captured_{len(placed_positions)}"
        
        # Get template piece to copy
        model_name = PIECE_MODEL_MAP.get(piece_type)
        if not model_name or model_name not in bpy.data.objects:
            continue
        
        src = bpy.data.objects[model_name]
        
        # Create piece object
        new_obj = src.copy()
        new_obj.data = src.data  # Share mesh data
        new_obj.name = off_board_name
        bpy.context.collection.objects.link(new_obj)
        
        # Set position on board surface
        new_obj.location = (x, y, z)
        
        # Make visible
        new_obj.hide_render = False
        new_obj.hide_viewport = False
        
        # Track for pool cleanup
        pool.all_pieces.append(new_obj)
        if off_board_name not in pool.active_pieces:
            pool.active_pieces[off_board_name] = new_obj
        
        placed_positions.append((x, y))


# ================================================================
# LIGHTING SYSTEM
# ================================================================

def configure_scene_lighting(lighting_config):
    """Configure scene lighting based on preset and parameters.
    
    Args:
        lighting_config: Dictionary with lighting configuration:
            - preset: str, "indoor" | "outdoor_sunny" | "outdoor_cloudy" | "evening" | "artificial" (default: "indoor")
            - intensity: float, multiplier (default: 1.0)
            - color_temperature: int, Kelvin (default: 5500)
            - main_angle: float, elevation angle in degrees (default: 45.0)
            - main_direction: float, azimuth in degrees (default: 0.0)
            - shadow_softness: float, 0.0 (hard) to 1.0 (soft) (default: 0.5)
            - multiple_sources: bool, use multiple lights (default: false)
    """
    if not lighting_config:
        return
    
    scene = bpy.context.scene
    preset = lighting_config.get("preset", "indoor")
    intensity = lighting_config.get("intensity", 1.0)
    color_temp = lighting_config.get("color_temperature", 5500)
    main_angle = radians(lighting_config.get("main_angle", 45.0))
    main_direction = radians(lighting_config.get("main_direction", 0.0))
    shadow_softness = lighting_config.get("shadow_softness", 0.5)
    multiple_sources = lighting_config.get("multiple_sources", False)
    
    # Clear existing lights (optional - you may want to keep them)
    # Uncomment if you want to replace all lights:
    # for obj in bpy.data.objects:
    #     if obj.type == 'LIGHT':
    #         bpy.data.objects.remove(obj, do_unlink=True)
    
    # Convert color temperature to RGB
    # Simplified blackbody approximation
    if color_temp <= 1000:
        color_temp = 1000
    elif color_temp >= 40000:
        color_temp = 40000
    
    # Blackbody color calculation (simplified)
    temp_kelvin = color_temp / 100.0
    red = 1.0 if temp_kelvin <= 66 else (329.698727446 * ((temp_kelvin - 60) ** -0.1332047592)) / 255.0
    green = (99.4708025861 * (temp_kelvin - 10) ** -0.0755148492) / 255.0 if temp_kelvin <= 66 else (288.1221695283 * ((temp_kelvin - 60) ** -0.0755148492)) / 255.0
    blue = 0.0 if temp_kelvin >= 66 else (138.5177312231 * (temp_kelvin - 10) ** -0.0428426271) / 255.0
    
    # Clamp values
    red = max(0.0, min(1.0, red))
    green = max(0.0, min(1.0, green))
    blue = max(0.0, min(1.0, blue))
    
    # Normalize for white balance
    max_val = max(red, green, blue)
    if max_val > 0:
        red /= max_val
        green /= max_val
        blue /= max_val
    
    light_color = (red, green, blue)
    
    # Find or create main light
    main_light_name = "MainLight"
    if main_light_name in bpy.data.objects:
        main_light = bpy.data.objects[main_light_name]
    else:
        light_data = bpy.data.lights.new(name=main_light_name, type='SUN')
        main_light = bpy.data.objects.new(name=main_light_name, object_data=light_data)
        bpy.context.collection.objects.link(main_light)
    
    main_light.data.type = 'SUN' if preset in ["outdoor_sunny", "outdoor_cloudy"] else 'AREA'
    
    # Configure based on preset
    if preset == "outdoor_sunny":
        main_light.data.energy = 10.0 * intensity
        if main_light.data.type == 'SUN':
            main_light.data.angle = radians(0.5)  # Hard shadows
    elif preset == "outdoor_cloudy":
        main_light.data.energy = 5.0 * intensity
        if main_light.data.type == 'SUN':
            main_light.data.angle = radians(2.0)  # Softer shadows
        elif main_light.data.type == 'AREA':
            main_light.data.size = 5.0
    elif preset == "evening":
        main_light.data.energy = 3.0 * intensity
        if main_light.data.type == 'SUN':
            main_light.data.angle = radians(1.5)
        elif main_light.data.type == 'AREA':
            main_light.data.size = 3.0 * shadow_softness
    elif preset == "artificial":
        main_light.data.type = 'SPOT'
        main_light.data.energy = 50.0 * intensity
        main_light.data.spot_size = radians(60.0)
        main_light.data.spot_blend = 0.3
    else:  # indoor
        main_light.data.energy = 5.0 * intensity
        if main_light.data.type == 'SUN':
            main_light.data.angle = radians(1.0 * shadow_softness)
        elif main_light.data.type == 'AREA':
            main_light.data.size = 3.0 * shadow_softness
    
    # Set color
    main_light.data.color = light_color
    
    # Position light based on angle and direction
    board_obj = bpy.data.objects[BOARD_NAME]
    center = board_obj.location
    distance = 20.0
    
    # Calculate light position (spherical coordinates)
    light_x = center.x + distance * cos(main_angle) * cos(main_direction)
    light_y = center.y + distance * cos(main_angle) * sin(main_direction)
    light_z = center.z + distance * sin(main_angle)
    
    main_light.location = (light_x, light_y, light_z)
    
    # Point light at board center
    direction = center - main_light.location
    direction.normalize()
    
    # For SUN, use rotation instead of location
    if main_light.data.type == 'SUN':
        quat = (-direction).to_track_quat('-Z', 'Y')
        main_light.rotation_euler = quat.to_euler()
    else:
        # For other lights, track to board
        # Check if constraint already exists
        track_constraint = None
        for c in main_light.constraints:
            if c.type == 'TRACK_TO':
                track_constraint = c
                break
        
        if track_constraint is None:
            track_constraint = main_light.constraints.new(type='TRACK_TO')
        
        track_constraint.target = board_obj
        track_constraint.track_axis = 'TRACK_NEGATIVE_Z'
        track_constraint.up_axis = 'UP_Y'
    
    # Add fill light if multiple sources enabled
    if multiple_sources:
        fill_light_name = "FillLight"
        if fill_light_name in bpy.data.objects:
            fill_light = bpy.data.objects[fill_light_name]
        else:
            fill_light_data = bpy.data.lights.new(name=fill_light_name, type='AREA')
            fill_light = bpy.data.objects.new(name=fill_light_name, object_data=fill_light_data)
            bpy.context.collection.objects.link(fill_light)
        
        fill_light.data.energy = 2.0 * intensity
        fill_light.data.color = light_color
        fill_light.data.size = 5.0
        
        # Position fill light opposite to main light
        fill_angle = main_angle + pi  # Opposite direction
        fill_direction = main_direction + pi
        fill_x = center.x + distance * cos(fill_angle) * cos(fill_direction) * 0.7
        fill_y = center.y + distance * cos(fill_angle) * sin(fill_direction) * 0.7
        fill_z = center.z + distance * sin(fill_angle) * 0.7
        
        fill_light.location = (fill_x, fill_y, fill_z)
        
        # Check if constraint already exists
        fill_constraint = None
        for c in fill_light.constraints:
            if c.type == 'TRACK_TO':
                fill_constraint = c
                break
        
        if fill_constraint is None:
            fill_constraint = fill_light.constraints.new(type='TRACK_TO')
        
        fill_constraint.target = board_obj
        fill_constraint.track_axis = 'TRACK_NEGATIVE_Z'
        fill_constraint.up_axis = 'UP_Y'


# ================================================================
# SEGMENTATION MAP GENERATION
# ================================================================

def get_segmentation_material(color, material_name):
    """Get or create a segmentation material with specified color.
    
    Args:
        color: RGBA tuple (r, g, b, a) in [0, 1]
        material_name: Name for the material
    
    Returns:
        Material object
    """
    if material_name in bpy.data.materials:
        mat = bpy.data.materials[material_name]
        # Update color even if material exists (in case it was changed)
        if hasattr(mat, 'node_tree') and mat.node_tree:
            nodes = mat.node_tree.nodes
            # Find emission node and update color
            for node in nodes:
                if node.type == 'EMISSION':
                    node.inputs['Color'].default_value = color
                    break
    else:
        mat = bpy.data.materials.new(name=material_name)
        # use_nodes is deprecated in Blender 5.0+, but still works
        # New materials use nodes by default
        if hasattr(mat, 'use_nodes'):
            mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        
        # Clear default nodes
        nodes.clear()
        
        # Create emission shader for flat color
        output = nodes.new(type='ShaderNodeOutputMaterial')
        emission = nodes.new(type='ShaderNodeEmission')
        
        # Set emission color
        emission.inputs['Color'].default_value = color
        emission.inputs['Strength'].default_value = 1.0
        
        # Connect emission to output
        links.new(emission.outputs['Emission'], output.inputs['Surface'])
    
    return mat


def get_segmentation_key_for_piece(piece_code):
    """Get segmentation key for a piece code.
    
    Args:
        piece_code: Piece code (e.g., "P", "p", "K", etc.)
    
    Returns:
        Segmentation key string
    """
    piece_type_map = {
        "P": "piece_white_pawn",
        "N": "piece_white_knight",
        "B": "piece_white_bishop",
        "R": "piece_white_rook",
        "Q": "piece_white_queen",
        "K": "piece_white_king",
        "p": "piece_black_pawn",
        "n": "piece_black_knight",
        "b": "piece_black_bishop",
        "r": "piece_black_rook",
        "q": "piece_black_queen",
        "k": "piece_black_king",
    }
    
    return piece_type_map.get(piece_code, "background")


def get_segmentation_color_for_piece(piece_code):
    """Get segmentation color for a piece code.
    
    Args:
        piece_code: Piece code (e.g., "P", "p", "K", etc.)
    
    Returns:
        RGBA tuple
    """
    segment_key = get_segmentation_key_for_piece(piece_code)
    return SEGMENTATION_COLORS.get(segment_key, SEGMENTATION_COLORS["background"])


def setup_segmentation_materials():
    """Set up segmentation materials for board, background, captured pieces, and all squares.
    
    These materials are reused across all renders to prevent material accumulation.
    Since we create unique mesh copies per piece during segmentation, materials can be safely shared.
    """
    # Create materials for base types (board, background, captured_pieces)
    for segment_key, color in SEGMENTATION_COLORS.items():
        material_name = f"seg_{segment_key}"
        get_segmentation_material(color, material_name)
    
    # Create materials for each square (64 squares) - reused across all renders
    square_colors = get_square_colors()
    for square, color in square_colors.items():
        material_name = f"seg_square_{square}"
        get_segmentation_material(color, material_name)


# Global storage for mesh data backups during segmentation
_segmentation_mesh_backups = {}

def apply_segmentation_materials():
    """Apply segmentation materials to board, pieces on the board (by square), and captured pieces.
    
    NOTE: Board must be included in segmentation map.
    On-board pieces get unique colors based on their square.
    Captured pieces get one unique color for all.
    
    CRITICAL: Pieces share mesh data, so we temporarily create unique mesh copies
    for each piece during segmentation to allow per-object materials.
    """
    global _segmentation_mesh_backups
    
    # Apply to board (CRITICAL: board must be in segmentation)
    board_obj = bpy.data.objects.get(BOARD_NAME)
    if board_obj and hasattr(board_obj.data, 'materials'):
        board_mat = get_segmentation_material(SEGMENTATION_COLORS["board"], "seg_board")
        # Apply material to board
        if len(board_obj.data.materials) > 0:
            board_obj.data.materials[0] = board_mat
        else:
            board_obj.data.materials.append(board_mat)
    
    # Get square colors for on-board pieces
    square_colors = get_square_colors()
    
    # Apply to pieces - CRITICAL: Create unique mesh data for each piece
    # so they can have different materials even when sharing the same source mesh
    pool = get_piece_pool()
    for piece_name, piece_obj in pool.active_pieces.items():
        # Use the actual Blender object, not the dict key
        actual_obj = bpy.data.objects.get(piece_obj.name)
        if actual_obj is None:
            continue
        
        # CRITICAL: Create unique mesh data copy for this object during segmentation
        # This allows each piece to have its own material without affecting others
        if actual_obj.name not in _segmentation_mesh_backups:
            # Store original mesh data reference
            _segmentation_mesh_backups[actual_obj.name] = actual_obj.data
            # Create unique copy of mesh data
            actual_obj.data = actual_obj.data.copy()
        
        # Use actual_obj.name for square extraction (should match piece_name but be safe)
        obj_name = actual_obj.name
        
        # Check if this is a captured piece (off-board)
        # Format: inst_P_sq_e2 (on-board) or inst_p_captured_0 (captured/off-board)
        if "_captured_" in obj_name:
            # Apply captured pieces color (single unique color for all captured pieces)
            # REUSE material instead of creating unique per-piece (prevents material accumulation)
            captured_color = SEGMENTATION_COLORS["captured_pieces"]
            captured_mat_name = "seg_captured_pieces"  # Single material for all captured pieces
            captured_mat = get_segmentation_material(captured_color, captured_mat_name)
            
            # Now we can safely assign to data.materials since mesh is unique
            if hasattr(actual_obj.data, 'materials'):
                if len(actual_obj.data.materials) > 0:
                    actual_obj.data.materials[0] = captured_mat
                else:
                    actual_obj.data.materials.append(captured_mat)
            continue
        
        # Extract square name from object name
        # Format: inst_P_sq_e2 -> extract "sq_e2" -> extract "e2"
        name_parts = obj_name.split('_')
        square_name = None
        for i, part in enumerate(name_parts):
            if part == "sq" and i + 1 < len(name_parts):
                # Next part should be the square (e.g., "e2")
                square_name = name_parts[i + 1]
                break
        
        if square_name and square_name in square_colors:
            # On-board piece: use square-based color
            # REUSE material by square instead of creating unique per-piece (prevents material accumulation)
            color = square_colors[square_name]
            material_name = f"seg_square_{square_name}"  # Reuse existing material from setup_segmentation_materials()
            seg_mat = get_segmentation_material(color, material_name)
            
            # Now we can safely assign to data.materials since mesh is unique
            if hasattr(actual_obj.data, 'materials'):
                if len(actual_obj.data.materials) > 0:
                    actual_obj.data.materials[0] = seg_mat
                else:
                    actual_obj.data.materials.append(seg_mat)
        else:
            # Fallback: if square extraction failed, use background color
            if square_name:
                print(f"Warning: Square '{square_name}' not found in square_colors for piece {obj_name}", flush=True)
            else:
                print(f"Warning: Could not extract square from piece name: {obj_name} (parts: {name_parts})", flush=True)
            # Use background color as fallback
            # REUSE material instead of creating unique per-piece (prevents material accumulation)
            fallback_color = SEGMENTATION_COLORS["background"]
            fallback_mat_name = "seg_background"  # Reuse existing material from setup_segmentation_materials()
            fallback_mat = get_segmentation_material(fallback_color, fallback_mat_name)
            if hasattr(actual_obj.data, 'materials'):
                if len(actual_obj.data.materials) > 0:
                    actual_obj.data.materials[0] = fallback_mat
                else:
                    actual_obj.data.materials.append(fallback_mat)


# Global storage for original materials (per-object)
_original_materials = {}

def store_original_materials():
    """Store original materials before applying segmentation materials."""
    global _original_materials
    _original_materials.clear()
    
    # Store board materials
    board_obj = bpy.data.objects.get(BOARD_NAME)
    if board_obj and hasattr(board_obj.data, 'materials'):
        if len(board_obj.data.materials) > 0:
            _original_materials[board_obj.name] = board_obj.data.materials[0]
    
    # Store piece materials (both on-board and captured pieces)
    pool = get_piece_pool()
    for piece_name, piece_obj in pool.active_pieces.items():
        if piece_obj.name not in bpy.data.objects:
            continue
        if hasattr(piece_obj.data, 'materials') and len(piece_obj.data.materials) > 0:
            _original_materials[piece_obj.name] = piece_obj.data.materials[0]

def restore_original_materials():
    """Restore original materials and mesh data after segmentation render."""
    global _original_materials, _segmentation_mesh_backups
    
    # Restore board materials
    board_obj = bpy.data.objects.get(BOARD_NAME)
    if board_obj and board_obj.name in _original_materials and hasattr(board_obj.data, 'materials'):
        original_mat = _original_materials[board_obj.name]
        if len(board_obj.data.materials) > 0:
            board_obj.data.materials[0] = original_mat
        else:
            board_obj.data.materials.append(original_mat)
    
    # Restore piece materials and mesh data (both on-board and captured pieces)
    pool = get_piece_pool()
    for piece_name, piece_obj in pool.active_pieces.items():
        if piece_obj.name not in bpy.data.objects:
            continue
        
        actual_obj = bpy.data.objects.get(piece_obj.name)
        if actual_obj is None:
            continue
        
        # CRITICAL: Restore original mesh data (shared mesh) after segmentation
        if actual_obj.name in _segmentation_mesh_backups:
            original_mesh = _segmentation_mesh_backups[actual_obj.name]
            # Delete the temporary unique mesh copy
            temp_mesh = actual_obj.data
            actual_obj.data = original_mesh
            # Clean up temporary mesh if no longer used
            if temp_mesh.users == 0:
                try:
                    bpy.data.meshes.remove(temp_mesh)
                except:
                    pass
            del _segmentation_mesh_backups[actual_obj.name]
        
        # Restore original material
        if actual_obj.name in _original_materials and hasattr(actual_obj.data, 'materials'):
            original_mat = _original_materials[actual_obj.name]
            if len(actual_obj.data.materials) > 0:
                actual_obj.data.materials[0] = original_mat
            else:
                actual_obj.data.materials.append(original_mat)
    
    _original_materials.clear()
    _segmentation_mesh_backups.clear()


def render_segmentation_map(scene, output_path):
    """Render segmentation map with flat colors for each object type.
    
    Args:
        scene: Blender scene
        output_path: Path to save segmentation map
    """
    # Store original materials BEFORE applying segmentation materials
    store_original_materials()
    
    # Apply segmentation materials
    apply_segmentation_materials()
    
    # Store original render settings
    original_filepath = scene.render.filepath
    
    # Disable all lights for flat color rendering (or use ambient light)
    # Temporarily hide/disable lights for pure color output
    original_lights = []
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT':
            original_lights.append((obj, obj.hide_render))
            obj.hide_render = True  # Hide lights
    
    # Create ambient light for visibility (uniform lighting for flat colors)
    ambient_light_name = "SegAmbientLight"
    if ambient_light_name in bpy.data.objects:
        ambient_light = bpy.data.objects[ambient_light_name]
    else:
        light_data = bpy.data.lights.new(name=ambient_light_name, type='AREA')
        ambient_light = bpy.data.objects.new(name=ambient_light_name, object_data=light_data)
        bpy.context.collection.objects.link(ambient_light)
    
    ambient_light.data.energy = 10.0  # Strong ambient for flat colors
    ambient_light.hide_render = False
    ambient_light.location = (0, 0, 10)
    ambient_light.data.size = 20.0  # Large area for uniform lighting
    
    # Render
    scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    
    # Restore original lights
    for obj, original_state in original_lights:
        obj.hide_render = original_state
    
    # Hide ambient light
    if ambient_light_name in bpy.data.objects:
        bpy.data.objects[ambient_light_name].hide_render = True
    
    # Restore original filepath
    scene.render.filepath = original_filepath
    
    # Restore original materials AFTER segmentation render
    restore_original_materials()


# -------------------------------------------------------------
# FEN PARSING
# -------------------------------------------------------------

def parse_fen_board(fen):
    """
    Parse only the board layout portion of a FEN string.
    Returns 8 lists (rank 8 → rank 1), each with 8 entries.
    Each entry: None or a letter ('P','p','R','r', etc.)
    """
    board_part = fen.split()[0]
    rows = board_part.split("/")
    board = []

    for row in rows:
        row_list = []
        for ch in row:
            if ch.isdigit():
                for _ in range(int(ch)):
                    row_list.append(None)
            else:
                row_list.append(ch)
        board.append(row_list)

    return board  # row[0] = rank 8, row[7] = rank 1


# -------------------------------------------------------------
# FEN → PIECES PLACEMENT
# -------------------------------------------------------------

def spawn_fen_board(fen):
    """Place pieces on board using object pooling for efficiency."""
    pool = get_piece_pool()
    
    # Hide all previous pieces (return to pool)
    clear_old_instances()
    
    # Hide template pieces efficiently using cached list
    hide_template_pieces()

    board_data = parse_fen_board(fen)
    board_obj = bpy.data.objects[BOARD_NAME]
    board_z = board_obj.location.z

    files = "abcdefgh"
    
    # Collect all piece names we'll need for this FEN
    needed_piece_names = set()
    for rank_index, row in enumerate(board_data):
        rank_number = 8 - rank_index
        for file_index, piece_code in enumerate(row):
            if piece_code is None or piece_code not in PIECE_MODEL_MAP:
                continue
            square_name = f"sq_{files[file_index]}{rank_number}"
            needed_piece_names.add(f"{PIECE_PREFIX}{piece_code}_{square_name}")

    for rank_index, row in enumerate(board_data):
        rank_number = 8 - rank_index

        for file_index, piece_code in enumerate(row):
            if piece_code is None:
                continue  # empty square

            if piece_code not in PIECE_MODEL_MAP:
                continue

            square_name = f"sq_{files[file_index]}{rank_number}"
            piece_name = f"{PIECE_PREFIX}{piece_code}_{square_name}"
            
            # Delete any duplicate piece with this name that's not in our tracking
            if piece_name in bpy.data.objects:
                existing = bpy.data.objects[piece_name]
                if piece_name not in pool.active_pieces:
                    # It's a duplicate - remove it
                    if existing in pool.all_pieces:
                        pool.all_pieces.remove(existing)
                    # Remove from available_pieces if present
                    for pt in pool.available_pieces:
                        if existing in pool.available_pieces[pt]:
                            pool.available_pieces[pt].remove(existing)
                    bpy.data.objects.remove(existing, do_unlink=True)
            
            # Get piece from pool (reuses existing or creates new)
            new_obj = pool.get_piece(piece_code, square_name, board_z)
            
            if new_obj is None:
                continue
            
            # Ensure piece is visible
            new_obj.hide_render = False
            new_obj.hide_viewport = False


def get_square_size(board_obj):
    """Calculate the size of a chess square from the board object."""
    corners = get_board_corners_world(board_obj)
    if len(corners) < 4:
        return 1.0  # Default fallback
    
    # Calculate board width and height from corners
    width = abs(corners[1].x - corners[0].x)
    height = abs(corners[3].y - corners[0].y)
    
    # Chess board is 8x8 squares
    square_width = width / 8.0
    square_height = height / 8.0
    
    # Return average (squares should be roughly square)
    return (square_width + square_height) / 2.0


def apply_piece_offsets(piece_offset_config, pieces=None):
    """Apply random offsets to pieces using normal distribution.
    
    Args:
        piece_offset_config: Dictionary with offset configuration:
            - enabled: bool, whether to apply offsets
            - distribution: "normal" or "uniform" (default: "normal")
            - mean_x: float, mean offset in X as percentage (default: 0.0)
            - mean_y: float, mean offset in Y as percentage (default: 0.0)
            - std_dev_x: float, standard deviation in X as percentage (default: 15.0)
            - std_dev_y: float, standard deviation in Y as percentage (default: 15.0)
            - max_offset_percent: float, hard limit to clip outliers (default: 45.0)
            - clip_outliers: bool, whether to clip at max_offset (default: true)
        pieces: Optional list of piece objects. If None, uses active pieces from pool.
    """
    if not piece_offset_config.get("enabled", False):
        return
    
    board_obj = bpy.data.objects[BOARD_NAME]
    square_size = get_square_size(board_obj)
    
    # Get pieces to offset
    if pieces is None:
        pool = get_piece_pool()
        pieces = [obj for obj in pool.active_pieces.values() if obj.name in bpy.data.objects]
    
    if not pieces:
        return
    
    # Get configuration with defaults
    distribution = piece_offset_config.get("distribution", "normal")
    mean_x = piece_offset_config.get("mean_x", 0.0)
    mean_y = piece_offset_config.get("mean_y", 0.0)
    std_dev_x = piece_offset_config.get("std_dev_x", 15.0) / 100.0  # Convert % to fraction
    std_dev_y = piece_offset_config.get("std_dev_y", 15.0) / 100.0
    max_offset_percent = piece_offset_config.get("max_offset_percent", 45.0) / 100.0
    clip_outliers = piece_offset_config.get("clip_outliers", True)
    
    # Calculate offset in world units
    max_offset_world = max_offset_percent * square_size
    
    for piece_obj in pieces:
        if piece_obj.name not in bpy.data.objects:
            continue
        
        # Generate offsets
        if distribution == "normal":
            offset_x = random.gauss(mean_x, std_dev_x)
            offset_y = random.gauss(mean_y, std_dev_y)
        else:  # uniform
            offset_x = random.uniform(-max_offset_percent, max_offset_percent)
            offset_y = random.uniform(-max_offset_percent, max_offset_percent)
        
        # Clip outliers if requested
        if clip_outliers:
            offset_x = max(-max_offset_percent, min(max_offset_percent, offset_x))
            offset_y = max(-max_offset_percent, min(max_offset_percent, offset_y))
        
        # Convert to world units and apply
        offset_x_world = offset_x * square_size
        offset_y_world = offset_y * square_size
        
        piece_obj.location.x += offset_x_world
        piece_obj.location.y += offset_y_world


def apply_piece_rotations(piece_rotation_config, pieces=None):
    """Apply random rotations to pieces around Z-axis (vertical).
    
    Args:
        piece_rotation_config: Dictionary with rotation configuration:
            - enabled: bool, whether to apply rotations
            - distribution: "normal" or "uniform" (default: "uniform")
            - min_angle: float, minimum rotation angle in degrees (default: -15.0)
            - max_angle: float, maximum rotation angle in degrees (default: 15.0)
            - mean_angle: float, mean rotation angle in degrees (default: 0.0, only used for normal)
            - std_dev_angle: float, standard deviation in degrees (default: 8.0, only used for normal)
            - clip_angle: float, hard limit to clip outliers in degrees (default: 30.0)
        pieces: Optional list of piece objects. If None, uses active pieces from pool.
    """
    if not piece_rotation_config.get("enabled", False):
        return
    
    # Get pieces to rotate
    if pieces is None:
        pool = get_piece_pool()
        pieces = [obj for obj in pool.active_pieces.values() if obj.name in bpy.data.objects]
    
    if not pieces:
        return
    
    # Get configuration with defaults
    distribution = piece_rotation_config.get("distribution", "uniform")
    min_angle = piece_rotation_config.get("min_angle", -15.0)
    max_angle = piece_rotation_config.get("max_angle", 15.0)
    mean_angle = piece_rotation_config.get("mean_angle", 0.0)
    std_dev_angle = piece_rotation_config.get("std_dev_angle", 8.0)
    clip_angle = piece_rotation_config.get("clip_angle", 30.0)
    clip_outliers = piece_rotation_config.get("clip_outliers", True)
    
    for piece_obj in pieces:
        if piece_obj.name not in bpy.data.objects:
            continue
        
        # Generate rotation angle
        if distribution == "normal":
            angle_deg = random.gauss(mean_angle, std_dev_angle)
        else:  # uniform
            angle_deg = random.uniform(min_angle, max_angle)
        
        # Clip outliers if requested
        if clip_outliers:
            angle_deg = max(-clip_angle, min(clip_angle, angle_deg))
        
        # Convert to radians and apply rotation around Z-axis
        angle_rad = radians(angle_deg)
        
        # Get current rotation
        current_rotation = piece_obj.rotation_euler.copy()
        
        # Apply rotation around Z-axis (vertical axis)
        current_rotation.z += angle_rad
        
        # Update piece rotation
        piece_obj.rotation_euler = current_rotation


# -------------------------------------------------------------
# CAMERA / RENDERING HELPERS
# -------------------------------------------------------------

def get_board_corners_world(board_obj):
    """
    Return 4 world-space corners of the board:
    0 bottom-left, 1 bottom-right, 2 top-right, 3 top-left
    """
    local_bb = [Vector(corner) for corner in board_obj.bound_box]
    xs = [v.x for v in local_bb]
    ys = [v.y for v in local_bb]
    zs = [v.z for v in local_bb]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    z = min(zs)

    corners_local = [
        Vector((min_x, min_y, z)),
        Vector((max_x, min_y, z)),
        Vector((max_x, max_y, z)),
        Vector((min_x, max_y, z)),
    ]
    return [(board_obj.matrix_world @ c) for c in corners_local]


def world_to_pixel(scene, cam, world_coord):
    """
    Convert world coordinate to pixel coordinate.
    Returns (x,y) as integer pixel coordinates or None if not visible.
    """
    co_ndc = world_to_camera_view(scene, cam, world_coord)
    if co_ndc.z < 0:
        return None

    x = co_ndc.x * scene.render.resolution_x
    y = (1 - co_ndc.y) * scene.render.resolution_y
    # Return as integer pixel coordinates
    return int(round(x)), int(round(y))


def randomize_camera_around_board(cam, board_obj, camera_radius=None, elevation=None, azimuth=None,
                                   camera_config=None):
    """Set camera position and orientation with optional variations.
    
    Args:
        cam: Camera object
        board_obj: Board object
        camera_radius: Optional radius override
        elevation: Optional elevation override (degrees)
        azimuth: Optional azimuth override (degrees)
        camera_config: Optional dictionary with camera variations:
            - tilt: float, rotation around view axis (degrees, default: 0)
            - roll: float, side-to-side tilt (degrees, default: 0)
            - fov: float, focal length in mm (default: 18.0)
            - position_jitter: [x, y, z] array, max jitter in world units (default: [0, 0, 0])
            - height_offset: float, vertical offset in world units (default: 0)
    """
    center = board_obj.location

    # Use provided values or randomize
    if elevation is not None:
        elev = radians(elevation)
    else:
        elev = random.uniform(ELEVATION_MIN, ELEVATION_MAX)
    
    if azimuth is not None:
        azim = radians(azimuth)
    else:
        azim = random.uniform(AZIMUTH_MIN, AZIMUTH_MAX)
    
    r = camera_radius if camera_radius is not None else CAMERA_RADIUS

    # Base position
    x = center.x + r * cos(elev) * cos(azim)
    y = center.y + r * cos(elev) * sin(azim)
    z = center.z + r * sin(elev)
    
    # Apply position jitter if specified
    if camera_config and "position_jitter" in camera_config:
        jitter = camera_config["position_jitter"]
        if isinstance(jitter, (list, tuple)) and len(jitter) >= 3:
            x += random.uniform(-jitter[0], jitter[0])
            y += random.uniform(-jitter[1], jitter[1])
            z += random.uniform(-jitter[2], jitter[2])
    
    # Apply height offset if specified
    if camera_config and "height_offset" in camera_config:
        height_offset = camera_config["height_offset"]
        z += height_offset
    
    cam.location = (x, y, z)

    # Base orientation (look at board center)
    direction = center - cam.location
    direction.normalize()

    quat = direction.to_track_quat('-Z', 'Y')
    cam.rotation_euler = quat.to_euler()
    
    # Apply tilt (rotation around view axis)
    if camera_config and "tilt" in camera_config:
        tilt = radians(camera_config["tilt"])
        # Apply tilt around view axis (Z-axis of camera)
        euler = Euler(cam.rotation_euler, 'XYZ')
        euler.z += tilt
        cam.rotation_euler = euler
    
    # Apply roll (side-to-side tilt)
    if camera_config and "roll" in camera_config:
        roll = radians(camera_config["roll"])
        # Apply roll by rotating around camera X-axis
        euler = Euler(cam.rotation_euler, 'XYZ')
        euler.x += roll
        cam.rotation_euler = euler
    
    # Configure camera FOV (focal length)
    if cam.data.type == 'PERSP':
        if camera_config and "fov" in camera_config:
            cam.data.lens = camera_config["fov"]
        else:
            # Default: phone-like wide angle view (~75 degrees)
            cam.data.lens = 18.0


def collect_piece_screen_positions(scene, cam):
    """Collect piece positions in pixel coordinates."""
    pieces = []
    # Use piece pool's active pieces for faster iteration
    pool = get_piece_pool()
    for piece_name, obj in pool.active_pieces.items():
        if obj.name in bpy.data.objects:  # Verify it still exists
            px = world_to_pixel(scene, cam, obj.location)
            if px is not None:
                pieces.append({
                    "name": obj.name,
                    "x": px[0],  # Integer pixel coordinate
                    "y": px[1],  # Integer pixel coordinate
                })
    return pieces


# ================================================================
# RENDER ONE IMAGE
# ================================================================

def configure_eevee_settings(scene, resolution_x=None, resolution_y=None):
    """Configure EEVEE settings for optimal performance (cached)."""
    global _eevee_settings_configured
    
    scene.render.engine = 'BLENDER_EEVEE'
    
    # Set resolution (can be overridden per render)
    scene.render.resolution_x = resolution_x if resolution_x is not None else IMG_RES_X
    scene.render.resolution_y = resolution_y if resolution_y is not None else IMG_RES_Y
    scene.render.resolution_percentage = 100
    
    # Enable object index pass for segmentation (if available)
    # Use context view layer instead of scene.view_layers.active
    try:
        view_layer = bpy.context.view_layer
        if hasattr(view_layer, 'use_pass_object_index'):
            view_layer.use_pass_object_index = True
    except (AttributeError, RuntimeError):
        # Fallback: try to access via scene if context not available
        if len(scene.view_layers) > 0:
            view_layer = scene.view_layers[0]
            if hasattr(view_layer, 'use_pass_object_index'):
                view_layer.use_pass_object_index = True
    
    if _eevee_settings_configured:
        return  # Other settings already configured
    
    # Optimize EEVEE settings for speed (Blender 4.0 API)
    if hasattr(scene.eevee, 'taa_render_samples'):
        scene.eevee.taa_render_samples = 8  # Reduced from 32 for much faster rendering (acceptable quality for dataset generation)
    if hasattr(scene.eevee, 'use_taa_reprojection'):
        scene.eevee.use_taa_reprojection = False  # Disable reprojection
    if hasattr(scene.eevee, 'use_bloom'):
        scene.eevee.use_bloom = False
    if hasattr(scene.eevee, 'use_ssr'):
        scene.eevee.use_ssr = False
    if hasattr(scene.eevee, 'use_gtao'):
        scene.eevee.use_gtao = False
    if hasattr(scene.eevee, 'use_soft_shadows'):
        scene.eevee.use_soft_shadows = False  # Disable soft shadows
    if hasattr(scene.eevee, 'shadow_cube_size'):
        scene.eevee.shadow_cube_size = '512'  # Smaller shadow maps
    
    _eevee_settings_configured = True

def render_one(image_index=0, fen=None, output_dir=None, camera_radius=None, elevation=None, azimuth=None, 
               game_number=None, move_number=None, filename=None, task_config=None):
    global _render_count
    
    # Periodic cleanup to prevent memory growth (very frequent to prevent progressive slowdown)
    _render_count += 1
    if _render_count % CLEANUP_INTERVAL == 0:
        pool = get_piece_pool()
        pool.periodic_cleanup()
        # Also aggressively limit all_pieces list size
        if len(pool.all_pieces) > 300:  # Lower hard limit to prevent accumulation
            # Keep only the most recent pieces
            excess = pool.all_pieces[:-300]
            for obj in excess:
                if obj.name in bpy.data.objects:
                    # Remove object and its mesh if not shared
                    mesh = obj.data if hasattr(obj, 'data') else None
                    bpy.data.objects.remove(obj, do_unlink=True)
                    # Clean up orphaned mesh
                    if mesh and mesh.users == 0:
                        try:
                            bpy.data.meshes.remove(mesh)
                        except:
                            pass
            pool.all_pieces = pool.all_pieces[-300:]
        
        # Clean up orphaned segmentation materials that are no longer used
        # Keep only materials that start with "seg_" and are actively being used
        try:
            materials_to_remove = []
            for mat in bpy.data.materials:
                # Only clean up segmentation materials that are orphaned
                if mat.name.startswith("seg_") and mat.users == 0:
                    # Double-check: ensure this isn't a material we want to keep
                    # (shouldn't happen since we reuse materials, but be safe)
                    if not any(mat.name == f"seg_{key}" for key in SEGMENTATION_COLORS.keys()):
                        square_colors = get_square_colors()
                        if not any(mat.name == f"seg_square_{sq}" for sq in square_colors.keys()):
                            materials_to_remove.append(mat)
            
            for mat in materials_to_remove:
                try:
                    bpy.data.materials.remove(mat)
                except:
                    pass
        except:
            pass  # Silently fail if cleanup fails
    
    scene = bpy.context.scene
    
    # Hide template pieces efficiently (already done in spawn_fen_board, but ensure here too)
    hide_template_pieces()
    
    col = bpy.data.collections["Chess Game"]
    col.hide_render = True

    # Configure EEVEE settings
    # Check for resolution override in task_config
    res_x = None
    res_y = None
    if task_config and "image" in task_config:
        image_config = task_config["image"]
        res_x = image_config.get("resolution_x")
        res_y = image_config.get("resolution_y")
    
    configure_eevee_settings(scene, res_x, res_y)
    
    # Set up segmentation materials (once)
    setup_segmentation_materials()

    board = bpy.data.objects[BOARD_NAME]
    cam = bpy.data.objects[CAMERA_NAME]
    


    # 1) place pieces from FEN
    spawn_fen_board(fen)
    
    # Apply piece offsets if configured
    if task_config and "piece_offset" in task_config:
        apply_piece_offsets(task_config["piece_offset"])
    
    # Apply piece rotations if configured
    if task_config and "piece_rotation" in task_config:
        apply_piece_rotations(task_config["piece_rotation"])

    # 2) camera viewpoint (use provided settings or randomize)
    # Build camera config from task_config if provided
    camera_config = None
    if task_config and "camera" in task_config:
        camera_config = task_config["camera"]
        # Extract base parameters for backward compatibility
        camera_radius = camera_config.get("radius", camera_radius)
        elevation = camera_config.get("elevation", elevation)
        azimuth = camera_config.get("azimuth", azimuth)
    
    randomize_camera_around_board(cam, board, camera_radius, elevation, azimuth, camera_config)
    
    # 3) Place captured pieces AFTER camera is positioned (opposite side)
    if task_config and "captured_pieces" in task_config:
        place_captured_pieces(task_config["captured_pieces"], board, cam)
    
    # Configure lighting if specified
    if task_config and "lighting" in task_config:
        configure_scene_lighting(task_config["lighting"])
    
    # Load models if specified
    if task_config:
        if "board_model" in task_config:
            load_board_model(task_config["board_model"])
        if "piece_model_set" in task_config:
            load_piece_set(task_config["piece_model_set"])
    
    # Note: View layer update moved to batch level for efficiency

    # 4) annotations (pixel coordinates)
    corners_world = get_board_corners_world(board)
    corners_px = []
    for idx, cw in enumerate(corners_world):
        px = world_to_pixel(scene, cam, cw)
        if px is None:
            x, y = None, None
        else:
            x, y = px  # Already integer pixel coordinates
        corners_px.append({
            "corner_index": idx,
            "x": x,
            "y": y
        })

    pieces_px = collect_piece_screen_positions(scene, cam)

    # 5) ensure output directory
    if output_dir is None:
        out_dir = bpy.path.abspath(OUTPUT_DIR)
    else:
        # Convert to absolute path if relative
        if os.path.isabs(output_dir):
            out_dir = output_dir
        else:
            # Relative paths: try to resolve from current working directory first
            # (which should be the project root when called from testing.py)
            cwd = os.getcwd()
            potential_path = os.path.join(cwd, output_dir)
            if os.path.exists(os.path.dirname(potential_path)) or os.path.exists(cwd):
                out_dir = os.path.abspath(potential_path)
            else:
                # Fallback: relative to blend file directory
                blend_dir = os.path.dirname(bpy.data.filepath)
                out_dir = os.path.abspath(os.path.join(blend_dir, output_dir))
        out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    # Generate filename based on game/move or use provided filename
    if filename:
        base_name = filename
    elif game_number is not None and move_number is not None:
        base_name = f"game_{game_number:04d}_move_{move_number:02d}"
    else:
        base_name = f"img_{image_index:06d}"
    
    img_path = os.path.join(out_dir, f"{base_name}.png")
    json_path = os.path.join(out_dir, f"{base_name}.json")

    # Final check: ensure template pieces are hidden before rendering
    # (Already hidden, but double-check efficiently)
    hide_template_pieces()
    
    # Note: View layer update removed here for performance - it's done at batch level instead
    # This avoids per-render overhead while still ensuring visibility updates

    # 6) render image
    scene.render.filepath = img_path
    bpy.ops.render.render(write_still=True)

    # 6) render segmentation map if enabled
    segmentation_path = None
    generate_segmentation = task_config.get("generate_segmentation", True) if task_config else True
    
    if generate_segmentation:
        segmentation_path = os.path.join(out_dir, f"{base_name}_segmentation.png")
        render_segmentation_map(scene, segmentation_path)

    # 8) write json (queued for batch writing)
    # Get actual resolution used
    actual_res_x = scene.render.resolution_x
    actual_res_y = scene.render.resolution_y
    
    data = {
        "image": os.path.basename(img_path),
        "resolution": [actual_res_x, actual_res_y],
        "board_corners": corners_px,
        "pieces": pieces_px,
        "fen": fen,
    }
    
    if segmentation_path:
        data["segmentation_map"] = os.path.basename(segmentation_path)
        # Include base colors (board, background, captured_pieces)
        segmentation_color_dict = {
            k: list(v[:3]) for k, v in SEGMENTATION_COLORS.items()  # RGB only, no alpha
        }
        # Include all square colors
        square_colors = get_square_colors()
        for square, color in square_colors.items():
            segmentation_color_dict[f"square_{square}"] = list(color[:3])  # RGB only, no alpha
        
        data["segmentation_colors"] = segmentation_color_dict
    
    queue_json_write(json_path, data)

    # Progress output (can be parsed by testing.py)
    print(f"PROGRESS:{image_index}:{img_path}", flush=True)
    # Don't print the full paths to reduce noise, but keep for debugging if needed
    # print("Rendered:", img_path)
    # print("Saved annotations:", json_path)


# ================================================================
# COMMAND LINE ARGUMENT PARSING
# ================================================================

def parse_args():
    """Parse command line arguments when run from Blender."""
    # Get arguments after '--' separator
    argv = sys.argv
    if "--" not in argv:
        return None
    
    argv = argv[argv.index("--") + 1:]
    
    parser = argparse.ArgumentParser(description="Render chess FEN positions")
    parser.add_argument("--num-renders", type=int, default=3, help="Number of renders")
    parser.add_argument("--camera-radius", type=float, default=None, help="Camera radius")
    parser.add_argument("--elevation-min", type=float, default=None, help="Min elevation (degrees)")
    parser.add_argument("--elevation-max", type=float, default=None, help="Max elevation (degrees)")
    parser.add_argument("--azimuth-min", type=float, default=None, help="Min azimuth (degrees)")
    parser.add_argument("--azimuth-max", type=float, default=None, help="Max azimuth (degrees)")
    parser.add_argument("--fen-file", type=str, default=None, help="File with FEN strings (one per line)")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for renders")
    parser.add_argument("--batch-size", type=int, default=None, help="Render in batches of this size (default: render all at once)")
    parser.add_argument("--progress-file", type=str, default=None, help="File to write progress updates to")
    parser.add_argument("--spec-file", type=str, default=None, help="JSON file with per-position specifications (renders array with fen, camera settings)")
    
    return parser.parse_args(argv)


def load_fens_from_file(filepath):
    """Load FEN strings from a file (one per line)."""
    fens = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                fens.append(line)
    return fens


# ================================================================
# MAIN LOOP
# ================================================================

# example FENs you can test
DEFAULT_FENS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
    "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2",
]

if __name__ == "__main__":
    args = parse_args()
    
    if args:
        # Check if using specification file (new format with render_tasks)
        render_tasks = None
        defaults = {}
        if args.spec_file and os.path.exists(args.spec_file):
            with open(args.spec_file, "r", encoding="utf-8") as f:
                spec = json.load(f)
            
            # Try new format first (render_tasks)
            render_tasks = spec.get("render_tasks", [])
            
            # Fallback to old format (renders) for backward compatibility
            if not render_tasks:
                renders_spec = spec.get("renders", [])
                defaults = spec.get("defaults", {})
                if renders_spec:
                    print(f"Loaded legacy specification file with {len(renders_spec)} renders")
                    # Convert old format to new format
                    render_tasks = []
                    for i, render_spec in enumerate(renders_spec):
                        task = {
                            "index": render_spec.get("index", i),
                            "fen": render_spec.get("fen"),
                        }
                        if "camera_radius" in render_spec or "elevation" in render_spec or "azimuth" in render_spec:
                            task["camera"] = {
                                "radius": render_spec.get("camera_radius", defaults.get("camera_radius")),
                                "elevation": render_spec.get("elevation", defaults.get("elevation")),
                                "azimuth": render_spec.get("azimuth", defaults.get("azimuth")),
                            }
                        if "game_number" in render_spec:
                            task["game_number"] = render_spec.get("game_number")
                        if "move_number" in render_spec:
                            task["move_number"] = render_spec.get("move_number")
                        if "filename" in render_spec:
                            task["filename"] = render_spec.get("filename")
                        render_tasks.append(task)
            
            if args.output_dir is None:
                args.output_dir = spec.get("output_dir")
            
            if render_tasks:
                print(f"Loaded specification file with {len(render_tasks)} render tasks")
        
        # Update camera settings from command line or defaults (only for legacy format)
        if args.camera_radius is not None:
            CAMERA_RADIUS = args.camera_radius
        elif defaults and "camera_radius" in defaults:
            CAMERA_RADIUS = defaults["camera_radius"]
        
        if args.elevation_min is not None:
            ELEVATION_MIN = radians(args.elevation_min)
        elif defaults and "elevation_min" in defaults:
            ELEVATION_MIN = radians(defaults["elevation_min"])
        
        if args.elevation_max is not None:
            ELEVATION_MAX = radians(args.elevation_max)
        elif defaults and "elevation_max" in defaults:
            ELEVATION_MAX = radians(defaults["elevation_max"])
        
        if args.azimuth_min is not None:
            AZIMUTH_MIN = radians(args.azimuth_min)
        elif defaults and "azimuth_min" in defaults:
            AZIMUTH_MIN = radians(defaults["azimuth_min"])
        
        if args.azimuth_max is not None:
            AZIMUTH_MAX = radians(args.azimuth_max)
        elif defaults and "azimuth_max" in defaults:
            AZIMUTH_MAX = radians(defaults["azimuth_max"])
        
        # Load FENs (legacy format) or use specification
        if render_tasks:
            # New format: use render_tasks
            num_renders = len(render_tasks)
        elif args.fen_file:
            fens = load_fens_from_file(args.fen_file)
            if not fens:
                print(f"Warning: No FENs found in {args.fen_file}, using defaults")
                fens = DEFAULT_FENS
            num_renders = args.num_renders
        else:
            fens = DEFAULT_FENS
            num_renders = args.num_renders
        
        print(f"Camera settings (defaults):")
        print(f"  Radius: {CAMERA_RADIUS}")
        print(f"  Elevation: {ELEVATION_MIN*180/3.14159:.1f}° - {ELEVATION_MAX*180/3.14159:.1f}°")
        print(f"  Azimuth: {AZIMUTH_MIN*180/3.14159:.1f}° - {AZIMUTH_MAX*180/3.14159:.1f}°")
        print(f"Rendering {num_renders} images...")
        if args.output_dir:
            print(f"Output directory: {args.output_dir}")
        if args.batch_size:
            print(f"Batch size: {args.batch_size}")
        
        # Initialize GPU (once at startup)
        ensure_gpu_initialized()
        
        # Start background JSON writer
        start_json_writer()
        
        # Progress tracking
        start_time = time.time()
        batch_size = args.batch_size if args.batch_size else num_renders
        
        # Render in batches
        for batch_start in range(0, num_renders, batch_size):
            batch_end = min(batch_start + batch_size, num_renders)
            batch_num = batch_start // batch_size + 1
            total_batches = (num_renders + batch_size - 1) // batch_size
            
            if total_batches > 1:
                print(f"Batch {batch_num}/{total_batches}: Rendering images {batch_start} to {batch_end-1}...")
            
            batch_start_time = time.time()
            
            # Update view layer once per batch (more efficient than per render)
            bpy.context.view_layer.update()
            
            for i in range(batch_start, batch_end):
                if render_tasks:
                    # New format: use task configuration
                    task = render_tasks[i]
                    fen = task.get("fen")
                    image_index = task.get("index", i)
                    game_number = task.get("game_number")
                    move_number = task.get("move_number")
                    filename = task.get("filename")
                    
                    # Extract camera params for backward compatibility
                    camera_radius = None
                    elevation = None
                    azimuth = None
                    if "camera" in task:
                        camera_config = task["camera"]
                        camera_radius = camera_config.get("radius")
                        elevation = camera_config.get("elevation")
                        azimuth = camera_config.get("azimuth")
                    
                    # Pass full task config
                    render_start = time.time()
                    render_one(image_index=image_index, fen=fen, output_dir=args.output_dir,
                              camera_radius=camera_radius, elevation=elevation, azimuth=azimuth,
                              game_number=game_number, move_number=move_number, filename=filename,
                              task_config=task)
                else:
                    # Legacy format: random FEN and camera
                    fen = random.choice(fens)
                    camera_radius = None
                    elevation = None
                    azimuth = None
                    image_index = i
                    game_number = None
                    move_number = None
                    filename = None
                    
                    render_start = time.time()
                    render_one(image_index=image_index, fen=fen, output_dir=args.output_dir,
                              camera_radius=camera_radius, elevation=elevation, azimuth=azimuth,
                              game_number=game_number, move_number=move_number, filename=filename,
                              task_config=None)
                render_time = time.time() - render_start
                
                # Write progress to file if specified
                if args.progress_file:
                    with open(args.progress_file, "w", encoding="utf-8") as pf:
                        pf.write(f"{i+1}/{num_renders}\n")
                        pf.write(f"{render_time:.2f}\n")
            
            batch_time = time.time() - batch_start_time
            if total_batches > 1:
                print(f"Batch {batch_num} completed in {batch_time:.2f}s ({batch_time/(batch_end-batch_start):.2f}s per image)")
        
        # Stop JSON writer and wait for all files to be written
        stop_json_writer()
        
        total_time = time.time() - start_time
        avg_time = total_time / num_renders
        print(f"TOTAL_TIME:{total_time:.2f}", flush=True)
        print(f"AVG_TIME:{avg_time:.2f}", flush=True)
        print(f"RENDERED:{num_renders}", flush=True)
        print(f"\n✓ Completed {num_renders} renders in {total_time:.2f}s (avg: {avg_time:.2f}s per image, {num_renders/total_time:.2f} images/sec)")
    else:
        # Default behavior (when run directly in Blender without args)
        for i in range(3):
            fen = random.choice(DEFAULT_FENS)
            render_one(image_index=i, fen=fen)
