FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for media processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml .
COPY app/ ./app/

# Install Python dependencies using uv
RUN uv sync --frozen

# Create instance/media directory
RUN mkdir -p /app/instance/media

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Run the Flask app
CMD [".venv/bin/python", "app/main.py"]
