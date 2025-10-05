# Start with an Anyscale base image.
# Use the drop-down above to browse through all available images.
FROM anyscale/ray:2.49.2-slim-py312-cu128

# Install system dependencies
RUN sudo apt-get update && sudo apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    portaudio19-dev \
    ffmpeg \
    libsndfile1
