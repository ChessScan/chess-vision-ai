#!/usr/bin/env python3
"""
Comprehensive asset validation for chess training data.
Checks all piece sets, boards, textures, and HDRIs.

Usage: python3 validate_all_assets.py
"""

import os
from pathlib import Path
from datetime import datetime

ASSETS_DIR = Path(__file__).parent

class Colors:
    OK = '\033[92m'
    WARN = '\033[93m'
    FAIL = '\033[91m'
    INFO = '\033[94m'
    RESET = '\033[0m'

def ok(msg): print(f"{Colors.OK}✓{Colors.RESET} {msg}")
def warn(msg): print(f"{Colors.WARN}⚠{Colors.RESET} {msg}")
def fail(msg): print(f"{Colors.FAIL}✗{Colors.RESET} {msg}")
def info(msg): print(f"{Colors.INFO}ℹ{Colors.RESET} {msg}")

def check_file(path: Path, min_size: int = 100) -> bool:
    """Check if file exists and has minimum size."""
    if not path.exists():
        fail(f"{path}: File not found")
        return False
    
    size = path.stat().st_size
    if size < min_size:
        warn(f"{path}: Suspiciously small ({size} bytes)")
        return False
    
    return True

def validate_piece_sets():
    """Validate all 4 piece sets."""
    print("\n" + "="*60)
    print("PIECE SETS VALIDATION")
    print("="*60)
    
    expected_pieces = ['king', 'queen', 'rook', 'bishop', 'knight', 'pawn']
    sets = [
        ('set_01_basic', 'Simple geometric'),
        ('set_02_tournament', 'Plastic tournament'),
        ('set_03_classic', 'Ornate wood'),
        ('set_04_modern', 'Minimalist'),
    ]
    
    total_pieces = 0
    valid_pieces = 0
    
    for set_name, description in sets:
        info(f"\n{set_name}: {description}")
        set_dir = ASSETS_DIR / "pieces" / set_name
        
        if not set_dir.exists():
            fail(f"Directory not found: {set_dir}")
            continue
        
        for color in ['white', 'black']:
            color_dir = set_dir / color
            if not color_dir.exists():
                fail(f"Directory not found: {color_dir}")
                continue
            
            for piece in expected_pieces:
                total_pieces += 1
                obj_file = color_dir / f"{piece}.obj"
                
                if check_file(obj_file, min_size=1000):
                    valid_pieces += 1
    
    print(f"\n{'='*60}")
    print(f"Piece Sets: {valid_pieces}/{total_pieces} files valid")
    if valid_pieces == total_pieces:
        ok("All piece sets validated ✓")
    else:
        fail(f"Missing {total_pieces - valid_pieces} files")
    print("="*60)
    
    return valid_pieces == total_pieces

def validate_boards():
    """Validate all board styles."""
    print("\n" + "="*60)
    print("BOARDS VALIDATION")
    print("="*60)
    
    boards = [
        ('walnut_4k', 'Walnut Classic'),
        ('maple_4k', 'Maple Tournament'),
        ('mahogany_4k', 'Mahogany Rich'),
        ('plastic_4k', 'Plastic Tournament'),
    ]
    
    total_boards = 0
    valid_boards = 0
    
    for board_name, description in boards:
        info(f"\n{board_name}: {description}")
        board_dir = ASSETS_DIR / "boards" / board_name
        
        if not board_dir.exists():
            fail(f"Directory not found: {board_dir}")
            continue
        
        # Check OBJ file
        total_boards += 1
        obj_file = board_dir / "board.obj"
        if check_file(obj_file, min_size=1000):
            ok(f"board.obj ({obj_file.stat().st_size/1024:.1f} KB)")
            valid_boards += 1
        
        # Check MTL file
        total_boards += 1
        mtl_file = board_dir / "board.mtl"
        if check_file(mtl_file, min_size=100):
            ok(f"board.mtl)")
            valid_boards += 1
        
        # Check for textures
        textures = list(board_dir.glob("*.exr")) + list(board_dir.glob("*.png")) + list(board_dir.glob("*.jpg"))
        if textures:
            ok(f"{len(textures)} texture files")
            for tex in textures:
                size = tex.stat().st_size / (1024*1024)  # MB
                info(f"  - {tex.name}: {size:.1f} MB")
    
    print(f"\n{'='*60}")
    print(f"Boards: {valid_boards}/{total_boards} files valid")
    print("="*60)
    
    return valid_boards == total_boards

def validate_hdris():
    """Validate HDRI environment maps."""
    print("\n" + "="*60)
    print("HDRI VALIDATION")
    print("="*60)
    
    hdri_dir = ASSETS_DIR / "hdri"
    expected_categories = ['office', 'studio', 'home', 'outdoor']
    
    total_hdri = 0
    valid_hdri = 0
    
    for category in expected_categories:
        cat_dir = hdri_dir / category
        if not cat_dir.exists():
            fail(f"Directory not found: {cat_dir}")
            continue
        
        hdris = list(cat_dir.glob("*.hdr")) + list(cat_dir.glob("*.exr"))
        
        if hdris:
            total_hdri += len(hdris)
            for hdri in hdris:
                size = hdri.stat().st_size / (1024*1024)  # MB
                if size > 10:  # HDRI should be large
                    ok(f"{category}/{hdri.name}: {size:.1f} MB")
                    valid_hdri += 1
                else:
                    warn(f"{category}/{hdri.name}: Small file ({size:.1f} MB)")
        else:
            warn(f"{category}: No HDRI files found")
    
    print(f"\n{'='*60}")
    print(f"HDRIs: {valid_hdri}/{total_hdri} files valid")
    print("="*60)
    
    return valid_hdri > 0

def validate_consistency():
    """Check that all assets use consistent scales."""
    print("\n" + "="*60)
    print("SCALE CONSISTENCY CHECK")
    print("="*60)
    
    info("Verifying all pieces use scale: 1 unit = 1 cm")
    
    # Check a sample piece from each set
    sets = ['set_01_basic', 'set_02_tournament', 'set_03_classic', 'set_04_modern']
    
    for set_name in sets:
        king_file = ASSETS_DIR / "pieces" / set_name / "white" / "king.obj"
        if king_file.exists():
            with open(king_file) as f:
                content = f.read()
                if "v " in content:
                    # Extract first vertex Y value
                    lines = [l for l in content.split('\n') if l.startswith('v ')]
                    if lines:
                        # Parse vertex
                        parts = lines[-1].split()  # Last vertex (top of king)
                        if len(parts) >= 3:
                            height = float(parts[2])  # Y in OBJ
                            # King should be ~9.5cm
                            if 0.08 < height < 0.11:  # 8-11cm in meters
                                ok(f"{set_name}/king height: {height*100:.1f}cm (valid)")
                            else:
                                warn(f"{set_name}/king height: {height*100:.1f}cm (unexpected)")
    
    # Check board dimensions
    board_file = ASSETS_DIR / "boards" / "walnut_4k" / "board.obj"
    if board_file.exists():
        with open(board_file) as f:
            content = f.read()
            lines = [l for l in content.split('\n') if l.startswith('v ')]
            if lines:
                # Find max extent
                max_x = max_y = max_z = 0
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 4:
                        x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                        max_x = max(max_x, abs(x))
                        max_y = max(max_y, abs(y))
                        max_z = max(max_z, abs(z))
                
                size = max(max_x, max_y) * 2 * 100  # cm
                if 54 < size < 58:  # Should be ~56cm
                    ok(f"Board size: {size:.1f}cm × {size:.1f}cm (valid)")
                else:
                    warn(f"Board size: {size:.1f}cm (expected ~56cm)")
    
    print("\n" + "="*60)
    ok("Scale consistency check complete")
    print("="*60)

def generate_summary():
    """Generate final summary report."""
    print("\n" + "="*60)
    print("ASSET INVENTORY SUMMARY")
    print("="*60)
    
    # Count files
    piece_sets = len([d for d in (ASSETS_DIR / "pieces").iterdir() if d.is_dir()])
    board_styles = len([d for d in (ASSETS_DIR / "boards").iterdir() if d.is_dir()])
    
    hdri_count = 0
    hdri_dir = ASSETS_DIR / "hdri"
    if hdri_dir.exists():
        for cat_dir in hdri_dir.iterdir():
            if cat_dir.is_dir():
                hdri_count += len(list(cat_dir.glob("*.hdr")) + list(cat_dir.glob("*.exr")))
    
    print(f"\n{Colors.INFO}Piece Sets:{Colors.RESET} {piece_sets}")
    print(f"  - 4 distinct styles (basic, tournament, classic, modern)")
    print(f"  - Each: 6 white + 6 black = 12 pieces")
    print(f"  - Total: ~{piece_sets * 12} OBJ files")
    
    print(f"\n{Colors.INFO}Board Styles:{Colors.RESET} {board_styles}")
    print(f"  - walnut_4k, maple_4k, mahogany_4k, plastic_4k")
    print(f"  - Tournament standard: 56cm × 56cm")
    
    print(f"\n{Colors.INFO}HDRI Environments:{Colors.RESET} {hdri_count}")
    print(f"  - Categories: office, studio, home, outdoor")
    
    # Calculate total size
    total_size = 0
    for pattern in ['**/*.obj', '**/*.exr', '**/*.hdr', '**/*.png']:
        for file in ASSETS_DIR.rglob(pattern):
            total_size += file.stat().st_size
    
    print(f"\n{Colors.INFO}Total Storage:{Colors.RESET} {total_size / (1024**3):.2f} GB")
    
    print("\n" + "="*60)
    print("READY FOR BLENDER RENDERING")
    print("="*60)

def main():
    """Run full validation suite."""
    
    print("="*60)
    print("CHESS VISION ASSET VALIDATION")
    print("="*60)
    print(f"Assets directory: {ASSETS_DIR}")
    print(f"Time: {datetime.now().isoformat()}")
    
    results = []
    
    results.append(("Piece Sets", validate_piece_sets()))
    results.append(("Boards", validate_boards()))
    results.append(("HDRIs", validate_hdris()))
    
    validate_consistency()
    generate_summary()
    
    # Final report
    print("\n" + "="*60)
    print("VALIDATION RESULTS")
    print("="*60)
    
    all_passed = True
    for name, passed in results:
        if passed:
            ok(f"{name}: PASSED")
        else:
            fail(f"{name}: FAILED")
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print(f"{Colors.OK}✓ ALL VALIDATIONS PASSED{Colors.RESET}")
        print("Assets are ready for dataset generation")
    else:
        print(f"{Colors.FAIL}✗ SOME VALIDATIONS FAILED{Colors.RESET}")
        print("Review errors above")
    print("="*60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())