# ChessVision Blender Synthetic Data Generator
# Based on /home/jan/Desktop/chess prototype

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV BLENDER_VERSION=4.0.2
ENV BLENDER_URL=https://download.blender.org/release/Blender4.0/blender-4.0.2-linux-x64.tar.xz

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    tar \
    xz-utils \
    python3 \
    python3-pip \
    libgl1 \
    libxi6 \
    libxrender1 \
    libxfixes3 \
    libxxf86vm1 \
    libxkbcommon0 \
    libsm6 \
    libegl1 \
    libglx-mesa0 \
    && rm -rf /var/lib/apt/lists/*

# Download and install Blender
RUN wget -q ${BLENDER_URL} -O /tmp/blender.tar.xz && \
    tar -xf /tmp/blender.tar.xz -C /opt && \
    rm /tmp/blender.tar.xz && \
    mv /opt/blender-* /opt/blender && \
    ln -s /opt/blender/blender /usr/local/bin/blender

# Set up working directory
WORKDIR /workspace

# Copy Blender assets and render script
COPY blender/render_fen.py /workspace/
COPY blender/assets /workspace/assets
COPY blender/test_render_config.json /workspace/
COPY blender/example_render_tasks.json /workspace/

# Create output directories
RUN mkdir -p /workspace/output/images /workspace/output/ground_truth

# Python dependencies
RUN pip3 install --break-system-packages --no-cache-dir \
    numpy \
    pillow

# Entrypoint script
COPY entrypoint.sh /workspace/
RUN chmod +x /workspace/entrypoint.sh

# Environment variables for rendering
ENV PYTHONUNBUFFERED=1
ENV BLENDER_BIN=/usr/local/bin/blender
ENV RENDER_TASKS=/workspace/tasks.json
ENV OUTPUT_DIR=/workspace/output

ENTRYPOINT ["/workspace/entrypoint.sh"]
CMD ["--help"]
