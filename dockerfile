FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for media processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

# Copy project files
COPY pyproject.toml .
COPY app/ ./app/
COPY uv.lock .

# Install Python dependencies using uv
RUN uv sync --frozen

# Create instance/media and instance/thumbnails directories
RUN mkdir -p /app/instance/media
RUN mkdir -p /app/instance/thumbnails

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Run the Flask app with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "app.main:create_app"]
