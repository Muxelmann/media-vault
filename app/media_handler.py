import os
from pathlib import Path
from io import BytesIO
import mimetypes

from PIL import Image
import cv2


SUPPORTED_IMAGE_FORMATS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg"}
SUPPORTED_VIDEO_FORMATS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}
SUPPORTED_MEDIA_FORMATS = SUPPORTED_IMAGE_FORMATS | SUPPORTED_VIDEO_FORMATS

# Thumbnail cache directory (set by routes.py)
THUMBNAIL_CACHE_ROOT = None


def set_thumbnail_cache_root(cache_root):
    """Set the root directory for thumbnail cache."""
    global THUMBNAIL_CACHE_ROOT
    THUMBNAIL_CACHE_ROOT = Path(cache_root) if cache_root else None
    if THUMBNAIL_CACHE_ROOT:
        THUMBNAIL_CACHE_ROOT.mkdir(parents=True, exist_ok=True)


def get_thumbnail_cache_path(media_root, media_filepath):
    """
    Get the cache path for a thumbnail.

    Args:
        media_root: Root media directory
        media_filepath: Absolute path to media file

    Returns:
        Path object for thumbnail cache location
    """
    if not THUMBNAIL_CACHE_ROOT:
        return None

    media_root = Path(media_root).resolve()
    media_filepath = Path(media_filepath).resolve()

    try:
        # Get relative path from media root
        rel_path = media_filepath.relative_to(media_root)
        # Create thumbnail filename with .thumb extension
        thumb_name = rel_path.stem + '.thumb' + (rel_path.suffix or '.jpg')
        # Build cache path mirroring media structure
        cache_path = THUMBNAIL_CACHE_ROOT / rel_path.parent / thumb_name
        return cache_path
    except (ValueError, OSError) as e:
        print(f"Error calculating cache path for {media_filepath}: {e}")
        return None


def is_media_file(filepath):
    """Check if file is a supported media file."""
    if not isinstance(filepath, Path):
        filepath = Path(filepath)
    return filepath.suffix.lower() in SUPPORTED_MEDIA_FORMATS


def is_directory(filepath):
    """Check if path is a directory."""
    if not isinstance(filepath, Path):
        filepath = Path(filepath)
    return filepath.is_dir()


def get_file_info(filepath):
    """Get metadata about a file."""
    if not isinstance(filepath, Path):
        filepath = Path(filepath)

    if not filepath.exists():
        return None

    is_dir = filepath.is_dir()
    is_media = is_media_file(filepath) if not is_dir else False
    file_type = "directory" if is_dir else "file"

    if not is_dir:
        file_type_cat = "image" if filepath.suffix.lower() in SUPPORTED_IMAGE_FORMATS else "video"
    else:
        file_type_cat = None

    return {
        "name": filepath.name,
        "path": str(filepath),
        "is_dir": is_dir,
        "is_media": is_media,
        "type": file_type,
        "media_type": file_type_cat,
        "suffix": filepath.suffix.lower(),
        "size": filepath.stat().st_size if filepath.is_file() else None,
    }


def list_directory(dirpath, offset=0, limit=20):
    """
    List files in a directory with pagination.

    Args:
        dirpath: Path object to directory
        offset: Pagination offset
        limit: Items per page

    Returns:
        Dict with total count, items, and pagination info
    """
    if not isinstance(dirpath, Path):
        dirpath = Path(dirpath)

    if not dirpath.is_dir():
        return None

    try:
        all_items = sorted(
            (item for item in dirpath.iterdir() if not item.name.startswith('.')),
            key=lambda x: (not x.is_dir(), x.name.lower())
        )
    except PermissionError:
        return None

    total = len(all_items)
    items = [get_file_info(item) for item in all_items[offset : offset + limit]]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": items,
        "has_more": (offset + limit) < total,
    }


def generate_image_thumbnail(filepath, media_root=None, size=(150, 150)):
    """
    Generate thumbnail for an image file. Handles animated GIFs.
    Caches thumbnails to disk if media_root is provided.
    """
    try:
        filepath = Path(filepath)

        with Image.open(filepath) as img:
            # Check if image is animated GIF
            is_animated = hasattr(img, 'is_animated') and img.is_animated

            if is_animated:
                # Create animated GIF thumbnail
                frames = []
                durations = []

                try:
                    while True:
                        # Extract frame and duration
                        frame = img.convert("RGBA")
                        durations.append(img.info.get('duration', 100))

                        # Resize frame
                        frame.thumbnail(size, Image.Resampling.LANCZOS)
                        frames.append(frame)

                        # Move to next frame
                        img.seek(img.tell() + 1)
                except EOFError:
                    pass

                if frames:
                    output = BytesIO()
                    frames[0].save(
                        output,
                        format="GIF",
                        save_all=True,
                        append_images=frames[1:],
                        duration=durations,
                        loop=0,
                        optimize=False,
                    )
                    output.seek(0)
                    thumb_data = output.getvalue()

                    # Save to cache if enabled
                    if media_root:
                        cache_path = get_thumbnail_cache_path(media_root, filepath)
                        if cache_path:
                            try:
                                cache_path.parent.mkdir(parents=True, exist_ok=True)
                                with open(cache_path, 'wb') as f:
                                    f.write(thumb_data)
                            except Exception as e:
                                print(f"Warning: Failed to cache thumbnail for {filepath}: {e}")

                    return thumb_data
            else:
                # Static image - convert to JPEG
                if img.mode in ("RGBA", "LA", "P"):
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                    img = bg

                img.thumbnail(size, Image.Resampling.LANCZOS)

                output = BytesIO()
                img.save(output, format="JPEG", quality=85)
                output.seek(0)
                thumb_data = output.getvalue()

                # Save to cache if enabled
                if media_root:
                    cache_path = get_thumbnail_cache_path(media_root, filepath)
                    if cache_path:
                        try:
                            cache_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(cache_path, 'wb') as f:
                                f.write(thumb_data)
                        except Exception as e:
                            print(f"Warning: Failed to cache thumbnail for {filepath}: {e}")

                return thumb_data
    except Exception as e:
        print(f"Error generating image thumbnail for {filepath}: {e}")
        return None


def generate_video_thumbnail(filepath, media_root=None, size=(150, 150)):
    """
    Generate thumbnail from first frame of video file.
    Caches thumbnail to disk if media_root is provided.
    """
    try:
        filepath = Path(filepath)
        cap = cv2.VideoCapture(str(filepath))
        ret, frame = cap.read()
        cap.release()

        if not ret:
            return None

        # Convert BGR to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)

        # Resize thumbnail
        img.thumbnail(size, Image.Resampling.LANCZOS)

        # Convert to JPEG bytes
        output = BytesIO()
        img.save(output, format="JPEG", quality=85)
        output.seek(0)
        thumb_data = output.getvalue()

        # Save to cache if enabled
        if media_root:
            cache_path = get_thumbnail_cache_path(media_root, filepath)
            if cache_path:
                try:
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(cache_path, 'wb') as f:
                        f.write(thumb_data)
                except Exception as e:
                    print(f"Warning: Failed to cache thumbnail for {filepath}: {e}")

        return thumb_data
    except Exception as e:
        print(f"Error generating video thumbnail for {filepath}: {e}")
        return None


def get_thumbnail(filepath, media_root=None):
    """
    Get or generate thumbnail for media file.
    Checks cache first, generates if needed, then caches for future use.

    Args:
        filepath: Path to media file
        media_root: Root media directory (enables caching)

    Returns:
        Bytes of thumbnail image or None if failed
    """
    if not isinstance(filepath, Path):
        filepath = Path(filepath)

    filepath = filepath.resolve()

    if not filepath.exists():
        return None

    # Check cache first
    if media_root:
        cache_path = get_thumbnail_cache_path(media_root, filepath)
        if cache_path:
            if cache_path.exists():
                try:
                    with open(cache_path, 'rb') as f:
                        thumb_data = f.read()
                        import sys
                        print(f"[CACHE HIT] {filepath.name}", file=sys.stderr)
                        return thumb_data
                except Exception as e:
                    import sys
                    print(f"[CACHE ERROR] Failed to read {cache_path}: {e}", file=sys.stderr)
                    # Fall through to generate
            else:
                import sys
                print(f"[CACHE MISS] {cache_path}", file=sys.stderr)
        else:
            import sys
            print(f"[CACHE DISABLED] media_root={media_root}, cache_root={THUMBNAIL_CACHE_ROOT}", file=sys.stderr)
    else:
        import sys
        print(f"[NO MEDIA_ROOT] {filepath.name}", file=sys.stderr)

    suffix = filepath.suffix.lower()

    if suffix in SUPPORTED_IMAGE_FORMATS:
        return generate_image_thumbnail(filepath, media_root=media_root)
    elif suffix in SUPPORTED_VIDEO_FORMATS:
        return generate_video_thumbnail(filepath, media_root=media_root)

    return None


def get_mime_type(filepath):
    """Get MIME type for a file."""
    if not isinstance(filepath, Path):
        filepath = Path(filepath)

    mime_type, _ = mimetypes.guess_type(str(filepath))
    return mime_type or "application/octet-stream"
