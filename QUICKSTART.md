# Media Vault - Quick Start Guide

## Installation & Running Locally

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Add media files:**
   Place your images/videos in `instance/media/` directory (auto-created on first run)
   ```bash
   mkdir -p instance/media
   # Copy your media files here
   ```

3. **Run the app:**
   ```bash
   ./.venv/bin/python app/main.py
   ```
   
   The app will be available at `http://localhost:5000`

## Docker Deployment

### Build the image:
```bash
docker build -t media-vault:latest .
```

### Run the container:
```bash
docker run -p 5000:5000 \
  -v $(pwd)/instance/media:/app/instance/media \
  media-vault:latest
```

## Features

✅ **Browse directories** - Navigate folder structure with breadcrumb navigation  
✅ **Thumbnail previews** - Automatic thumbnail generation for images & videos  
✅ **Animated GIFs** - Full GIF animation support  
✅ **Video preview frames** - Extract and display first frame of videos  
✅ **HTML5 video player** - Built-in player for MP4, WebM, MOV, AVI, MKV  
✅ **Infinite scroll** - Load more items as you scroll down  
✅ **Responsive design** - Works on desktop, tablet, and mobile  
✅ **Security** - Protected against directory traversal attacks  

## Supported Formats

**Images:** PNG, JPG, JPEG, GIF, BMP, WebP, SVG  
**Videos:** MP4, WebM, MOV, AVI, MKV  

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Browse root media directory |
| `/browse/<path>` | GET | Browse specific directory |
| `/view/<path>` | GET | View media file |
| `/api/list/<path>` | GET | Get directory listing (JSON) |
| `/api/thumbnails/<path>` | GET | Get thumbnail image |
| `/media/<path>` | GET | Serve media file |

## Troubleshooting

**Port 5000 already in use?**
```bash
# Kill the process using port 5000
lsof -i :5000 | grep -v COMMAND | awk '{print $2}' | xargs kill -9
```

**Images not showing?**
- Verify media files are in `instance/media/`
- Check file format is supported (see Supported Formats above)
- Try refreshing the browser

**Docker image build fails?**
- Ensure Docker is running
- Check that you have sufficient disk space
- Try: `docker system prune` to free resources

## Future Enhancements

- User authentication & authorization
- Database indexing for fast search
- Metadata management (tags, descriptions)
- File upload, modification, and deletion
- Advanced filtering and sorting
- Favorite collections
- Full-text search

## Development Notes

The app uses:
- **Flask** - Lightweight web framework
- **Pillow** - Image processing for thumbnails
- **OpenCV** - Video frame extraction
- **Bootstrap 5** - Responsive UI framework
- **Infinite scroll** - Client-side pagination with Intersection Observer API

See [README.md](README.md) for detailed documentation.
