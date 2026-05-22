# Media Vault

A Flask-based media browser for browsing and previewing media files organized in directories. Features include thumbnail previews, animated GIFs, video preview frames, and infinite scroll pagination.

## Features

- 📁 Browse media directories with thumbnail previews
- 🖼️ Support for common image formats (PNG, JPG, GIF, BMP, WebP, SVG)
- 🎬 Support for video formats (MP4, WebM, MOV, AVI, MKV) with preview frames
- ✨ Animated GIF support
- 📜 Infinite scroll pagination for large directories
- 🔒 Security-hardened path handling (prevents directory traversal)
- 🎨 Responsive design with Bootstrap 5
- 🐳 Docker-ready deployment

## Supported Formats

**Images:** PNG, JPG, JPEG, GIF, BMP, WebP, SVG

**Videos:** MP4, WebM, MOV, AVI, MKV

## Prerequisites

- Python 3.11+
- FFmpeg (for video processing)
- [uv](https://github.com/astral-sh/uv) package manager (recommended)

## Installation

### Local Development

1. Clone the repository:
```bash
cd media-vault-anthropic
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Run the development server:
```bash
python app/main.py
```

The app will be available at `http://localhost:5000`

### Adding Media

1. Create a media directory or place files in `instance/media/`
2. Supported files will automatically appear in the browser
3. Subdirectories are supported

## Docker Deployment

1. Build the Docker image:
```bash
docker build -t media-vault .
```

2. Run the container:
```bash
docker run \
    -p 5000:5000 \
    -v $(pwd)/instance/media:/app/instance/media \
    -v $(pwd)/instance/thumbnails:/app/instance/thumbnails \
    media-vault
```

The app will be accessible at `http://localhost:5000`

## Project Structure

```
media-vault-anthropic/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── main.py               # Entry point
│   ├── routes.py             # Route handlers
│   ├── media_handler.py      # Media utilities
│   ├── security.py           # Path validation
│   ├── templates/
│   │   ├── base.html         # Base template
│   │   ├── browse.html       # Directory listing
│   │   ├── view.html         # Media viewer
│   │   └── error.html        # Error page
│   └── static/
│       ├── style.css         # Styles
│       └── script.js         # Client-side logic
├── instance/
│   └── media/                # Media directory
├── Dockerfile
├── pyproject.toml
└── README.md
```

## API Endpoints

- `GET /` - Browse root media directory
- `GET /browse/<path>` - Browse a specific directory
- `GET /view/<path>` - View a media file
- `GET /api/list/<path>` - Get directory listing (JSON)
- `GET /api/thumbnails/<path>` - Get thumbnail for a file
- `GET /media/<path>` - Serve media file

## Future Features

- User accounts and authentication
- Database indexing for quick search
- Metadata management for media items
- File upload, modification, and deletion
- Advanced filtering and sorting
- Favoriting and collections

## Development

### Adding New Features

The app is structured to be extensible:
- `media_handler.py` - Add new media processing functions
- `routes.py` - Add new endpoints
- `templates/` - Add new pages or modify layouts
- `static/` - Add styles or scripts

### Testing

Create test media files in `instance/media/`:
```bash
# Create a test directory structure
mkdir -p instance/media/test_dir
# Place images and videos in the media directory
```