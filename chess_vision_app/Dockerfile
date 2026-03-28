FROM cirrusci/flutter:3.19.4

USER root

# Install additional dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    unzip \
    xz-utils \
    zip \
    libglu1-mesa \
    socat \
    fonts-droid-fallback \
    && rm -rf /var/lib/apt/lists/*

# Ensure flutter is available and up-to-date
RUN flutter config --no-analytics && \
    flutter doctor -v

# Setup working directory
WORKDIR /app
RUN chmod 777 /app

# Pre-cache dependencies
COPY pubspec.yaml ./
RUN flutter pub get

# Copy the rest of the app (will be overridden by volume mount)
COPY . .

# Expose ports for Flutter web
EXPOSE 8080 5555

# Run as default user
USER flutteruser

CMD ["bash"]
