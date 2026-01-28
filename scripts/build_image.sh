#!/bin/bash

# Check if competition argument is provided
if [ $# -eq 0 ]; then
    echo "Error: Please provide a competition name as an argument"
    echo "Usage: $0 <competition>"
    exit 1
fi

# Get the competition from the first argument
COMPETITION="$1"

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Verify that the competition data directory exists
COMPETITION_DATA_DIR="$PROJECT_ROOT/yak_server/data/$COMPETITION"
if [ ! -d "$COMPETITION_DATA_DIR" ]; then
    echo "Error: Competition data directory does not exist: $COMPETITION_DATA_DIR"
    exit 1
fi

# Get the yak version
YAK_VERSION=$(uv version --short 2>/dev/null || echo "unknown")

# Check if version is unknown and exit
if [ "$YAK_VERSION" = "unknown" ]; then
    echo "Error: Unable to determine yak version. Please ensure uv is installed and working."
    exit 1
fi

# Build the Docker image
IMAGE_NAME="yak-server:$YAK_VERSION-$COMPETITION"
echo "Building Docker image: $IMAGE_NAME"

docker buildx build \
    --load \
    --build-arg "COMPETITION=$COMPETITION" \
    -t "$IMAGE_NAME" \
    "$PROJECT_ROOT"

# Check if docker build was successful
if [ $? -eq 0 ]; then
    echo "Successfully built image: $IMAGE_NAME"
else
    echo "Error: Docker build failed"
    exit 1
fi
