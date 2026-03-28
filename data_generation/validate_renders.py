#!/usr/bin/env python3
"""Chess Vision Render Quality Validator

Automatically scores renders based on technical specs, camera config,
scene composition, and file integrity.

Usage: python validate_renders.py --dir /path/to/renders/
"""

import json
import argparse
from pathlib import Path
from PIL import Image
from typing import Dict, List, Tuple
import sys

class RenderValidator:
    def __init__(self, renders_dir: Path):
        self.renders_dir = Path(renders_dir)
        self.annotations_file = self.renders_dir / "annotations.json"
        
    def validate_all(self) -> Dict:
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
        except FileNotFoundError:
            print(f"✗ Annotations not found: {self.annotations_file}")
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
    
    def validate_single(self, png_file: Path) -> Dict:
        """Validate a single render file."""
        result = {
            "file": png_file.name,
            "passed": True,
            "categories": {},
            "total_score": 0,
            "issues": []
        }
        
        # Technical Specs (max 40 pts)
        tech_score = self._validate_technical(png_file, result["issues"])
        result["categories"]["technical"] = tech_score
        
        # Scene Composition (max 33 pts)
        comp_score = self._validate_composition(png_file, result["issues"])
        result["categories"]["composition"] = comp_score
        
        # File Integrity  
        integ_score = self._validate_integrity(png_file, result["issues"])
        result["categories"]["integrity"] = integ_score
        
        # Calculate total
        result["total_score"] = sum(result["categories"].values())
        result["max_possible"] = 100
        result["percentage"] = (result["total_score"] / result["max_possible"]) * 100
        
        # Pass/Fail threshold
        if result["percentage"] < 80 or result["categories"]["integrity"] < 10:
            result["passed"] = False
            
        return result
    
    def _validate_technical(self, png_file: Path, issues: List) -> int:
        """Validate technical specs (40 pts)."""
        score = 0
        
        try:
            # Open and check dimensions
            img = Image.open(png_file)
            width, height = img.size
            
            # Resolution check (10 pts)
            if width == 640 and height == 640:
                score += 10
            else:
                issues.append(f"Wrong resolution: {width}x{height}")
                score += 0
                
            # Color mode (10 pts)
            if img.mode == 'RGB':
                score += 10
            else:
                issues.append(f"Wrong color mode: {img.mode}")
                
            # File size check (10 pts)
            size_kb = png_file.stat().st_size / 1024
            if 150 <= size_kb <= 800:
                score += 10
            elif size_kb < 100:
                issues.append(f"File too small: {size_kb:.1f}KB (possible corruption)")
            elif size_kb > 1000:
                issues.append(f"File unusually large: {size_kb:.1f}KB")
                
            img.close()
            
        except Exception as e:
            issues.append(f"Cannot open image: {e}")
            return 0
            
        return score
    
    def _validate_composition(self, png_file: Path, issues: List) -> int:
        """Validate scene composition from annotations (33 pts)."""
        score = 0
        
        # Find matching annotation
        file_stem = png_file.stem
        matching = [a for a in self.annotations.get("images", []) 
                   if a["file_name"].startswith(file_stem)]
        
        if not matching:
            issues.append("No matching annotation in JSON")
            return 0
            
        image_info = matching[0]
        image_id = image_info["id"]
        
        # Count pieces (16 pts)
        pieces = [a for a in self.annotations.get("annotations", [])
                 if a["image_id"] == image_id]
        piece_count = len(pieces)
        
        if 2 <= piece_count <= 32:
            score += 16
        else:
            issues.append(f"Suspicious piece count: {piece_count}")
            score += 0
            
        # Validate bbox coordinates are in bounds (8 pts)
        valid_bboxes = all(
            a["bbox"][0] + a["bbox"][2] <= 640 and  # x + w <= 640
            a["bbox"][1] + a["bbox"][3] <= 640 and  # y + h <= 640
            a["bbox"][0] >= 0 and a["bbox"][1] >= 0
            for a in pieces
        )
        
        if valid_bboxes:
            score += 8
        else:
            issues.append("Bounding boxes exceed image bounds")
            
        # Camera metadata present (9 pts)
        if "camera" in image_info.get("metadata", {}):
            score += 9
        else:
            issues.append("Missing camera metadata")
            
        return score
    
    def _validate_integrity(self, png_file: Path, issues: List) -> int:
        """Validate file integrity (20 pts)."""
        score = 0
        
        # Check file is readable (10 pts)
        try:
            img = Image.open(png_file)
            img.verify()  # Verify without loading
            score += 10
        except Exception as e:
            issues.append(f"File integrity error: {e}")
            return 0
            
        # Check for pixel uniformity (10 pts) - detect black renders
        try:
            img = Image.open(png_file).convert('RGB')
            pixels = list(img.getdata())
            total_pixels = len(pixels)
            
            # Check if too many pixels are identical (black/solid render)
            unique_colors = len(set(pixels))
            diversity_ratio = unique_colors / total_pixels
            
            if diversity_ratio > 0.01:  # At least 1% color diversity
                score += 10
            else:
                issues.append(f"Low color diversity ({diversity_ratio:.2%}) - possible black render")
                
            img.close()
        except Exception as e:
            issues.append(f"Pixel check failed: {e}")
            
        return score
    
    def print_report(self, results: Dict):
        """Print validation report."""
        print("="*70)
        print("  CHESS VISION RENDER QUALITY REPORT")
        print("="*70)
        print(f"\nValidated: {results['renders_validated']} renders")
        print(f"Failed: {results['renders_failed']} renders")
        print(f"Average Score: {results['average_score']:.1f}/100")
        
        print("\n" + "-"*70)
        print(f"{'File':<30} {'Score':>10} {'Status':>10}")
        print("-"*70)
        
        for detail in results["details"]:
            status = "✓ PASS" if detail["passed"] else "✗ FAIL"
            print(f"{detail['file'][:28]:<30} {detail['total_score']:>8}/100 {status:>8}")
            
            # Show issues
            if detail.get("issues"):
                for issue in detail["issues"][:3]:  # Max 3 issues
                    print(f"  → {issue}")
                    
        print("-"*70)
        
        if results["renders_failed"] == 0:
            print("\n🎉 ALL RENDERS PASSED - Ready for production!")
        else:
            print(f"\n⚠️ {results['renders_failed']} renders failed validation - review needed")
            return 1
            
        return 0


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
