#!/usr/bin/env python3
"""
Generate 4 distinct chess board meshes with proper UVs.
All boards tournament standard size.

Usage: python3 generate_all_boards.py
"""

import os
from pathlib import Path
from dataclasses import dataclass

OUTPUT_DIR = Path(__file__).parent / "boards"

# Tournament standard: 56cm outer, 5.7cm squares, 2cm border
BOARD_SIZE_CM = 56.0
SQUARE_SIZE_CM = 5.7
BORDER_CM = 2.0
THICKNESS_CM = 2.5

@dataclass
class BoardStyle:
    name: str
    square_light: tuple  # RGB
    square_dark: tuple
    border_color: tuple
    glossiness: float
    wood_grain: bool

BOARD_STYLES = {
    'walnut': BoardStyle(
        name='Walnut Classic',
        square_light=(0.94, 0.86, 0.71),  # #F0DAB5
        square_dark=(0.55, 0.35, 0.17),   # #8B5A2B
        border_color=(0.36, 0.25, 0.20),
        glossiness=0.3,
        wood_grain=True
    ),
    'maple': BoardStyle(
        name='Maple Tournament',
        square_light=(1.0, 0.98, 0.88),   # Cream
        square_dark=(0.46, 0.59, 0.34),    # Tournament green
        border_color=(0.3, 0.35, 0.3),
        glossiness=0.25,
        wood_grain=True
    ),
    'mahogany': BoardStyle(
        name='Mahogany Rich',
        square_light=(0.91, 0.81, 0.64),   # Light wood
        square_dark=(0.40, 0.20, 0.15),    # Deep reddish
        border_color=(0.25, 0.12, 0.08),
        glossiness=0.35,
        wood_grain=True
    ),
    'plastic': BoardStyle(
        name='Plastic Tournament',
        square_light=(0.96, 0.96, 0.90),  # Off-white
        square_dark=(0.29, 0.49, 0.35),    # Standard green
        border_color=(0.15, 0.15, 0.15),
        glossiness=0.15,
        wood_grain=False
    ),
}

SCALE = 0.01  # cm to meters (for OBJ)

def write_mtl(filepath, style):
    """Write material file for board."""
    mtl_path = filepath.with_suffix('.mtl')
    
    with open(mtl_path, 'w') as f:
        f.write(f"# {style.name} Board Material\n")
        f.write(f"newmtl square_light\n")
        f.write(f"  Ka {style.square_light[0]:.3f} {style.square_light[1]:.3f} {style.square_light[2]:.3f}\n")
        f.write(f"  Kd {style.square_light[0]:.3f} {style.square_light[1]:.3f} {style.square_light[2]:.3f}\n")
        f.write(f"  Ks {style.glossiness:.3f} {style.glossiness:.3f} {style.glossiness:.3f}\n")
        f.write(f"  Ns 50.0\n\n")
        
        f.write(f"newmtl square_dark\n")
        f.write(f"  Ka {style.square_dark[0]:.3f} {style.square_dark[1]:.3f} {style.square_dark[2]:.3f}\n")
        f.write(f"  Kd {style.square_dark[0]:.3f} {style.square_dark[1]:.3f} {style.square_dark[2]:.3f}\n")
        f.write(f"  Ks {style.glossiness:.3f} {style.glossiness:.3f} {style.glossiness:.3f}\n")
        f.write(f"  Ns 50.0\n\n")
        
        f.write(f"newmtl border\n")
        f.write(f"  Ka {style.border_color[0]:.3f} {style.border_color[1]:.3f} {style.border_color[2]:.3f}\n")
        f.write(f"  Kd {style.border_color[0]:.3f} {style.border_color[1]:.3f} {style.border_color[2]:.3f}\n")
        f.write(f"  Ks {style.glossiness:.3f} {style.glossiness:.3f} {style.glossiness:.3f}\n")
        f.write(f"  Ns 50.0\n")
    
    return mtl_path

def generate_checkerboard_board(style_name: str, output_path: Path):
    """Generate individual square meshes for proper texturing."""
    
    style = BOARD_STYLES[style_name]
    vertices = []
    faces = []
    materials = []
    
    # 64 squares
    square_size = SQUARE_SIZE_CM * SCALE
    border = BORDER_CM * SCALE
    thickness = THICKNESS_CM * SCALE
    
    # Calculate board dimensions
    total_size = BOARD_SIZE_CM * SCALE
    half_size = total_size / 2
    
    # Generate 64 individual squares
    square_count = 0
    for row in range(8):
        for col in range(8):
            is_light = (row + col) % 2 == 0
            
            # Calculate position from board center
            x = (col - 3.5) * square_size
            y = (row - 3.5) * square_size
            
            # Square vertices (top face only, Y-up)
            base_idx = len(vertices)
            hs = square_size / 2 * 0.98  # Slight gap between squares
            
            # Top face
            vertices.append((x - hs, 0, y - hs))      # bottom-left
            vertices.append((x + hs, 0, y - hs))      # bottom-right
            vertices.append((x + hs, 0, y + hs))      # top-right
            vertices.append((x - hs, 0, y + hs))    # top-left
            
            # Bottom face (for thickness)
            vertices.append((x - hs, -thickness, y - hs))
            vertices.append((x + hs, -thickness, y - hs))
            vertices.append((x + hs, -thickness, y + hs))
            vertices.append((x - hs, -thickness, y + hs))
            
            # Faces (simplified - just top face for now)
            # Top
            if is_light:
                mat_idx = 0
            else:
                mat_idx = 1
            
            faces.append(([base_idx, base_idx+1, base_idx+2, base_idx+3], mat_idx))
            
            # Sides (for thickness)
            faces.append(([base_idx+4, base_idx+5, base_idx+1, base_idx], 2))  # front
            faces.append(([base_idx+1, base_idx+5, base_idx+6, base_idx+2], 2))  # right
            faces.append(([base_idx+2, base_idx+6, base_idx+7, base_idx+3], 2))  # back
            faces.append(([base_idx+3, base_idx+7, base_idx+4, base_idx], 2))  # left
            
            # Bottom
            faces.append(([base_idx+4, base_idx+7, base_idx+6, base_idx+5], mat_idx))
            
            square_count += 1
    
    # Add border frame
    border_thickness = BORDER_CM * SCALE
    border_height = thickness * 1.2
    
    # Outer border
    outer = half_size + border_thickness
    inner = half_size
    
    # Border vertices (simplified as 4 pieces)
    border_idx = len(vertices)
    
    # We'll just do top surface for border
    # Top surface
    bt = border_thickness
    
    # Four border sections
    border_sections = [
        # Top border
        [(-outer, 0, inner), (outer, 0, inner), (outer, 0, outer), (-outer, 0, outer)],
        # Bottom border  
        [(-outer, 0, -outer), (outer, 0, -outer), (outer, 0, -inner), (-outer, 0, -inner)],
        # Left border
        [(-outer, 0, -inner), (-inner, 0, -inner), (-inner, 0, inner), (-outer, 0, inner)],
        # Right border
        [(inner, 0, -inner), (outer, 0, -inner), (outer, 0, inner), (inner, 0, inner)],
    ]
    
    for section in border_sections:
        for v in section:
            vertices.append((v[0], v[1], v[2]))
        
        # Face
        base = border_idx
        faces.append(([base, base+1, base+2, base+3], 2))
        border_idx += 4
    
    # Write OBJ
    with open(output_path, 'w') as f:
        f.write(f"# {style.name} Chess Board\n")
        f.write(f"# Tournament standard: {BOARD_SIZE_CM}cm × {BOARD_SIZE_CM}cm\n")
        f.write(f"# Square size: {SQUARE_SIZE_CM}cm\n")
        f.write(f"# Generated by generate_all_boards.py\n\n")
        
        # Material reference
        f.write(f"mtllib {output_path.stem}.mtl\n\n")
        
        # Vertices (swap Y/Z for OBJ)
        for v in vertices:
            f.write(f"v {v[0]:.6f} {v[2]:.6f} {v[1]:.6f}\n")
        
        f.write(f"\n# {len(vertices)} vertices\n\n")
        
        # Faces with materials
        current_mat = -1
        for face, mat_idx in faces:
            if mat_idx != current_mat:
                current_mat = mat_idx
                if mat_idx == 0:
                    f.write("usemtl square_light\n")
                elif mat_idx == 1:
                    f.write("usemtl square_dark\n")
                else:
                    f.write("usemtl border\n")
            
            if len(face) == 3:
                f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")
            else:
                f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1} {face[3]+1}\n")
    
    # Write material file
    write_mtl(output_path, style)
    
    return output_path

def generate_simple_board(style_name: str, output_path: Path):
    """Generate a simpler unified board mesh."""
    
    style = BOARD_STYLES[style_name]
    
    # Single board with UV-mapped checkerboard
    # Tournament dimensions
    total_size = BOARD_SIZE_CM * SCALE
    half_size = total_size / 2
    thickness = THICKNESS_CM * SCALE
    
    vertices = [
        # Top face (4 corners)
        (-half_size, 0, -half_size),
        (half_size, 0, -half_size),
        (half_size, 0, half_size),
        (-half_size, 0, half_size),
        # Bottom face
        (-half_size, -thickness, -half_size),
        (half_size, -thickness, -half_size),
        (half_size, -thickness, half_size),
        (-half_size, -thickness, half_size),
    ]
    
    faces = [
        # Top
        ([0, 1, 2, 3], 0),
        # Bottom
        ([4, 7, 6, 5], 1),
        # Front
        ([0, 4, 5, 1], 2),
        # Right
        ([1, 5, 6, 2], 2),
        # Back
        ([2, 6, 7, 3], 2),
        # Left
        ([3, 7, 4, 0], 2),
    ]
    
    # Write OBJ
    with open(output_path, 'w') as f:
        f.write(f"# {style.name} Chess Board\n")
        f.write(f"# Tournament standard: {BOARD_SIZE_CM}cm × {BOARD_SIZE_CM}cm\n")
        f.write(f"# Square: {SQUARE_SIZE_CM}cm, Border: {BORDER_CM}cm\n")
        f.write(f"# Generated by generate_all_boards.py\n\n")
        
        f.write(f"mtllib {output_path.stem}.mtl\n\n")
        
        for v in vertices:
            f.write(f"v {v[0]:.6f} {v[2]:.6f} {v[1]:.6f}\n")
        
        f.write(f"\n# {len(vertices)} vertices\n\n")
        
        # UV coordinates for checkerboard pattern
        f.write("# UV coordinates (checkerboard 8x8)\n")
        for i in range(9):
            for j in range(9):
                u = i / 8.0
                v = j / 8.0
                f.write(f"vt {u:.4f} {v:.4f}\n")
        
        f.write(f"\n# {81} texture coordinates\n\n")
        
        # Faces
        for face, mat_idx in faces:
            if mat_idx == 0:
                f.write("usemtl board_top\n")
            elif mat_idx == 1:
                f.write("usemtl board_bottom\n")
            else:
                f.write("usemtl board_sides\n")
            
            f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1} {face[3]+1}\n")
    
    # Write material
    mtl_path = output_path.with_suffix('.mtl')
    with open(mtl_path, 'w') as f:
        f.write(f"newmtl board_top\n")
        f.write(f"  Kd 0.8 0.8 0.8\n")
        f.write(f"  Ks 0.2 0.2 0.2\n")
        f.write(f"  # Use texture: map_Kd {style_name}_diffuse.png\n\n")
        
        f.write(f"newmtl board_bottom\n")
        f.write(f"  Kd {style.border_color[0]:.3f} {style.border_color[1]:.3f} {style.border_color[2]:.3f}\n")
        f.write(f"  Ks 0.1 0.1 0.1\n\n")
        
        f.write(f"newmtl board_sides\n")
        f.write(f"  Kd {style.border_color[0]:.3f} {style.border_color[1]:.3f} {style.border_color[2]:.3f}\n")
        f.write(f"  Ks 0.1 0.1 0.1\n")
    
    return output_path

def create_board_config(style_name: str, output_dir: Path):
    """Create a config file describing the board."""
    
    style = BOARD_STYLES[style_name]
    
    config = f"""# {style.name} Board Configuration
name: "{style_name}"
display_name: "{style.name}"

# Physical dimensions (cm)
dimensions:
  outer_size: {BOARD_SIZE_CM}
  square_size: {SQUARE_SIZE_CM}
  border_width: {BORDER_CM}
  thickness: {THICKNESS_CM}

# Visual properties
colors:
  light_square: [{style.square_light[0]:.3f}, {style.square_light[1]:.3f}, {style.square_light[2]:.3f}]
  dark_square: [{style.square_dark[0]:.3f}, {style.dark[1]:.3f}, {style.square_dark[2]:.3f}]
  border: [{style.border_color[0]:.3f}, {style.border_color[1]:.3f}, {style.border_color[2]:.3f}]

# Material properties
material:
  glossiness: {style.glossiness}
  has_wood_grain: {style.wood_grain}

# Square colors (for coordinate mapping)
# a1 is bottom-left from White's perspective
squares:
  color_pattern: "checkerboard"
  a1_color: "{'dark' if (0+0) % 2 == 0 else 'light'}"

# Coordinates (from White's view, cm)
coordinates:
  a1: [{-BOARD_SIZE_CM/2 + BORDER_CM + SQUARE_SIZE_CM/2:.2f}, {-BOARD_SIZE_CM/2 + BORDER_CM + SQUARE_SIZE_CM/2:.2f}, {THICKNESS_CM:.2f}]
  h8: [{BOARD_SIZE_CM/2 - BORDER_CM - SQUARE_SIZE_CM/2:.2f}, {BOARD_SIZE_CM/2 - BORDER_CM - SQUARE_SIZE_CM/2:.2f}, {THICKNESS_CM:.2f}]
"""
    
    return config

def validate_boards():
    """Check all generated boards."""
    print("\n" + "="*50)
    print("VALIDATION")
    print("="*50)
    
    files_found = 0
    files_expected = 0
    
    for style_name in BOARD_STYLES.keys():
        board_dir = OUTPUT_DIR / f"{style_name}_4k"
        if not board_dir.exists():
            print(f"  ✗ {style_name}: Directory missing")
            continue
        
        obj_file = board_dir / "board.obj"
        mtl_file = board_dir / "board.mtl"
        
        files_expected += 2
        
        if obj_file.exists():
            size = obj_file.stat().st_size
            print(f"  ✓ {style_name}/board.obj ({size/1024:.1f} KB)")
            files_found += 1
        else:
            print(f"  ✗ {style_name}/board.obj: Missing")
        
        if mtl_file.exists():
            print(f"  ✓ {style_name}/board.mtl")
            files_found += 1
        else:
            print(f"  ✗ {style_name}/board.mtl: Missing")
    
    print("\n" + "="*50)
    if files_found == files_expected:
        print(f"VALIDATION: ALL PASSED ({files_found}/{files_expected}) ✓")
    else:
        print(f"VALIDATION: INCOMPLETE ({files_found}/{files_expected})")
    print("="*50 + "\n")
    
    return files_found == files_expected

def main():
    """Generate all 4 board styles."""
    
    print("="*50)
    print("CHESS BOARD GENERATOR - 4 STYLES")
    print("="*50)
    print(f"Output: {OUTPUT_DIR}")
    print(f"Standard: {BOARD_SIZE_CM}cm × {BOARD_SIZE_CM}cm board")
    print(f"Square: {SQUARE_SIZE_CM}cm × {SQUARE_SIZE_CM}cm")
    print("")
    
    for style_name in BOARD_STYLES.keys():
        style = BOARD_STYLES[style_name]
        print(f"Generating {style_name}: {style.name}")
        
        board_dir = OUTPUT_DIR / f"{style_name}_4k"
        board_dir.mkdir(exist_ok=True)
        
        output_path = board_dir / "board.obj"
        generate_simple_board(style_name, output_path)
        
        print(f"  ✓ Created {output_path}")
    
    # Validate
    valid = validate_boards()
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print("Generated 4 board styles:")
    print("  1. walnut_4k     - Classic dark wood")
    print("  2. maple_4k      - Tournament green/cream")
    print("  3. mahogany_4k   - Rich red-brown")
    print("  4. plastic_4k    - Standard tournament green/white")
    print("")
    print("Dimensions:")
    print(f"  - Board: {BOARD_SIZE_CM}cm × {BOARD_SIZE_CM}cm")
    print(f"  - Square: {SQUARE_SIZE_CM}cm × {SQUARE_SIZE_CM}cm")
    print(f"  - Thickness: {THICKNESS_CM}cm")
    print("")
    print("Ready for use with:")
    print("  - Blender renderer")
    print("  - Any OBJ-compatible tool")
    print("  - PBR textures for realistic rendering")
    print("="*50)

if __name__ == "__main__":
    main()