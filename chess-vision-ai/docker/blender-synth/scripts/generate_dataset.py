#!/usr/bin/env python3
"""
ChessVision Dataset Generator
Batch FEN-based rendering with randomized camera angles
Based on prototype: /home/jan/Desktop/chess/blender/render_fen.py
"""

import json
import random
import subprocess
import os
import sys
import uuid
from datetime import datetime
import argparse

# Chess piece names for random FEN generation
PIECES = ['P', 'N', 'B', 'R', 'Q', 'K', 'p', 'n', 'b', 'r', 'q', 'k']
BLENDER_BIN = os.environ.get('BLENDER_BIN', 'blender')
OUTPUT_DIR = os.environ.get('OUTPUT_DIR', '/workspace/output')

def generate_random_fen():
    """Generate a random chess position FEN (simplified)."""
    board = [['' for _ in range(8)] for _ in range(8)]
    
    # Place kings
    board[random.randint(0, 7)][random.randint(0, 7)] = 'K'
    
    # Randomly place other pieces
    for piece in 'pnbrqPNBRQ':
        if random.random() < 0.3:  # 30% chance to place each piece type
            squares = [(r, f) for r in range(8) for f in range(8) if board[r][f] == '']
            if squares:
                r, f = random.choice(squares)
                board[r][f] = piece
    
    # Build FEN
    fen_rows = []
    for row in board:
        fen_row = ''
        empty = 0
        for sq in row:
            if sq == '':
                empty += 1
            else:
                if empty:
                    fen_row += str(empty)
                    empty = 0
                fen_row += sq
        if empty:
            fen_row += str(empty)
        fen_rows.append(fen_row)
    
    position = '/'.join(fen_rows)
    active = 'w' if random.random() < 0.5 else 'b'
    castling = '-'
    enpassant = '-'
    halfmove = '0'
    fullmove = '1'
    
    return f"{position} {active} {castling} {enpassant} {halfmove} {fullmove}"

def render_scene(fen, output_id, config):
    """Render single FEN using Blender."""
    output_path = os.path.join(OUTPUT_DIR, 'images', f"{output_id}.png")
    json_path = os.path.join(OUTPUT_DIR, 'ground_truth', f"{output_id}.json")
    
    # Camera randomization
    elevation = random.uniform(config['elevation_min'], config['elevation_max'])
    azimuth = random.uniform(config['azimuth_min'], config['azimuth_max'])
    radius = config['camera_radius']
    
    # Build render command
    cmd = [
        BLENDER_BIN,
        '-b',  # background mode
        '--python', '/workspace/render_fen.py',
        '--',
        '--fen', fen,
        '--output', output_path,
        '--json', json_path,
        '--elevation', str(elevation),
        '--azimuth', str(azimuth),
        '--radius', str(radius)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            return True, output_path
        else:
            return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, "Render timeout"
    except Exception as e:
        return False, str(e)

def main():
    parser = argparse.ArgumentParser(description='Generate synthetic chess dataset')
    parser.add_argument('count', type=int, default=100, help='Number of images to generate')
    parser.add_argument('--config', type=str, default='/workspace/test_render_config.json')
    args = parser.parse_args()
    
    # Load config
    config = {
        'elevation_min': float(os.environ.get('ELEVATION_MIN', 5)),
        'elevation_max': float(os.environ.get('ELEVATION_MAX', 15)),
        'azimuth_min': float(os.environ.get('AZIMUTH_MIN', -60)),
        'azimuth_max': float(os.environ.get('AZIMUTH_MAX', 60)),
        'camera_radius': float(os.environ.get('CAMERA_RADIUS', 18))
    }
    
    # Ensure output directories exist
    os.makedirs(os.path.join(OUTPUT_DIR, 'images'), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, 'ground_truth'), exist_ok=True)
    
    print(f"Starting batch generation of {args.count} images...")
    print(f"Config: {json.dumps(config, indent=2)}")
    print("")
    
    success_count = 0
    failure_count = 0
    
    start_time = datetime.now()
    
    for i in range(args.count):
        fen = generate_random_fen()
        output_id = str(uuid.uuid4())[:8]
        
        success, result = render_scene(fen, output_id, config)
        
        if success:
            success_count += 1
            print(f"[{i+1}/{args.count}] ✓ Rendered: {output_id}")
        else:
            failure_count += 1
            print(f"[{i+1}/{args.count}] ✗ Failed: {result}")
        
        # Progress report
        if (i + 1) % 10 == 0:
            elapsed = datetime.now() - start_time
            rate = (i + 1) / elapsed.total_seconds()
            eta = (args.count - (i + 1)) / rate if rate > 0 else 0
            print(f"    Rate: {rate:.2f} images/sec | ETA: {eta/60:.1f} min")
    
    print("")
    print("=== Summary ===")
    print(f"Generated: {success_count}/{args.count}")
    print(f"Failed: {failure_count}")
    print(f"Total time: {(datetime.now() - start_time).total_seconds()/60:.1f} minutes")
    print(f"Output: {OUTPUT_DIR}")

if __name__ == '__main__':
    main()
