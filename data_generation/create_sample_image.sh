#!/bin/bash
# Create chess sample image using ImageMagick step by step

cd /home/node/.openclaw/workspace/data_generation

# Base image (wood background)
convert -size 640x640 xc:"#8B7355" base.png

# Create board
cp base.png board.png

# Draw border
convert board.png -stroke "#3d2914" -strokewidth 20 -fill none \
  -draw "rectangle 30,30 610,610" board.png

# Draw light squares (checkered pattern)
for row in 0 2 4 6; do
  for col in 0 2 4 6; do
    x1=$((40 + col * 70))
    y1=$((40 + row * 70))
    x2=$((x1 + 70))
    y2=$((y1 + 70))
    convert board.png -fill "#f0d9b5" -draw "rectangle $x1,$y1 $x2,$y2" board.png
  done
done

# Draw dark squares
for row in 1 3 5 7; do
  for col in 1 3 5 7; do
    x1=$((40 + col * 70))
    y1=$((40 + row * 70))
    x2=$((x1 + 70))
    y2=$((y1 + 70))
    convert board.png -fill "#b58863" -draw "rectangle $x1,$y1 $x2,$y2" board.png
  done
done

# Draw a few dark squares on alternates too
for row in 0 2 4 6; do
  for col in 1 3 5 7; do
    x1=$((40 + col * 70))
    y1=$((40 + row * 70))
    x2=$((x1 + 70))
    y2=$((y1 + 70))
    convert board.png -fill "#b58863" -draw "rectangle $x1,$y1 $x2,$y2" board.png
  done
done

for row in 1 3 5 7; do
  for col in 0 2 4 6; do
    x1=$((40 + col * 70))
    y1=$((40 + row * 70))
    x2=$((x1 + 70))
    y2=$((y1 + 70))
    convert board.png -fill "#b58863" -draw "rectangle $x1,$y1 $x2,$y2" board.png
  done
done

# Add "white pieces" (some white circles on bottom)
convert board.png -fill "#f5f5f0" -draw "circle 285,570 270,570" \
  -fill "#f5f5f0" -draw "circle 355,570 340,570" \
  -fill "#1a1a1a" -draw "circle 285,80 270,80" \
  -fill "#1a1a1a" -draw "circle 355,80 340,80" \
  with_pieces.png

# Add bounding box
convert with_pieces.png \
  -stroke "#4ade80" -strokewidth 4 -fill none \
  -draw "rectangle 280,525 360,605" \
  -fill "#4ade80" -draw "rectangle 280,505 360,525" \
  sample_pipeline_output.png

echo "Created: sample_pipeline_output.png"
ls -la sample_pipeline_output.png

# Cleanup
rm -f base.png board.png with_pieces.png