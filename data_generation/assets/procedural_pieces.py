#!/usr/bin/env python3
"""
Procedural Chess Piece Generator (Blender)
Creates simple but functional chess pieces using Blender primitives.

Usage:
    blender --background --python procedural_pieces.py

Output:
    - Saves pieces to assets/procedural/ directory
    - Creates a full Tournament Staunton set
    - Exports as .blend and .obj
"""

import bpy
import os
import bmesh
import math
from mathutils import Vector

# Configuration
OUTPUT_DIR = "/home/node/.openclaw/workspace/data_generation/assets/procedural"
SCALE_CM = 0.01  # Blender units to cm
PIECE_HEIGHTS = {
    'king': 9.5 * SCALE_CM,
    'queen': 8.5 * SCALE_CM,
    'rook': 5.5 * SCALE_CM,
    'bishop': 7.0 * SCALE_CM,
    'knight': 6.0 * SCALE_CM,
    'pawn': 5.0 * SCALE_CM,
}

BASE_DIAMETERS = {
    'king': 3.8 * SCALE_CM,
    'queen': 3.5 * SCALE_CM,
    'rook': 3.2 * SCALE_CM,
    'bishop': 3.0 * SCALE_CM,
    'knight': 3.0 * SCALE_CM,
    'pawn': 2.8 * SCALE_CM,
}

def clear_scene():
    """Clear all mesh objects from scene."""
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()
    
    # Clean up materials
    for material in bpy.data.materials:
        if material.name not in ['White', 'Black']:
            bpy.data.materials.remove(material)

def create_material(name, color):
    """Create a simple PBR material."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    # Clear default nodes
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # Create nodes
    output = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    
    # Configure BSDF
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.4
    
    # Link
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_base(name, diameter, height=0.3 * SCALE_CM):
    """Create cylindrical base for piece."""
    bpy.ops.mesh.primitive_cylinder_add(
        radius=diameter / 2,
        depth=height,
        location=(0, 0, height / 2)
    )
    base = bpy.context.active_object
    base.name = f"{name}_base"
    return base

def create_king(color_name, color_rgb):
    """Create a King piece."""
    height = PIECE_HEIGHTS['king']
    diameter = BASE_DIAMETERS['king']
    
    pieces = []
    
    # Base
    base = create_base('king', diameter)
    pieces.append(base)
    
    # Main cylinder (body)
    body_height = height * 0.5
    bpy.ops.mesh.primitive_cylinder_add(
        radius=diameter * 0.35,
        depth=body_height,
        location=(0, 0, 0.3 * SCALE_CM + body_height / 2)
    )
    body = bpy.context.active_object
    body.name = 'king_body'
    pieces.append(body)
    
    # Collar
    collar_height = height * 0.1
    bpy.ops.mesh.primitive_cylinder_add(
        radius=diameter * 0.45,
        depth=collar_height,
        location=(0, 0, 0.3 * SCALE_CM + body_height + collar_height / 2)
    )
    collar = bpy.context.active_object
    collar.name = 'king_collar'
    pieces.append(collar)
    
    # Upper cylinder
    upper_height = height * 0.2
    bpy.ops.mesh.primitive_cylinder_add(
        radius=diameter * 0.3,
        depth=upper_height,
        location=(0, 0, 0.3 * SCALE_CM + body_height + collar_height + upper_height / 2)
    )
    upper = bpy.context.active_object
    upper.name = 'king_upper'
    pieces.append(upper)
    
    # Sphere (head)
    head_y = 0.3 * SCALE_CM + body_height + collar_height + upper_height
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=diameter * 0.35,
        location=(0, 0, head_y + diameter * 0.25)
    )
    head = bpy.context.active_object
    head.name = 'king_head'
    pieces.append(head)
    
    # Cross (simplified as intersecting boxes)
    cross_size = diameter * 0.25
    bpy.ops.mesh.primitive_cube_add(
        size=cross_size,
        location=(0, 0, head_y + diameter * 0.6)
    )
    cross_v = bpy.context.active_object
    cross_v.scale = (0.3, 1, 0.3)
    pieces.append(cross_v)
    
    bpy.ops.mesh.primitive_cube_add(
        size=cross_size,
        location=(0, 0, head_y + diameter * 0.45)
    )
    cross_h = bpy.context.active_object
    cross_h.scale = (1, 0.3, 0.3)
    pieces.append(cross_h)
    
    # Join all pieces
    bpy.ops.object.select_all(action='DESELECT')
    for piece in pieces:
        piece.select_set(True)
    bpy.context.view_layer.objects.active = pieces[0]
    bpy.ops.object.join()
    
    king = bpy.context.active_object
    king.name = f'king_{color_name.lower()}'
    
    # Apply material
    mat = create_material(f'pieces_{color_name.lower()}', color_rgb)
    king.data.materials.append(mat)
    
    return king

def create_queen(color_name, color_rgb):
    """Create a Queen piece."""
    height = PIECE_HEIGHTS['queen']
    diameter = BASE_DIAMETERS['queen']
    
    pieces = []
    
    # Base
    base = create_base('queen', diameter)
    pieces.append(base)
    
    # Body (tapered using multiple cylinders)
    segments = 3
    body_height = height * 0.55
    segment_height = body_height / segments
    
    for i in range(segments):
        radius = diameter * 0.4 * (1 - i * 0.1)
        z_pos = 0.3 * SCALE_CM + i * segment_height + segment_height / 2
        bpy.ops.mesh.primitive_cylinder_add(
            radius=radius,
            depth=segment_height,
            location=(0, 0, z_pos)
        )
        seg = bpy.context.active_object
        seg.name = f'queen_seg_{i}'
        pieces.append(seg)
    
    # Collar
    collar_height = height * 0.08
    bpy.ops.mesh.primitive_cylinder_add(
        radius=diameter * 0.45,
        depth=collar_height,
        location=(0, 0, 0.3 * SCALE_CM + body_height + collar_height / 2)
    )
    collar = bpy.context.active_object
    collar.name = 'queen_collar'
    pieces.append(collar)
    
    # Head (sphere with points - simplified as cylinder + sphere)
    head_y = 0.3 * SCALE_CM + body_height + collar_height
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=diameter * 0.35,
        location=(0, 0, head_y + diameter * 0.3)
    )
    head = bpy.context.active_object
    head.name = 'queen_head'
    pieces.append(head)
    
    # Crown points (simplified as small cones around top)
    for angle in [0, 90, 180, 270]:
        rad = math.radians(angle)
        x = math.cos(rad) * diameter * 0.25
        y = math.sin(rad) * diameter * 0.25
        z = head_y + diameter * 0.5
        bpy.ops.mesh.primitive_cone_add(
            radius1=diameter * 0.08,
            radius2=0,
            depth=diameter * 0.2,
            location=(x, y, z)
        )
        point = bpy.context.active_object
        point.name = f'queen_point_{angle}'
        pieces.append(point)
    
    # Join
    bpy.ops.object.select_all(action='DESELECT')
    for piece in pieces:
        piece.select_set(True)
    bpy.context.view_layer.objects.active = pieces[0]
    bpy.ops.object.join()
    
    queen = bpy.context.active_object
    queen.name = f'queen_{color_name.lower()}'
    
    mat = create_material(f'pieces_{color_name.lower()}', color_rgb)
    queen.data.materials.append(mat)
    
    return queen

def create_rook(color_name, color_rgb):
    """Create a Rook piece."""
    height = PIECE_HEIGHTS['rook']
    diameter = BASE_DIAMETERS['rook']
    
    pieces = []
    
    # Base
    base = create_base('rook', diameter)
    pieces.append(base)
    
    # Body (straight cylinder)
    body_height = height * 0.65
    bpy.ops.mesh.primitive_cylinder_add(
        radius=diameter * 0.35,
        depth=body_height,
        location=(0, 0, 0.3 * SCALE_CM + body_height / 2)
    )
    body = bpy.context.active_object
    body.name = 'rook_body'
    pieces.append(body)
    
    # Collar
    collar_height = height * 0.1
    bpy.ops.mesh.primitive_cylinder_add(
        radius=diameter * 0.42,
        depth=collar_height,
        location=(0, 0, 0.3 * SCALE_CM + body_height + collar_height / 2)
    )
    collar = bpy.context.active_object
    collar.name = 'rook_collar'
    pieces.append(collar)
    
    # Top (crenellations)
    top_y = 0.3 * SCALE_CM + body_height + collar_height
    top_height = height * 0.15
    
    # Main top cylinder
    bpy.ops.mesh.primitive_cylinder_add(
        radius=diameter * 0.35,
        depth=top_height,
        location=(0, 0, top_y + top_height / 2)
    )
    top = bpy.context.active_object
    top.name = 'rook_top'
    pieces.append(top)
    
    # Battlements (cutouts would require boolean, using add-on blocks instead)
    for i in range(4):
        angle = i * 90
        rad = math.radians(angle)
        x = math.cos(rad) * diameter * 0.3
        y = math.sin(rad) * diameter * 0.3
        z = top_y + top_height
        bpy.ops.mesh.primitive_cube_add(
            size=diameter * 0.15,
            location=(x, y, z + diameter * 0.075)
        )
        battlement = bpy.context.active_object
        battlement.name = f'rook_battlement_{i}'
        battlement.rotation_euler = (0, 0, rad)
        pieces.append(battlement)
    
    # Join
    bpy.ops.object.select_all(action='DESELECT')
    for piece in pieces:
        piece.select_set(True)
    bpy.context.view_layer.objects.active = pieces[0]
    bpy.ops.object.join()
    
    rook = bpy.context.active_object
    rook.name = f'rook_{color_name.lower()}'
    
    mat = create_material(f'pieces_{color_name.lower()}', color_rgb)
    rook.data.materials.append(mat)
    
    return rook

def create_bishop(color_name, color_rgb):
    """Create a Bishop piece."""
    height = PIECE_HEIGHTS['bishop']
    diameter = BASE_DIAMETERS['bishop']
    
    pieces = []
    
    # Base
    base = create_base('bishop', diameter)
    pieces.append(base)
    
    # Body (slightly tapered)
    body_segments = 2
    body_height = height * 0.5
    segment_height = body_height / body_segments
    
    for i in range(body_segments):
        radius = diameter * 0.35 * (1 - i * 0.1)
        z = 0.3 * SCALE_CM + i * segment_height + segment_height / 2
        bpy.ops.mesh.primitive_cylinder_add(
            radius=radius,
            depth=segment_height,
            location=(0, 0, z)
        )
        seg = bpy.context.active_object
        seg.name = f'bishop_seg_{i}'
        pieces.append(seg)
    
    # Collar
    collar_height = height * 0.08
    bpy.ops.mesh.primitive_cylinder_add(
        radius=diameter * 0.4,
        depth=collar_height,
        location=(0, 0, 0.3 * SCALE_CM + body_height + collar_height / 2)
    )
    collar = bpy.context.active_object
    collar.name = 'bishop_collar'
    pieces.append(collar)
    
    # Head (oval/oblate sphere)
    head_y = 0.3 * SCALE_CM + body_height + collar_height
    head_height = height * 0.25
    
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=diameter * 0.35,
        location=(0, 0, head_y + head_height * 0.35)
    )
    head = bpy.context.active_object
    head.scale = (1, 1, 1.3)
    head.name = 'bishop_head'
    pieces.append(head)
    
    # Mitre slit (simplified as thin box)
    bpy.ops.mesh.primitive_cube_add(
        size=diameter * 0.4,
        location=(0, 0, head_y + head_height * 0.5)
    )
    slit = bpy.context.active_object
    slit.scale = (0.05, 1, 0.8)
    slit.name = 'bishop_slit'
    pieces.append(slit)
    
    # Join
    bpy.ops.object.select_all(action='DESELECT')
    for piece in pieces:
        piece.select_set(True)
    bpy.context.view_layer.objects.active = pieces[0]
    bpy.ops.object.join()
    
    bishop = bpy.context.active_object
    bishop.name = f'bishop_{color_name.lower()}'
    
    mat = create_material(f'pieces_{color_name.lower()}', color_rgb)
    bishop.data.materials.append(mat)
    
    return bishop

def create_knight(color_name, color_rgb):
    """Create a Knight piece (simplified horse head)."""
    height = PIECE_HEIGHTS['knight']
    diameter = BASE_DIAMETERS['knight']
    
    pieces = []
    
    # Base
    base = create_base('knight', diameter)
    pieces.append(base)
    
    # Body (straight cylinder)
    body_height = height * 0.45
    bpy.ops.mesh.primitive_cylinder_add(
        radius=diameter * 0.35,
        depth=body_height,
        location=(0, 0, 0.3 * SCALE_CM + body_height / 2)
    )
    body = bpy.context.active_object
    body.name = 'knight_body'
    pieces.append(body)
    
    # Collar
    collar_height = height * 0.08
    bpy.ops.mesh.primitive_cylinder_add(
        radius=diameter * 0.42,
        depth=collar_height,
        location=(0, 0, 0.3 * SCALE_CM + body_height + collar_height / 2)
    )
    collar = bpy.context.active_object
    collar.name = 'knight_collar'
    pieces.append(collar)
    
    # Head (simplified as wedge)
    head_y = 0.3 * SCALE_CM + body_height + collar_height
    head_height = height * 0.35
    
    bpy.ops.mesh.primitive_cone_add(
        radius1=diameter * 0.35,
        radius2=diameter * 0.15,
        depth=head_height,
        location=(0, 0, head_y + head_height / 2)
    )
    head = bpy.context.active_object
    head.rotation_euler = (math.radians(90), 0, 0)  # Tilt forward
    head.name = 'knight_head'
    pieces.append(head)
    
    # Mane detail (small box)
    bpy.ops.mesh.primitive_cube_add(
        size=diameter * 0.2,
        location=(0, -diameter * 0.15, head_y + head_height * 0.7)
    )
    mane = bpy.context.active_object
    mane.name = 'knight_mane'
    pieces.append(mane)
    
    # Join
    bpy.ops.object.select_all(action='DESELECT')
    for piece in pieces:
        piece.select_set(True)
    bpy.context.view_layer.objects.active = pieces[0]
    bpy.ops.object.join()
    
    knight = bpy.context.active_object
    knight.name = f'knight_{color_name.lower()}'
    
    mat = create_material(f'pieces_{color_name.lower()}', color_rgb)
    knight.data.materials.append(mat)
    
    return knight

def create_pawn(color_name, color_rgb):
    """Create a Pawn piece."""
    height = PIECE_HEIGHTS['pawn']
    diameter = BASE_DIAMETERS['pawn']
    
    pieces = []
    
    # Base
    base = create_base('pawn', diameter)
    pieces.append(base)
    
    # Body (straight)
    body_height = height * 0.5
    bpy.ops.mesh.primitive_cylinder_add(
        radius=diameter * 0.35,
        depth=body_height,
        location=(0, 0, 0.3 * SCALE_CM + body_height / 2)
    )
    body = bpy.context.active_object
    body.name = 'pawn_body'
    pieces.append(body)
    
    # Collar
    collar_height = height * 0.1
    bpy.ops.mesh.primitive_cylinder_add(
        radius=diameter * 0.42,
        depth=collar_height,
        location=(0, 0, 0.3 * SCALE_CM + body_height + collar_height / 2)
    )
    collar = bpy.context.active_object
    collar.name = 'pawn_collar'
    pieces.append(collar)
    
    # Head (sphere)
    head_y = 0.3 * SCALE_CM + body_height + collar_height
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=diameter * 0.4,
        location=(0, 0, head_y + diameter * 0.25)
    )
    head = bpy.context.active_object
    head.name = 'pawn_head'
    pieces.append(head)
    
    # Join
    bpy.ops.object.select_all(action='DESELECT')
    for piece in pieces:
        piece.select_set(True)
    bpy.context.view_layer.objects.active = pieces[0]
    bpy.ops.object.join()
    
    pawn = bpy.context.active_object
    pawn.name = f'pawn_{color_name.lower()}'
    
    mat = create_material(f'pieces_{color_name.lower()}', color_rgb)
    pawn.data.materials.append(mat)
    
    return pawn

def create_full_set(color_name, color_rgb):
    """Create all 6 piece types for one color."""
    pieces = {}
    pieces['king'] = create_king(color_name, color_rgb)
    pieces['queen'] = create_queen(color_name, color_rgb)
    pieces['rook'] = create_rook(color_name, color_rgb)
    pieces['bishop'] = create_bishop(color_name, color_rgb)
    pieces['knight'] = create_knight(color_name, color_rgb)
    pieces['pawn'] = create_pawn(color_name, color_rgb)
    return pieces

def export_piece(obj, filepath):
    """Export single piece to OBJ."""
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    bpy.ops.export_scene.obj(
        filepath=filepath,
        use_selection=True,
        use_materials=True,
        use_triangles=False
    )

def main():
    """Generate and export full procedural chess set."""
    
    print("=== Procedural Chess Set Generator ===")
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(f"{OUTPUT_DIR}/white", exist_ok=True)
    os.makedirs(f"{OUTPUT_DIR}/black", exist_ok=True)
    
    # Colors
    WHITE_COLOR = (0.95, 0.95, 0.9)  # Off-white
    BLACK_COLOR = (0.15, 0.15, 0.15)  # Dark gray/black
    
    # Clear scene
    clear_scene()
    
    print("\nGenerating WHITE pieces...")
    white_pieces = create_full_set('White', WHITE_COLOR)
    
    print("Generating BLACK pieces...")
    black_pieces = create_full_set('Black', BLACK_COLOR)
    
    # Export individual pieces
    print("\nExporting to OBJ...")
    
    for name, piece in white_pieces.items():
        filepath = f"{OUTPUT_DIR}/white/{name}.obj"
        export_piece(piece, filepath)
        print(f"  Exported: {filepath}")
    
    for name, piece in black_pieces.items():
        filepath = f"{OUTPUT_DIR}/black/{name}.obj"
        export_piece(piece, filepath)
        print(f"  Exported: {filepath}")
    
    # Save full collection as BLEND
    print("\nSaving blend file...")
    blend_path = f"{OUTPUT_DIR}/procedural_chess_set.blend"
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"  Saved: {blend_path}")
    
    # Create preview scene
    print("\nCreating preview arrangement (starting position)...")
    
    # Clear and arrange
    clear_scene()
    
    # Regenerate for arrangement
    white = create_full_set('White', WHITE_COLOR)
    black = create_full_set('Black', BLACK_COLOR)
    
    # Create board (simple plane for preview)
    bpy.ops.mesh.primitive_plane_add(size=5.7 * 0.01, location=(0, 0, 0))
    board = bpy.context.active_object
    board.name = "board_preview"
    
    # Position pieces (simplified - would use proper board coordinates in production)
    spacing = 5.7 * 0.01  # 5.7cm in meters
    
    # Arrange white pieces in back rank
    z_white = spacing
    white['rook'].location = (-3.5 * spacing, z_white, 0)
    white['knight'].location = (-2.5 * spacing, z_white, 0)
    white['bishop'].location = (-1.5 * spacing, z_white, 0)
    white['queen'].location = (-0.5 * spacing, z_white, 0)
    white['king'].location = (0.5 * spacing, z_white, 0)
    white['bishop'].location = (1.5 * spacing, z_white, 0)
    white['knight'].location = (2.5 * spacing, z_white, 0)
    white['rook'].location = (3.5 * spacing, z_white, 0)
    
    print("\n=== Complete ===")
    print(f"All pieces exported to: {OUTPUT_DIR}")
    print("\nFile structure:")
    print(f"  {OUTPUT_DIR}/white/king.obj")
    print(f"  {OUTPUT_DIR}/white/queen.obj")
    print(f"  ...")
    print(f"  {OUTPUT_DIR}/black/pawn.obj")
    print(f"  {OUTPUT_DIR}/procedural_chess_set.blend")
    print("\nThese are SIMPLIFIED procedural pieces.")
    print("For production, download higher-quality scans or models.")

if __name__ == "__main__":
    main()