"""
Dataset management and export functionality.
"""

import json
import csv
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import random

from chess_data_gen.config import Config, ExportFormat


@dataclass
class DatasetSplit:
    """Dataset split configuration."""
    train: float = 0.8
    val: float = 0.1
    test: float = 0.1
    
    def validate(self):
        total = self.train + self.val + self.test
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Split ratios must sum to 1.0, got {total}")


class Dataset:
    """Dataset containing generated samples."""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config
        self.samples: List[Dict[str, Any]] = []
        self.splits: Dict[str, List[int]] = {}  # split_name -> sample indices
    
    def add_sample(self, sample: Dict[str, Any]):
        """Add a sample to the dataset."""
        self.samples.append(sample)
    
    def split(self, train: float = 0.8, val: float = 0.1, test: float = 0.1,
              random_seed: int = 42):
        """Split dataset into train/val/test."""
        split_config = DatasetSplit(train=train, val=val, test=test)
        split_config.validate()
        
        # Shuffle indices
        rng = random.Random(random_seed)
        indices = list(range(len(self.samples)))
        rng.shuffle(indices)
        
        # Calculate split points
        n = len(indices)
        train_end = int(n * train)
        val_end = train_end + int(n * val)
        
        # Assign splits
        self.splits = {
            'train': indices[:train_end],
            'val': indices[train_end:val_end],
            'test': indices[val_end:],
        }
        
        print(f"Dataset split:")
        print(f"  Train: {len(self.splits['train'])} samples")
        print(f"  Val: {len(self.splits['val'])} samples")
        print(f"  Test: {len(self.splits['test'])} samples")
    
    def export(self, output_dir: Path, format: ExportFormat = ExportFormat.COCO):
        """Export dataset to specified format."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if format == ExportFormat.COCO:
            self._export_coco(output_dir)
        elif format == ExportFormat.YOLO:
            self._export_yolo(output_dir)
        elif format == ExportFormat.TFRECORD:
            self._export_tfrecord(output_dir)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_coco(self, output_dir: Path):
        """Export to COCO format."""
        # COCO categories
        categories = [
            {"id": 1, "name": "white_king", "supercategory": "white"},
            {"id": 2, "name": "white_queen", "supercategory": "white"},
            {"id": 3, "name": "white_rook", "supercategory": "white"},
            {"id": 4, "name": "white_bishop", "supercategory": "white"},
            {"id": 5, "name": "white_knight", "supercategory": "white"},
            {"id": 6, "name": "white_pawn", "supercategory": "white"},
            {"id": 7, "name": "black_king", "supercategory": "black"},
            {"id": 8, "name": "black_queen", "supercategory": "black"},
            {"id": 9, "name": "black_rook", "supercategory": "black"},
            {"id": 10, "name": "black_bishop", "supercategory": "black"},
            {"id": 11, "name": "black_knight", "supercategory": "black"},
            {"id": 12, "name": "black_pawn", "supercategory": "black"},
        ]
        
        # Category name to ID mapping
        cat_to_id = {cat["name"]: cat["id"] for cat in categories}
        
        # Export each split
        for split_name, indices in self.splits.items():
            if not indices:
                continue
            
            coco_data = {
                "info": {
                    "description": f"Chess Vision Dataset - {split_name}",
                    "version": "1.0",
                    "year": 2026,
                },
                "images": [],
                "annotations": [],
                "categories": categories,
            }
            
            annotation_id = 1
            
            for idx in indices:
                sample = self.samples[idx]
                
                # Add image
                image_id = idx + 1
                coco_data["images"].append({
                    "id": image_id,
                    "file_name": sample["image_filename"],
                    "width": 640,
                    "height": 640,
                    "extra_info": {
                        "fen": sample["position_fen"],
                        "category": sample["position_category"],
                    }
                })
                
                # Add annotations
                for ann in sample.get("annotations", []):
                    bbox = ann["bbox"]
                    coco_data["annotations"].append({
                        "id": annotation_id,
                        "image_id": image_id,
                        "category_id": cat_to_id.get(ann["class"], 1),
                        "bbox": bbox,  # [x, y, width, height]
                        "area": bbox[2] * bbox[3],
                        "iscrowd": 0,
                        "attributes": {
                            "square": ann.get("square", ""),
                            "occlusion": ann.get("occlusion", 1.0),
                        }
                    })
                    annotation_id += 1
            
            # Save JSON
            output_file = output_dir / f"{split_name}_annotations.json"
            with open(output_file, 'w') as f:
                json.dump(coco_data, f, indent=2)
            
            print(f"  Exported {split_name}: {len(coco_data['images'])} images, "
                  f"{len(coco_data['annotations'])} annotations")
    
    def _export_yolo(self, output_dir: Path):
        """Export to YOLO format."""
        # YOLO: one text file per image, normalized coordinates
        
        # Category mapping
        categories = [
            "white_king", "white_queen", "white_rook", "white_bishop", 
            "white_knight", "white_pawn",
            "black_king", "black_queen", "black_rook", "black_bishop", 
            "black_knight", "black_pawn",
        ]
        cat_to_idx = {cat: idx for idx, cat in enumerate(categories)}
        
        # Save categories file
        with open(output_dir / "classes.txt", 'w') as f:
            f.write('\n'.join(categories))
        
        # Export each split
        for split_name, indices in self.splits.items():
            if not indices:
                continue
            
            labels_dir = output_dir / split_name / "labels"
            images_dir = output_dir / split_name / "images"
            labels_dir.mkdir(parents=True, exist_ok=True)
            images_dir.mkdir(parents=True, exist_ok=True)
            
            for idx in indices:
                sample = self.samples[idx]
                base_name = Path(sample["image_filename"]).stem
                
                # Copy image
                src_image = Path(sample["image_path"])
                dst_image = images_dir / sample["image_filename"]
                if src_image.exists():
                    shutil.copy2(src_image, dst_image)
                
                # Create label file
                label_file = labels_dir / f"{base_name}.txt"
                with open(label_file, 'w') as f:
                    for ann in sample.get("annotations", []):
                        cat_idx = cat_to_idx.get(ann["class"], 0)
                        bbox = ann["bbox"]
                        
                        # Normalize to 0-1
                        x_center = (bbox[0] + bbox[2] / 2) / 640
                        y_center = (bbox[1] + bbox[3] / 2) / 640
                        width = bbox[2] / 640
                        height = bbox[3] / 640
                        
                        f.write(f"{cat_idx} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
            
            print(f"  Exported {split_name}: {len(indices)} images to {output_dir / split_name}")
    
    def _export_tfrecord(self, output_dir: Path):
        """Export to TensorFlow TFRecord format (placeholder)."""
        # TFRecord export would require tensorflow dependency
        # This is a placeholder for the structure
        print("TFRecord export requires TensorFlow. Skipping.")
    
    def statistics(self) -> Dict[str, Any]:
        """Calculate dataset statistics."""
        stats = {
            'total_samples': len(self.samples),
            'total_annotations': sum(
                len(s.get('annotations', [])) for s in self.samples
            ),
            'category_distribution': {},
            'position_categories': {},
        }
        
        for sample in self.samples:
            # Position categories
            cat = sample.get('position_category', 'unknown')
            stats['position_categories'][cat] = stats['position_categories'].get(cat, 0) + 1
            
            # Piece classes
            for ann in sample.get('annotations', []):
                piece_class = ann.get('class', 'unknown')
                stats['category_distribution'][piece_class] = \
                    stats['category_distribution'].get(piece_class, 0) + 1
        
        return stats
    
    def generate_preview_grid(self, rows: int = 4, cols: int = 4, 
                             output_path: Path = None) -> Path:
        """Generate a preview grid of sample images."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            if output_path is None:
                output_path = Path("preview_grid.png")
            
            # Select random samples
            samples = random.sample(self.samples, min(rows * cols, len(self.samples)))
            
            # Create grid
            cell_width, cell_height = 320, 320
            grid = Image.new('RGB', (cols * cell_width, rows * cell_height))
            
            for idx, sample in enumerate(samples):
                if idx >= rows * cols:
                    break
                
                row = idx // cols
                col = idx % cols
                
                # Load image
                img_path = Path(sample['image_path'])
                if img_path.exists():
                    img = Image.open(img_path)
                    img = img.resize((cell_width, cell_height))
                    
                    # Paste into grid
                    grid.paste(img, (col * cell_width, row * cell_height))
            
            grid.save(output_path)
            return output_path
            
        except ImportError:
            print("PIL not available for preview generation")
            return None
