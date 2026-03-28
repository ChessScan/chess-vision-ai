FROM ubuntu:22.04

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    unzip \
    xz-utils \
    zip \
    libglu1-mesa \
    openjdk-17-jdk \
    wget \
    python3 \
    python3-pip \
    nodejs \
    npm \
    socat \
    gdb \
    libstdc++6 \
    fonts-droid-fallback \
    && rm -rf /var/lib/apt/lists/*

# Set Java environment
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Install Flutter
ENV FLUTTER_VERSION=3.19.3
ENV FLUTTER_HOME=/opt/flutter
ENV PATH="${FLUTTER_HOME}/bin:${PATH}"

RUN git clone -b stable --depth 1 https://github.com/flutter/flutter.git ${FLUTTER_HOME}

# Pre-download Flutter dependencies
RUN flutter doctor && \
    flutter config --no-analytics && \
    flutter precache

# Install Android SDK
ENV ANDROID_SDK_ROOT=/opt/android-sdk
ENV PATH="${ANDROID_SDK_ROOT}/cmdline-tools/latest/bin:${ANDROID_SDK_ROOT}/platform-tools:${PATH}"

RUN mkdir -p ${ANDROID_SDK_ROOT}/cmdline-tools && \
    cd ${ANDROID_SDK_ROOT}/cmdline-tools && \
    wget -q https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip && \
    unzip commandlinetools-linux-11076708_latest.zip && \
    mv cmdline-tools latest && \
    rm commandlinetools-linux-11076708_latest.zip

# Accept Android licenses and install tools
RUN yes | sdkmanager --licenses && \
    sdkmanager "platform-tools" "build-tools;34.0.0" \
               "platforms;android-34" \
               "emulator" \
               "system-images;android-34;google_apis;x86_64"

# Create app directory
WORKDIR /app

# Copy pubspec files first for caching
COPY pubspec.* ./
RUN flutter pub get

# Copy entire app
COPY . .

# Get dependencies again after full copy
RUN flutter pub get

# Expose ports for Flutter web and debugging
EXPOSE 8080 5037 5555

# Default command
CMD ["bash"]
