#!/usr/bin/env python3
"""
Generate 4 distinct chess piece sets with consistent tournament scaling.
All pieces normalized to standard tournament proportions.

Usage: python3 generate_all_piece_sets.py
"""

import os
import math
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple

OUTPUT_DIR = Path(__file__).parent / "pieces"

# Tournament standard proportions (in generic units, scaled to cm later)
# Based on Staunton tournament set proportions
@dataclass
class PieceSpec:
    """Standardized piece specifications."""
    base_diameter: float
    base_height: float
    body_height: float
    body_taper: float  # 1.0 = straight, <1.0 = tapered
    head_style: str    # 'crown', 'sphere', 'cylinder', 'cone'
    head_scale: float
    detail_level: int  # 1-5 complexity

# Standard proportions relative to base diameter
STANDARD_SPECS = {
    'king': PieceSpec(1.8, 0.4, 3.2, 0.85, 'crown_cross', 1.0, 5),
    'queen': PieceSpec(1.7, 0.4, 2.8, 0.80, 'crown_points', 1.0, 5),
    'rook': PieceSpec(1.6, 0.4, 2.4, 1.0, 'battlement', 1.0, 3),
    'bishop': PieceSpec(1.5, 0.4, 2.2, 0.75, 'mitre', 1.1, 4),
    'knight': PieceSpec(1.5, 0.4, 2.0, 0.70, 'horse_head', 0.9, 4),
    'pawn': PieceSpec(1.3, 0.35, 1.6, 0.65, 'sphere', 1.0, 2),
}

# Scale factor: 1 unit = 2.5 cm (to reach proper tournament sizes from current specs)
# King height in spec: ~4 units -> 10 cm when scaled by 0.025
SCALE_CM = 0.025

class OBJGenerator:
    """Generate OBJ files with consistent mesh topology."""
    
    def __init__(self, style: str):
        self.style = style
        self.vertices = []
        self.faces = []
        self.current_vertex = 0
    
    def add_cylinder(self, radius: float, height: float, y_offset: float, 
                      segments: int = 32, taper: float = 1.0):
        """Add a tapered cylinder."""
        base_idx = self.current_vertex
        
        # Bottom circle
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = radius * math.cos(angle)
            z = radius * math.sin(angle)
            self.vertices.append((x, z, y_offset))
        
        # Bottom center
        self.vertices.append((0, 0, y_offset))
        bottom_center = self.current_vertex + segments
        
        # Top circle (possibly tapered)
        top_radius = radius * taper
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = top_radius * math.cos(angle)
            z = top_radius * math.sin(angle)
            self.vertices.append((x, z, y_offset + height))
        
        # Top center
        self.vertices.append((0, 0, y_offset + height))
        top_center = self.current_vertex + 2 * segments + 1
        
        # Faces
        # Bottom
        for i in range(segments):
            next_i = (i + 1) % segments
            self.faces.append([base_idx + i, base_idx + next_i, bottom_center])
        
        # Top
        for i in range(segments):
            next_i = (i + 1) % segments
            self.faces.append([base_idx + segments + i, top_center, base_idx + segments + next_i])
        
        # Sides (quads)
        for i in range(segments):
            next_i = (i + 1) % segments
            v0 = base_idx + i
            v1 = base_idx + next_i
            v2 = base_idx + segments + next_i
            v3 = base_idx + segments + i
            self.faces.append([v0, v1, v2, v3])
        
        self.current_vertex = top_center + 1
    
    def add_sphere(self, radius: float, y_center: float, segments: int = 24):
        """Add a sphere."""
        base_idx = self.current_vertex
        
        # Simplified sphere as a few stacked circles
        rings = 8
        for ring in range(rings + 1):
            angle = math.pi * ring / rings
            y = y_center + radius * math.cos(angle)
            r = radius * math.sin(angle)
            
            for i in range(segments):
                theta = 2 * math.pi * i / segments
                x = r * math.cos(theta)
                z = r * math.sin(theta)
                self.vertices.append((x, z, y))
        
        # Faces (simplified)
        for ring in range(rings):
            for i in range(segments):
                next_i = (i + 1) % segments
                v0 = base_idx + ring * segments + i
                v1 = base_idx + ring * segments + next_i
                v2 = base_idx + (ring + 1) * segments + next_i
                v3 = base_idx + (ring + 1) * segments + i
                self.faces.append([v0, v1, v2, v3])
        
        self.current_vertex = len(self.vertices)
    
    def add_box(self, size: Tuple[float, float, float], center: Tuple[float, float, float]):
        """Add a rectangular box."""
        base_idx = self.current_vertex
        sx, sy, sz = size
        cx, cz, cy = center  # OBJ coordinate swap
        
        # 8 corners
        corners = [
            (cx - sx/2, cz - sz/2, cy - sy/2),
            (cx + sx/2, cz - sz/2, cy - sy/2),
            (cx + sx/2, cz + sz/2, cy - sy/2),
            (cx - sx/2, cz + sz/2, cy - sy/2),
            (cx - sx/2, cz - sz/2, cy + sy/2),
            (cx + sx/2, cz - sz/2, cy + sy/2),
            (cx + sx/2, cz + sz/2, cy + sy/2),
            (cx - sx/2, cz + sz/2, cy + sy/2),
        ]
        
        self.vertices.extend(corners)
        
        # 6 faces
        face_indices = [
            [0, 1, 2, 3],  # bottom
            [4, 7, 6, 5],  # top
            [0, 4, 5, 1],  # front
            [2, 6, 7, 3],  # back
            [0, 3, 7, 4],  # left
            [1, 5, 6, 2],  # right
        ]
        
        for face in face_indices:
            self.faces.append([base_idx + i for i in face])
        
        self.current_vertex += 8
    
    def save(self, filepath: str):
        """Save to OBJ file."""
        with open(filepath, 'w') as f:
            f.write(f"# Chess piece: {self.style}\n")
            f.write(f"# Generated by generate_all_piece_sets.py\n")
            f.write(f"# Scale: 1 unit = 1cm\n\n")
            
            for v in self.vertices:
                # OBJ uses Y-up, we store as (x, z, y) for correct orientation
                f.write(f"v {v[0]*SCALE_CM:.6f} {v[2]*SCALE_CM:.6f} {v[1]*SCALE_CM:.6f}\n")
            
            f.write(f"\n# {len(self.vertices)} vertices\n\n")
            
            f.write(f"# {len(self.faces)} faces\n\n")
            for face in self.faces:
                if len(face) == 3:
                    f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")
                else:
                    f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1} {face[3]+1}\n")

def generate_set_1_basic(name: str = "set_01_basic"):
    """Set 1: Simple geometric (existing style)."""
    output = OUTPUT_DIR / name
    output.mkdir(parents=True, exist_ok=True)
    (output / "white").mkdir(exist_ok=True)
    (output / "black").mkdir(exist_ok=True)
    
    for piece, spec in STANDARD_SPECS.items():
        gen = OBJGenerator(name)
        
        # Base
        gen.add_cylinder(spec.base_diameter/2, spec.base_height, 0)
        
        # Body (tapered)
        y = spec.base_height
        gen.add_cylinder(spec.base_diameter/2 * 0.7, spec.body_height, y, taper=spec.body_taper)
        
        # Head
        y += spec.body_height
        if spec.head_style == 'crown_cross':
            gen.add_cylinder(spec.base_diameter/3, spec.base_height * 0.8, y)
            # Cross (simplified as boxes)
            h = spec.base_diameter * 0.4
            gen.add_box((h*0.3, h, h*0.3), (0, 0, y + spec.base_height * 0.8))
            gen.add_box((h, h*0.3, h*0.3), (0, 0, y + spec.base_height * 0.5))
        elif spec.head_style == 'crown_points':
            gen.add_cylinder(spec.base_diameter/2.5, spec.base_height * 0.7, y)
            # Crown points (small cones as boxes)
            pass
        elif spec.head_style == 'battlement':
            gen.add_cylinder(spec.base_diameter/2.2, spec.base_height * 0.6, y)
        elif spec.head_style == 'mitre':
            gen.add_sphere(spec.base_diameter/3, y + spec.base_height/2)
        elif spec.head_style == 'horse_head':
            gen.add_cylinder(spec.base_diameter/3, spec.base_height * 0.8, y, taper=0.6)
        else:  # sphere
            gen.add_sphere(spec.base_diameter/3, y + spec.base_height/3)
        
        # Save both colors
        gen.save(str(output / "white" / f"{piece}.obj"))
        gen.save(str(output / "black" / f"{piece}.obj"))
    
    print(f"  ✓ Generated {name}")
    return output

def generate_set_2_tournament(name: str = "set_02_tournament"):
    """Set 2: Tournament plastic - wider bases, more defined steps."""
    output = OUTPUT_DIR / name
    output.mkdir(parents=True, exist_ok=True)
    (output / "white").mkdir(exist_ok=True)
    (output / "black").mkdir(exist_ok=True)
    
    # Slightly wider, lower profile
    scale = 1.1
    
    for piece, spec in STANDARD_SPECS.items():
        gen = OBJGenerator(name)
        
        # Wider base with step
        gen.add_cylinder(spec.base_diameter/2 * scale, spec.base_height * 0.6, 0)
        gen.add_cylinder(spec.base_diameter/2 * scale * 0.9, spec.base_height * 0.4, spec.base_height * 0.6)
        
        # Body with collar
        y = spec.base_height
        gen.add_cylinder(spec.base_diameter/2 * 0.75 * scale, spec.body_height * 0.8, y, taper=0.9)
        
        # Collar
        y += spec.body_height * 0.8
        gen.add_cylinder(spec.base_diameter/2 * scale * 0.85, spec.base_height * 0.3, y)
        
        # Head
        y += spec.base_height * 0.3
        if spec.head_style == 'crown_cross':
            gen.add_cylinder(spec.base_diameter/2.5 * scale, spec.base_height * 0.6, y)
            # Cross
            h = spec.base_diameter * 0.35 * scale
            gen.add_box((h*0.25, h, h*0.25), (0, 0, y + spec.base_height * 0.6))
            gen.add_box((h, h*0.25, h*0.25), (0, 0, y + spec.base_height * 0.4))
        elif spec.head_style == 'crown_points':
            gen.add_cylinder(spec.base_diameter/2.2 * scale, spec.base_height * 0.5, y)
            gen.add_sphere(spec.base_diameter/2.5 * scale * 0.6, y + spec.base_height * 0.5)
        elif spec.head_style == 'battlement':
            gen.add_cylinder(spec.base_diameter/2 * scale, spec.base_height * 0.5, y)
            # Castle crenellations
            for i in range(4):
                angle = i * math.pi / 2
                x = math.cos(angle) * spec.base_diameter * 0.2 * scale
                z = math.sin(angle) * spec.base_diameter * 0.2 * scale
                h = spec.base_height * 0.3
                gen.add_box((h, h, h), (x, z, y + spec.base_height * 0.5 + h/2))
        elif spec.head_style == 'mitre':
            gen.add_cylinder(spec.base_diameter/2.5 * scale, spec.base_height * 0.5, y, taper=1.3)
            gen.add_sphere(spec.base_diameter/2.8 * scale, y + spec.base_height * 0.4)
        elif spec.head_style == 'horse_head':
            # Horse head = tapered cylinder tilted
            gen.add_cylinder(spec.base_diameter/3 * scale, spec.base_height * 0.7, y, taper=0.5)
        else:  # pawn
            gen.add_sphere(spec.base_diameter/2.5 * scale, y + spec.base_height * 0.25)
        
        gen.save(str(output / "white" / f"{piece}.obj"))
        gen.save(str(output / "black" / f"{piece}.obj"))
    
    print(f"  ✓ Generated {name}")
    return output

def generate_set_3_classic(name: str = "set_03_classic"):
    """Set 3: Classic wood - taller, more ornate."""
    output = OUTPUT_DIR / name
    output.mkdir(parents=True, exist_ok=True)
    (output / "white").mkdir(exist_ok=True)
    (output / "black").mkdir(exist_ok=True)
    
    scale_height = 1.15  # Taller
    
    for piece, spec in STANDARD_SPECS.items():
        gen = OBJGenerator(name)
        
        # Stepped base
        gen.add_cylinder(spec.base_diameter/2 * 0.9, spec.base_height * 0.4, 0)
        gen.add_cylinder(spec.base_diameter/2 * 1.0, spec.base_height * 0.35, spec.base_height * 0.4)
        gen.add_cylinder(spec.base_diameter/2 * 0.85, spec.base_height * 0.25, spec.base_height * 0.75)
        
        # Tall tapered body
        y = spec.base_height
        body_segments = 3
        seg_height = (spec.body_height * scale_height) / body_segments
        
        for i in range(body_segments):
            taper = 1.0 - i * 0.1
            r = spec.base_diameter/2 * 0.65 * (1 - i * 0.08)
            gen.add_cylinder(r, seg_height, y + i * seg_height, taper=taper)
        
        y += spec.body_height * scale_height
        
        # Ornate collar
        gen.add_cylinder(spec.base_diameter/2 * 0.9, spec.base_height * 0.25, y)
        y += spec.base_height * 0.25
        gen.add_cylinder(spec.base_diameter/2 * 0.7, spec.base_height * 0.15, y)
        y += spec.base_height * 0.15
        
        # Elaborate heads
        if spec.head_style == 'crown_cross':
            # Orb with cross
            gen.add_sphere(spec.base_diameter/3, y + spec.base_diameter/4)
            h = spec.base_diameter * 0.5
            gen.add_box((h*0.2, h*0.8, h*0.2), (0, 0, y + spec.base_diameter/2))
            gen.add_box((h*0.8, h*0.2, h*0.2), (0, 0, y + spec.base_diameter/3))
        elif spec.head_style == 'crown_points':
            gen.add_cylinder(spec.base_diameter/3, spec.base_height * 0.4, y, taper=0.7)
            gen.add_sphere(spec.base_diameter/3.5, y + spec.base_height * 0.3)
        elif spec.head_style == 'battlement':
            # Tapered cylinder with top ring
            gen.add_cylinder(spec.base_diameter/2.5, spec.base_height * 0.7, y, taper=0.9)
            gen.add_cylinder(spec.base_diameter/2.2, spec.base_height * 0.2, y + spec.base_height * 0.7)
        elif spec.head_style == 'mitre':
            gen.add_cylinder(spec.base_diameter/3, spec.base_height * 0.4, y, taper=1.4)
            gen.add_sphere(spec.base_diameter/3.5, y + spec.base_height * 0.3)
        elif spec.head_style == 'horse_head':
            gen.add_cylinder(spec.base_diameter/3, spec.body_height * 0.4, y, taper=0.7)
        else:  # pawn with ball
            gen.add_cylinder(spec.base_diameter/3, spec.base_height * 0.3, y, taper=0.8)
            gen.add_sphere(spec.base_diameter/3, y + spec.base_height * 0.25)
        
        gen.save(str(output / "white" / f"{piece}.obj"))
        gen.save(str(output / "black" / f"{piece}.obj"))
    
    print(f"  ✓ Generated {name}")
    return output

def generate_set_4_modern(name: str = "set_04_modern"):
    """Set 4: Modern minimalist - smooth, geometric, low profile."""
    output = OUTPUT_DIR / name
    output.mkdir(parents=True, exist_ok=True)
    (output / "white").mkdir(exist_ok=True)
    (output / "black").mkdir(exist_ok=True)
    
    for piece, spec in STANDARD_SPECS.items():
        gen = OBJGenerator(name)
        
        # Simple flat base
        gen.add_cylinder(spec.base_diameter/2 * 0.95, spec.base_height * 0.5, 0)
        
        # Smooth body, minimal taper
        y = spec.base_height * 0.5
        gen.add_cylinder(spec.base_diameter/2 * 0.7, spec.body_height * 0.9, y, taper=0.95)
        
        # Minimal transition
        y += spec.body_height * 0.9
        
        # Simplified heads
        if spec.head_style == 'crown_cross':
            # Simple post with cross
            gen.add_cylinder(spec.base_diameter/4, spec.base_height * 0.9, y)
            h = spec.base_diameter * 0.4
            gen.add_box((h*0.15, h, h*0.15), (0, 0, y + spec.base_height * 0.9))
            gen.add_box((h, h*0.15, h*0.15), (0, 0, y + spec.base_height * 0.6))
        elif spec.head_style == 'crown_points':
            gen.add_cylinder(spec.base_diameter/3, spec.base_height * 0.5, y, taper=0.8)
            gen.add_cylinder(spec.base_diameter/4, spec.base_height * 0.3, y + spec.base_height * 0.5, taper=1.5)
        elif spec.head_style == 'battlement':
            gen.add_cylinder(spec.base_diameter/2.5, spec.base_height * 0.8, y, taper=1.0)
        elif spec.head_style == 'mitre':
            gen.add_cylinder(spec.base_diameter/3, spec.base_height * 0.5, y, taper=1.2)
            gen.add_sphere(spec.base_diameter/4, y + spec.base_height * 0.4)
        elif spec.head_style == 'horse_head':
            # Smooth cone
            gen.add_cylinder(spec.base_diameter/3.5, spec.body_height * 0.5, y, taper=0.4)
        else:  # pawn - simple ball
            gen.add_sphere(spec.base_diameter/3, y + spec.base_height * 0.2)
        
        gen.save(str(output / "white" / f"{piece}.obj"))
        gen.save(str(output / "black" / f"{piece}.obj"))
    
    print(f"  ✓ Generated {name}")
    return output

def validate_sets():
    """Check all generated sets."""
    print("\n" + "="*50)
    print("VALIDATION")
    print("="*50)
    
    expected_pieces = ['king', 'queen', 'rook', 'bishop', 'knight', 'pawn']
    sets = ['set_01_basic', 'set_02_tournament', 'set_03_classic', 'set_04_modern']
    
    all_valid = True
    
    for set_name in sets:
        set_path = OUTPUT_DIR / set_name
        if not set_path.exists():
            print(f"  ✗ {set_name}: Directory missing")
            all_valid = False
            continue
        
        for color in ['white', 'black']:
            color_path = set_path / color
            if not color_path.exists():
                print(f"  ✗ {set_name}/{color}: Directory missing")
                all_valid = False
                continue
            
            for piece in expected_pieces:
                piece_file = color_path / f"{piece}.obj"
                if not piece_file.exists():
                    print(f"  ✗ {set_name}/{color}/{piece}.obj: Missing")
                    all_valid = False
                elif piece_file.stat().st_size < 1000:
                    print(f"  ⚠ {set_name}/{color}/{piece}.obj: Suspiciously small")
                else:
                    print(f"  ✓ {set_name}/{color}/{piece}.obj")
    
    print("\n" + "="*50)
    if all_valid:
        print("VALIDATION: ALL PASSED ✓")
    else:
        print("VALIDATION: FAILED - check errors above")
    print("="*50 + "\n")
    
    return all_valid

def main():
    """Generate all 4 piece sets."""
    
    print("="*50)
    print("CHESS PIECE GENERATOR - 4 STYLE SETS")
    print("="*50)
    print(f"Output: {OUTPUT_DIR}")
    print("Scale: 1 unit = 1cm (tournament standard)")
    print("")
    
    # Generate all sets
    generate_set_1_basic()
    generate_set_2_tournament()
    generate_set_3_classic()
    generate_set_4_modern()
    
    # Validate
    valid = validate_sets()
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print("Generated 4 complete chess piece sets:")
    print("  1. set_01_basic - Simple geometric (baseline)")
    print("  2. set_02_tournament - Plastic tournament style")
    print("  3. set_03_classic - Ornate wood style")
    print("  4. set_04_modern - Minimalist geometric")
    print("")
    print("Each set contains:")
    print("  - 6 white pieces per set")
    print("  - 6 black pieces per set")
    print("  - 12 OBJ files × 4 sets = 48 total files")
    print("")
    print("All scaled to tournament proportions:")
    print("  - King: ~9.5cm tall (standard)")
    print("  - Pawn: ~5cm tall (standard)")
    print("  - Base diameters proportional")
    print("")
    print("Next: Generate 4 board variations")
    print("      Run generate_all_boards.py")
    print("="*50)

if __name__ == "__main__":
    main()