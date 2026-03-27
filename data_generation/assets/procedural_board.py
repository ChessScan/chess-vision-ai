#!/usr/bin/env python3
"""
Procedural Chess Board Generator (Blender)
Creates textured chess board with PBR materials.

Usage:
    blender --background --python procedural_board.py

Output:
    - Tournament standard 8x8 board
    - UV mapped with texture coordinates
    - PBR material setup
"""

import bpy
import os
from mathutils import Vector

OUTPUT_DIR = "/home/node/.openclaw/workspace/data_generation/assets/procedural"

def create_board(style="walnut"):
    """Create a chess board mesh with proper UVs."""
    
    # Board dimensions (tournament standard)
    SQUARE_SIZE = 5.7 * 0.01  # 5.7cm in meters
    BOARD_SIZE = SQUARE_SIZE * 8
    BORDER = 2.0 * 0.01  # 2cm border
    THICKNESS = 2.5 * 0.01  # 2.5cm thick
    
    total_size = BOARD_SIZE + 2 * BORDER
    
    # Create main board
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, 0, THICKNESS / 2)
    )
    board = bpy.context.active_object
    board.name = f"board_{style}"
    board.scale = (total_size / 2, total_size / 2, THICKNESS / 2)
    
    # Create UV map
    bpy.ops.mesh.uv_texture_add()
    
    # Switch to edit mode to set up UVs properly
    bpy.context.view_layer.objects.active = board
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Unwrap (this is simplified - proper board needs grid UVs)
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Create material based on style
    mat = create_board_material(style)
    board.data.materials.append(mat)
    
    return board

def create_board_material(style):
    """Create PBR material for chess board."""
    
    mat = bpy.data.materials.new(name=f"board_{style}")
    mat.use_nodes = True
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # Output node
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Principled BSDF
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    
    # Colors based on style
    colors = {
        'walnut': {
            'light': (0.94, 0.86, 0.71),  # #F0DAB5
            'dark': (0.55, 0.35, 0.17),   # #8B5A2B
            'roughness': 0.3
        },
        'maple': {
            'light': (1.0, 1.0, 0.82),    # Cream
            'dark': (0.46, 0.59, 0.34),   # Tournament green
            'roughness': 0.35
        },
        'mahogany': {
            'light': (0.91, 0.81, 0.64),  # Light wood
            'dark': (0.36, 0.25, 0.20),   # Dark mahogany
            'roughness': 0.25
        },
        'plastic': {
            'light': (0.96, 0.96, 0.86),  # Off-white
            'dark': (0.29, 0.49, 0.35),   # Green
            'roughness': 0.15
        }
    }
    
    c = colors.get(style, colors['walnut'])
    
    # For procedural checkerboard, we'd need complex node setup
    # Here we'll create a simplified single-color material
    # In production, use texture maps from downloaded assets
    
    bsdf.inputs['Base Color'].default_value = (*c['light'], 1.0)
    bsdf.inputs['Roughness'].default_value = c['roughness']
    bsdf.inputs['Specular'].default_value = 0.5
    
    # Link nodes
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_simple_checkerboard():
    """Create actual 64 individual squares (allows proper texturing)."""
    
    pieces = []
    SQUARE_SIZE = 5.7 * 0.01
    BORDER = 2.0 * 0.01
    THICKNESS = 2.5 * 0.01
    
    # Create 64 squares
    for row in range(8):
        for col in range(8):
            # Calculate position
            x = (col - 3.5) * SQUARE_SIZE
            y = (row - 3.5) * SQUARE_SIZE
            
            bpy.ops.mesh.primitive_cube_add(
                size=SQUARE_SIZE * 0.98,  # Slight gap between squares
                location=(x, y, THICKNESS / 2)
            )
            square = bpy.context.active_object
            square.scale = (1, 1, THICKNESS / SQUARE_SIZE * 0.5)
            
            # Determine color (checkerboard pattern)
            is_light = (row + col) % 2 == 0
            
            # Create material
            mat = bpy.data.materials.new(name=f"square_{'light' if is_light else 'dark'}")
            mat.use_nodes = True
            mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (
                (0.95, 0.87, 0.68, 1.0) if is_light else (0.55, 0.35, 0.17, 1.0)
            )
            
            square.data.materials.append(mat)
            pieces.append(square)
    
    # Create border frame
    total_size = SQUARE_SIZE * 8 + 2 * BORDER
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, 0, THICKNESS / 4)
    )
    frame = bpy.context.active_object
    frame.scale = (total_size / 2, total_size / 2, THICKNESS / 4)
    frame.name = "board_frame"
    
    # Subtract center (would need boolean in real implementation)
    # For now, just make it solid
    
    # Join all squares
    bpy.ops.object.select_all(action='DESELECT')
    for piece in pieces:
        piece.select_set(True)
    bpy.context.view_layer.objects.active = pieces[0]
    bpy.ops.object.join()
    
    board = bpy.context.active_object
    board.name = "checkerboard"
    
    return board

def main():
    """Generate procedural board(s)."""
    
    print("=== Procedural Chess Board Generator ===")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Clear scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # Generate boards in different styles
    styles = ['walnut', 'maple', 'mahogany', 'plastic']
    
    for style in styles:
        print(f"\nGenerating {style} board...")
        
        # Clear and create
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        
        board = create_simple_checkerboard()
        board.name = f"board_{style}"
        
        # Export
        filepath = f"{OUTPUT_DIR}/board_{style}.obj"
        bpy.ops.export_scene.obj(
            filepath=filepath,
            use_materials=True
        )
        print(f"  Exported: {filepath}")
    
    # Save template scene
    blend_path = f"{OUTPUT_DIR}/boards_template.blend"
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"\nTemplate saved: {blend_path}")
    
    print("\n=== Complete ===")
    print("Note: These are simplified procedural boards.")
    print("For production, use downloaded PBR textures for realistic wood grain.")
    print("\nNext steps:")
    print("  1. Download wood textures from polyhaven.com")
    print("  2. Apply texture maps to these UVs")
    print("  3. Add normal maps for wood grain detail")

if __name__ == "__main__":
    main()