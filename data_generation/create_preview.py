#!/usr/bin/env python3
"""
Create a preview/example image of the chess vision dataset output.
Shows annotated chess board with bounding boxes.
"""

from PIL import Image, ImageDraw, ImageFont
import random
import math

# Create 640x640 image (standard output size)
img_size = 640
img = Image.new('RGB', (img_size, img_size), color=(240, 235, 220))
draw = ImageDraw.Draw(img)

# Draw chess board pattern
board_size = 560
square_size = board_size // 8
offset = (img_size - board_size) // 2

# Wood colors
light_sq = (240, 217, 181)  # Light wood
dark_sq = (181, 136, 99)    # Dark wood
border_color = (60, 40, 30)

# Draw board with border
draw.rectangle([offset-10, offset-10, offset+board_size+10, offset+board_size+10], fill=border_color)

for row in range(8):
    for col in range(8):
        color = light_sq if (row + col) % 2 == 0 else dark_sq
        x = offset + col * square_size
        y = offset + row * square_size
        draw.rectangle([x, y, x + square_size, y + square_size], fill=color)

# Add some pieces as simple shapes with shadows
pieces = [
    # (row, col, color, type)
    (0, 4, 'black', 'K'),  # King e8
    (0, 3, 'black', 'Q'),  # Queen d8
    (0, 0, 'black', 'R'),  # Rook a8
    (0, 7, 'black', 'R'),  # Rook h8
    (0, 2, 'black', 'B'),  # Bishop c8
    (0, 5, 'black', 'B'),  # Bishop f8
    (0, 1, 'black', 'N'),  # Knight b8
    (0, 6, 'black', 'N'),  # Knight g8
    (1, 0, 'black', 'P'),  # Pawns
    (1, 1, 'black', 'P'),
    (1, 2, 'black', 'P'),
    (1, 3, 'black', 'P'),
    (1, 4, 'black', 'P'),
    (7, 4, 'white', 'K'),  # King e1
    (7, 3, 'white', 'Q'),  # Queen d1
    (7, 0, 'white', 'R'),  # Rook a1
    (7, 7, 'white', 'R'),  # Rook h1
    (7, 2, 'white', 'B'),  # Bishop c1
    (7, 5, 'white', 'B'),  # Bishop f1
    (7, 1, 'white', 'N'),  # Knight b1
    (7, 6, 'white', 'N'),  # Knight g1
    (6, 0, 'white', 'P'),  # Pawns
    (6, 1, 'white', 'P'),
    (6, 2, 'white', 'P'),
    (6, 3, 'white', 'P'),
    (6, 4, 'white', 'P'),
]

# Draw pieces with simple shapes
for row, col, color, piece_type in pieces:
    x = offset + col * square_size + square_size // 2
    y = offset + row * square_size + square_size // 2
    radius = square_size // 2 - 5
    
    # Shadow
    shadow_offset = 3
    shadow_color = (80, 80, 80, 100)
    draw.ellipse([x - radius + shadow_offset, y - radius + shadow_offset,
                  x + radius + shadow_offset, y + radius + shadow_offset], fill=(100, 100, 100))
    
    # Piece color
    if color == 'white':
        fill_col = (245, 245, 240)
        outline_col = (200, 200, 190)
    else:
        fill_col = (40, 40, 45)
        outline_col = (80, 80, 90)
    
    # Draw piece
    draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=fill_col, outline=outline_col, width=2)
    
    # Add piece type text
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    text_color = (20, 20, 20) if color == 'white' else (220, 220, 230)
    bbox = draw.textbbox((0, 0), piece_type, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = x - text_width // 2
    text_y = y - text_height // 2 - 2
    draw.text((text_x, text_y), piece_type, fill=text_color, font=font)

# Add some bounding boxes for annotation visualization
annotations = [
    # Highlight a few pieces with bounding boxes
    (7, 4, 'white_king'),
    (7, 3, 'white_queen'),
    (0, 4, 'black_king'),
    (0, 3, 'black_queen'),
]

for row, col, label in annotations:
    x = offset + col * square_size
    y = offset + row * square_size
    bbox_color = (50, 200, 50)  # Green
    
    # Draw bounding box
    draw.rectangle([x-2, y-2, x+square_size+2, y+square_size+2], outline=bbox_color, width=3)
    
    # Draw label background
    label_y = y - 18
    draw.rectangle([x, label_y, x + len(label) * 7 + 4, label_y + 16], fill=bbox_color)
    draw.text((x+2, label_y+1), label, fill=(255, 255, 255))

# Add overlay text
overlay_text = [
    "Chess Vision Dataset Preview",
    "Resolution: 640×640",
    "Format: COCO Annotations",
    "Pieces: Tournament Staunton",
    "Board: Walnut Classic 56cm",
]

overlay_y = 10
for i, text in enumerate(overlay_text):
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font = ImageFont.load_default()
    
    # Semi-transparent background
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    draw.rectangle([5, overlay_y + i*18, 10 + text_width, overlay_y + i*18 + 16], fill=(0, 0, 0, 180))
    draw.text((8, overlay_y + i*18), text, fill=(255, 255, 255), font=font)

# Add grid overlay to show coordinates
for i in range(9):
    # Files (a-h)
    x = offset + i * square_size
    if i < 8:
        file_char = chr(ord('a') + i)
        draw.text((x + square_size//2 - 3, offset + board_size + 2), file_char, fill=(80, 80, 80))
    
    # Ranks (1-8)
    y = offset + i * square_size
    if i < 8:
        rank_char = str(8 - i)
        draw.text((offset - 10, y + square_size//2 - 5), rank_char, fill=(80, 80, 80))

# Save
output_path = "/home/node/.openclaw/workspace/data_generation/preview_example.png"
img.save(output_path, quality=95)
print(f"✓ Preview saved to: {output_path}")

# Also create a variation showing different lighting
img2 = img.copy()
draw2 = ImageDraw.Draw(img2)

# Add warm lighting overlay
for i in range(img_size):
    for j in range(img_size):
        pixel = img2.getpixel((i, j))
        # Warm color grading
        new_pixel = (
            min(255, int(pixel[0] * 1.1)),  # More red
            min(255, int(pixel[1] * 0.95)),  # Less green
            min(255, int(pixel[2] * 0.85)),  # Less blue
        )
        img2.putpixel((i, j), new_pixel)

output_path2 = "/home/node/.openclaw/workspace/data_generation/preview_warm_lighting.png"
img2.save(output_path2, quality=95)
print(f"✓ Warm lighting variant saved to: {output_path2}")

print("\n✓ Preview images generated!")
