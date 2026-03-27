#!/bin/bash
# Download remaining large assets (run this after cloning)
# These are too large for git - download them separately

echo "=== Chess Vision Asset Downloader ==="
cd "$(dirname "$0")"

# Wood texture sets to download
echo ""
echo "Downloading wood textures (Polyhaven CC0)..."

# Walnut set
echo "  - walnut textures..."
cd boards/walnut_4k
[ ! -f "wood_table_worn_diff_4k.exr" ] && curl -fLO "https://dl.polyhaven.org/file/ph-assets/Textures/exr/4k/wood_table_worn/wood_table_worn_diff_4k.exr"
[ ! -f "wood_table_worn_nor_gl_4k.exr" ] && curl -fLO "https://dl.polyhaven.org/file/ph-assets/Textures/exr/4k/wood_table_worn/wood_table_worn_nor_gl_4k.exr"
[ ! -f "wood_table_worn_rough_4k.exr" ] && curl -fLO "https://dl.polyhaven.org/file/ph-assets/Textures/exr/4k/wood_table_worn/wood_table_worn_rough_4k.exr"
cd ../..

# Maple set  
echo "  - maple textures..."
cd boards/maple_4k
[ ! -f "wood_floor_deck_diff_4k.exr" ] && curl -fLO "https://dl.polyhaven.org/file/ph-assets/Textures/exr/4k/wood_floor_deck/wood_floor_deck_diff_4k.exr"
cd ../..

# HDRI environments
echo ""
echo "Downloading HDRI environments (Polyhaven CC0)..."

cd hdri/office
[ ! -f "kloetzle_blei_4k.hdr" ] && curl -fLO "https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/4k/kloetzle_blei_4k.hdr"
cd ../..

cd hdri/studio
[ ! -f "studio_small_09_4k.exr" ] && curl -fLO "https://dl.polyhaven.org/file/ph-assets/HDRIs/exr/4k/studio_small_09_4k.exr"
cd ../..

cd hdri/home
[ ! -f "apartment_4k.exr" ] && curl -fLO "https://dl.polyhaven.org/file/ph-assets/HDRIs/exr/4k/hotel_room_4k.exr"
cd ../..

cd hdri/outdoor
[ ! -f "indoor_pool_4k.exr" ] && curl -fLO "https://dl.polyhaven.org/file/ph-assets/HDRIs/exr/4k/indoor_pool_4k.exr"
cd ../..

echo ""
echo "=== Complete ==="
echo "Run check_assets.sh to verify download succeeded."
