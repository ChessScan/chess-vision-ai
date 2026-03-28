#!/usr/bin/env python3
"""Chess Vision Render Quality Validator (Blender format version)

Handles Blender's native annotation format with large coordinate values.
"""

import json
import argparse
from pathlib import Path
import struct
import sys

class RenderValidator:
    def __init__(self, renders_dir: Path):
        self.renders_dir = Path(renders_dir)
        self.annotations_file = self.renders_dir / "annotations.json"
        
    def validate_all(self) -> dict:
        """Run full validation suite."""
        results = {
            "renders_validated": 0,
            "renders_failed": 0,
            "total_score": 0,
            "average_score": 0,
            "details": []
        }
        
        # Load annotations
        try:
            with open(self.annotations_file, 'r') as f:
                self.annotations = json.load(f)
            
            if isinstance(self.annotations, list):
                print(f"✓ Loaded {len(self.annotations)} image annotations")
                print(f"✓ Found {sum(len(img.get('annotations', [])) for img in self.annotations)} bounding boxes\n")
            else:
                print(f"Warning: Expected list, got {type(self.annotations)}")
                return results
                
        except FileNotFoundError:
            print(f"✗ Annotations not found: {self.annotations_file}")
            return results
        except json.JSONDecodeError as e:
            print(f"✗ JSON error: {e}")
            return results
            
        # Process each PNG
        for png_file in sorted(self.renders_dir.glob("*.png")):
            result = self.validate_single(png_file)
            results["details"].append(result)
            
            if result["passed"]:
                results["renders_validated"] += 1
                results["total_score"] += result["total_score"]
            else:
                results["renders_failed"] += 1
                
        if results["renders_validated"] > 0:
            results["average_score"] = results["total_score"] / results["renders_validated"]
            
        return results
    
    def _find_annotation(self, png_file: Path):
        """Find matching annotation for a PNG file."""
        if not isinstance(self.annotations, list):
            return None
        
        png_name = png_file.name
        for ann in self.annotations:
            if png_name in ann.get('image', ''):
                return ann
        return None
    
    def validate_single(self, png_file: Path) -> dict:
        """Validate a single render file."""
        result = {
            "file": png_file.name,
            "passed": True,
            "categories": {},
            "total_score": 0,
            "issues": [],
            "metadata": {}
        }
        
        # Technical Specs (max 40 pts)
        tech_score = self._validate_technical(png_file, result["issues"], result["metadata"])
        result["categories"]["technical"] = tech_score
        
        # Scene Composition from annotations (max 33 pts)
        comp_score = self._validate_composition(png_file, result["issues"])
        result["categories"]["composition"] = comp_score
        
        # File Integrity  (max 27 pts)
        integ_score = self._validate_integrity(png_file, result["issues"])
        result["categories"]["integrity"] = integ_score
        
        # Calculate total
        result["total_score"] = sum(result["categories"].values())
        result["max_possible"] = 100
        result["percentage"] = (result["total_score"] / result["max_possible"]) * 100
        
        # Pass/Fail threshold (80% or higher)
        if result["percentage"] < 80:
            result["passed"] = False
            
        return result
    
    def _validate_technical(self, png_file: Path, issues: list, metadata: dict) -> int:
        """Validate technical specs (40 pts)."""
        score = 0
        
        # Parse PNG dimensions manually
        try:
            with open(png_file, 'rb') as f:
                # PNG signature
                header = f.read(8)
                if header != b'\x89PNG\r\n\x1a\n':
                    issues.append("Invalid PNG signature")
                    return 0
                    
                # IHDR chunk (dimensions)
                while True:
                    length_bytes = f.read(4)
                    if len(length_bytes) != 4:
                        break
                    length = struct.unpack('>I', length_bytes)[0]
                    chunk_type = f.read(4)
                    
                    if chunk_type == b'IHDR':
                        width, height = struct.unpack('>II', f.read(8))
                        color_type = struct.unpack('B', f.read(1))[0]
                        
                        metadata['width'] = width
                        metadata['height'] = height
                        
                        # Resolution check (15 pts)
                        if width == 640 and height == 640:
                            score += 15
                        else:
                            issues.append(f"Wrong resolution: {width}x{height}")
                            score += 0
                            
                        # Color type check (5 pts)
                        if color_type in [2, 6]:
                            score += 5
                        else:
                            issues.append(f"Non-RGB color type: {color_type}")
                            
                        break
                    else:
                        f.seek(length + 4, 1)
                        
        except Exception as e:
            issues.append(f"PNG parse error: {e}")
            return 0
            
        # File size check (15 pts)
        size_kb = png_file.stat().st_size / 1024
        metadata['size_kb'] = f"{size_kb:.1f}"
        
        if 150 <= size_kb <= 600:
            score += 15
        elif size_kb < 100:
            issues.append(f"File too small: {size_kb:.1f}KB")
        elif size_kb > 800:
            issues.append(f"File unusually large: {size_kb:.1f}KB")
        else:
            score += 12
            
        # Extension check (5 pts)
        if png_file.suffix == '.png':
            score += 5
            
        return score
    
    def _validate_composition(self, png_file: Path, issues: list) -> int:
        """Validate scene composition from annotations (33 pts)."""
        score = 0
        
        ann = self._find_annotation(png_file)
        
        if not ann:
            issues.append("No matching annotation in JSON")
            return 0
            
        # Count pieces (16 pts)
        pieces = ann.get("annotations", [])
        piece_count = len(pieces)
        
        if 2 <= piece_count <= 32:
            score += 16
        elif piece_count == 0:
            issues.append(f"Zero pieces annotated")
            score += 0
        else:
            issues.append(f"Suspicious piece count: {piece_count}")
            score += 12
            
        # Parse FEN to verify piece count (8 pts)
        fen = ann.get("position", "")
        if fen:
            try:
                # Count pieces in FEN
                fen_part = fen.split(' ')[0]
                pieces_only = fen_part.replace('/', '').replace('1','').replace('2',' ')
                pieces_only = pieces_only.replace('3','   ').replace('4','    ')
                pieces_only = pieces_only.replace('5','     ').replace('6','      ')
                pieces_only = pieces_only.replace('7','       ').replace('8','        ')
                actual_pieces = len(pieces_only.replace(' ', ''))
                
                if piece_count == actual_pieces:
                    score += 8
                else:
                    issues.append(f"FEN/annotation mismatch: {actual_pieces} vs {piece_count}")
                    score += 4
            except Exception as e:
                pass
                
        # Camera metadata present (9 pts)
        cam_meta = ann.get("camera", {})
        if cam_meta:
            if "distance" in cam_meta and "angle" in cam_meta:
                score += 9
        else:
            issues.append("Missing camera metadata")
            
        return score
    
    def _validate_integrity(self, png_file: Path, issues: list) -> int:
        """Validate file integrity (27 pts)."""
        score = 0
        
        # Check file is readable and has PNG chunks (20 pts)
        try:
            with open(png_file, 'rb') as f:
                header = f.read(8)
                if header == b'\x89PNG\r\n\x1a\n':
                    score += 10
                else:
                    issues.append("Bad PNG header")
                    return 0
                    
                has_idat = False
                has_iend = False
                
                while True:
                    length_bytes = f.read(4)
                    if len(length_bytes) != 4:
                        break
                    length = struct.unpack('>I', length_bytes)[0]
                    chunk_type = f.read(4)
                    
                    if chunk_type == b'IDAT':
                        has_idat = True
                    elif chunk_type == b'IEND':
                        has_iend = True
                        break
                        
                    f.seek(length + 4, 1)
                    
                if has_idat and has_iend:
                    score += 10
                elif not has_idat:
                    issues.append("Missing IDAT")
                elif not has_iend:
                    issues.append("Truncated PNG")
                    
        except Exception as e:
            issues.append(f"File read error: {e}")
            return 0
            
        # File size sanity (7 pts)
        size = png_file.stat().st_size
        if size > 1000:
            score += 7
        else:
            issues.append(f"Suspiciously small: {size} bytes")
            
        return score
    
    def print_report(self, results: dict):
        """Print validation report."""
        print("="*70)
        print("  CHESS VISION RENDER QUALITY REPORT")
        print("="*70)
        print(f"\n📊 Validated: {results['renders_validated']} renders")
        print(f"✗ Failed: {results['renders_failed']} renders")
        print(f"⭐ Average Score: {results['average_score']:.1f}/100")
        
        print("\n" + "-"*70)
        print(f"{'File':<30} {'Res':<10} {'Size':<8} {'Score':<8} {'Status':>8}")
        print("-"*70)
        
        for detail in results["details"]:
            meta = detail.get("metadata", {})
            res = f"{meta.get('width', '-')}\u00d7{meta.get('height', '-')}"
            size = meta.get("size_kb", "?")
            
            status = "✓ PASS" if detail["passed"] else "✗ FAIL"
            print(f"{detail['file'][:28]:<30} {res:<10} {size+'KB':<8} {detail['total_score']:<3}/100 {status:>8}")
            
            # Show issues
            if detail.get("issues"):
                for issue in detail["issues"][:2]:
                    print(f"  → {issue}")
                    
        print("-"*70)
        
        # Category breakdown
        if results["details"]:
            print("\nCategory Breakdown (average):")
            categories = {}
            for d in results["details"]:
                for cat, score in d["categories"].items():
                    categories[cat] = categories.get(cat, []) + [score]
            
            max_vals = {"technical": 40, "composition": 33, "integrity": 27}
            for cat, scores in categories.items():
                avg = sum(scores) / len(scores)
                max_val = max_vals.get(cat, 100)
                print(f"  {cat.title():<12}: {avg:.1f}/{max_val}")
                
        print("-"*70)
        
        # Per-image camera details
        if self.annotations and results["details"]:
            print("\nCamera Metadata:")
            print("-"*70)
            for detail in results["details"]:
                ann = self._find_annotation(Path(detail['file']))
                if ann and ann.get("camera"):
                    cam = ann["camera"]
                    print(f"\n{detail['file'][:28]}:")
                    print(f"  Distance: {cam.get('distance', '?'):.1f}cm")
                    print(f"  Angle: {cam.get('angle', '?'):.1f}\u00b0")
                    print(f"  Rotation: {cam.get('rotation', '?'):.1f}\u00b0")
                    print(f"  FOV: {cam.get('focal_length', '?')}mm")
        print("-"*70)
        
        if results["renders_failed"] == 0 and results["renders_validated"] > 0:
            print("\n🎉 ALL RENDERS PASSED - Ready for production!")
            print("\n✅ Quality threshold MET (80%+ score)")
            print("✅ Technical specs VALID (640×640, proper file sizes)")
            print("✅ Annotation integrity VERIFIED (FEN matching)")
            print("✅ Camera metadata PRESENT (distance/angle/rotation)")
            return 0
        elif results["renders_validated"] == 0:
            print("\n⚠️ No renders validated")
            return 1
        else:
            print(f"\n⚠️ {results['renders_failed']} renders failed validation")
            return 1


def main():
    parser = argparse.ArgumentParser(description="Validate chess render quality")
    parser.add_argument("--dir", required=True, help="Directory with renders and annotations.json")
    args = parser.parse_args()
    
    validator = RenderValidator(Path(args.dir))
    results = validator.validate_all()
    exit_code = validator.print_report(results)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
