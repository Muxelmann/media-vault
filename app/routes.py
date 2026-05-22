from pathlib import Path
from flask import Blueprint, render_template, current_app, send_file, jsonify, request
from urllib.parse import quote

from app.security import secure_path
from app.media_handler import (
    list_directory,
    get_file_info,
    get_thumbnail,
    is_directory,
    is_media_file,
    get_mime_type,
    set_thumbnail_cache_root,
)

bp = Blueprint("main", __name__)


def get_breadcrumbs(rel_path):
    """Generate breadcrumb navigation from path."""
    if not rel_path or rel_path == ".":
        return [("Home", "/")]

    parts = Path(rel_path).parts
    breadcrumbs = [("Home", "/")]

    accumulated = ""
    for part in parts:
        accumulated = str(Path(accumulated) / part)
        breadcrumbs.append((part, f"/browse/{quote(accumulated)}"))

    return breadcrumbs


@bp.route("/")
def index():
    """Browse root media directory."""
    media_root = Path(current_app.config["MEDIA_ROOT"])
    offset = request.args.get("offset", 0, type=int)
    limit = request.args.get("limit", 20, type=int)

    result = list_directory(media_root, offset=offset, limit=limit)
    if result is None:
        return render_template("error.html", message="Cannot access media directory"), 400

    # Convert absolute paths to relative paths in items for templates
    items_with_rel_paths = []
    for item in result["items"]:
        item_copy = item.copy()
        item_path = Path(item["path"])
        item_copy["path"] = str(item_path.relative_to(media_root))
        items_with_rel_paths.append(item_copy)

    return render_template(
        "browse.html",
        items=items_with_rel_paths,
        total=result["total"],
        offset=offset,
        limit=limit,
        has_more=result["has_more"],
        breadcrumbs=get_breadcrumbs(""),
        current_path="",
    )


@bp.route("/browse/<path:filepath>")
def browse(filepath):
    """Browse a specific directory."""
    media_root = Path(current_app.config["MEDIA_ROOT"])

    # Validate path
    safe = secure_path(media_root, filepath)
    if safe is None:
        return render_template("error.html", message="Invalid path"), 400

    # Check if directory
    if not is_directory(safe):
        return render_template("error.html", message="Not a directory"), 400

    offset = request.args.get("offset", 0, type=int)
    limit = request.args.get("limit", 20, type=int)

    result = list_directory(safe, offset=offset, limit=limit)
    if result is None:
        return render_template("error.html", message="Cannot access directory"), 400

    # Calculate relative path for breadcrumbs and convert items to use relative paths
    rel_path = safe.relative_to(media_root)

    # Convert absolute paths to relative paths in items for templates
    items_with_rel_paths = []
    for item in result["items"]:
        item_copy = item.copy()
        item_path = Path(item["path"])
        item_copy["path"] = str(item_path.relative_to(media_root))
        items_with_rel_paths.append(item_copy)

    return render_template(
        "browse.html",
        items=items_with_rel_paths,
        total=result["total"],
        offset=offset,
        limit=limit,
        has_more=result["has_more"],
        breadcrumbs=get_breadcrumbs(str(rel_path)),
        current_path=filepath,
    )


@bp.route("/view/<path:filepath>")
def view(filepath):
    """View a media file."""
    media_root = Path(current_app.config["MEDIA_ROOT"])

    # Validate path
    safe = secure_path(media_root, filepath)
    if safe is None:
        return render_template("error.html", message="Invalid path"), 400

    if not safe.exists():
        return render_template("error.html", message="File not found"), 404

    # If directory, redirect to browse
    if is_directory(safe):
        return f'/browse/{filepath}', 302

    # Get file info
    file_info = get_file_info(safe)
    file_info["mime_type"] = get_mime_type(safe)
    rel_path = safe.relative_to(media_root)
    parent_path = rel_path.parent

    # Calculate prev/next navigation
    parent_dir = safe.parent
    prev_file = None
    next_file = None
    current_index = None
    total_media_files = 0

    try:
        # Get all items in parent directory, sorted same as browse page
        all_items = sorted(
            (item for item in parent_dir.iterdir() if not item.name.startswith('.')),
            key=lambda x: (not x.is_dir(), x.name.lower())
        )
        # Filter to media files only
        media_items = [item for item in all_items if is_media_file(item)]
        total_media_files = len(media_items)

        # Find current file in media list
        for idx, item in enumerate(media_items):
            if item == safe:
                current_index = idx
                break

        # Calculate prev/next relative paths
        if current_index is not None:
            if current_index > 0:
                prev_file = str(media_items[current_index - 1].relative_to(media_root))
            if current_index < len(media_items) - 1:
                next_file = str(media_items[current_index + 1].relative_to(media_root))
    except PermissionError:
        pass

    return render_template(
        "view.html",
        file_info=file_info,
        file_path=str(rel_path),
        parent_path=str(parent_path) if str(parent_path) != "." else "",
        breadcrumbs=get_breadcrumbs(str(rel_path)),
        prev_file=prev_file,
        next_file=next_file,
        current_index=current_index,
        total_media_files=total_media_files,
    )


@bp.route("/api/list/")
def api_list_root():
    """API endpoint for root directory listing."""
    media_root = Path(current_app.config["MEDIA_ROOT"])
    offset = request.args.get("offset", 0, type=int)
    limit = request.args.get("limit", 20, type=int)

    result = list_directory(media_root, offset=offset, limit=limit)
    if result is None:
        return jsonify({"error": "Cannot access directory"}), 400

    # Convert absolute paths to relative paths in items for API response
    items_with_rel_paths = []
    for item in result["items"]:
        item_copy = item.copy()
        item_path = Path(item["path"])
        item_copy["path"] = str(item_path.relative_to(media_root))
        items_with_rel_paths.append(item_copy)

    return jsonify({
        "total": result["total"],
        "offset": result["offset"],
        "limit": result["limit"],
        "items": items_with_rel_paths,
        "has_more": result["has_more"],
    })


@bp.route("/api/list/<path:filepath>")
def api_list(filepath):
    """API endpoint for directory listing (used by infinite scroll)."""
    media_root = Path(current_app.config["MEDIA_ROOT"])

    # Validate path
    safe = secure_path(media_root, filepath)

    if safe is None:
        return jsonify({"error": "Invalid path"}), 400

    if not is_directory(safe):
        return jsonify({"error": "Not a directory"}), 400

    offset = request.args.get("offset", 0, type=int)
    limit = request.args.get("limit", 20, type=int)

    result = list_directory(safe, offset=offset, limit=limit)
    if result is None:
        return jsonify({"error": "Cannot access directory"}), 400

    # Convert absolute paths to relative paths in items for API response
    items_with_rel_paths = []
    for item in result["items"]:
        item_copy = item.copy()
        item_path = Path(item["path"])
        item_copy["path"] = str(item_path.relative_to(media_root))
        items_with_rel_paths.append(item_copy)

    return jsonify({
        "total": result["total"],
        "offset": result["offset"],
        "limit": result["limit"],
        "items": items_with_rel_paths,
        "has_more": result["has_more"],
    })


@bp.route("/api/thumbnails/<path:filepath>")
def api_thumbnail(filepath):
    """API endpoint for thumbnail generation with caching."""
    media_root = Path(current_app.config["MEDIA_ROOT"])

    # Validate path
    safe = secure_path(media_root, filepath)
    if safe is None:
        return jsonify({"error": "Invalid path"}), 400

    if not safe.exists():
        return jsonify({"error": "File not found"}), 404

    if is_directory(safe):
        return jsonify({"error": "Cannot thumbnail directory"}), 400

    # Get thumbnail (with caching)
    thumbnail_data = get_thumbnail(safe, media_root=media_root)
    if thumbnail_data is None:
        return jsonify({"error": "Cannot generate thumbnail"}), 400

    # Determine MIME type based on source file
    # GIF thumbnails are returned as animated GIFs, others as JPEG
    is_gif = safe.suffix.lower() == ".gif"
    mimetype = "image/gif" if is_gif else "image/jpeg"

    return send_file(
        BytesIO(thumbnail_data),
        mimetype=mimetype,
        as_attachment=False,
    )


@bp.route("/media/<path:filepath>")
def serve_media(filepath):
    """Serve media file."""
    media_root = Path(current_app.config["MEDIA_ROOT"])

    # Validate path
    safe = secure_path(media_root, filepath)
    if safe is None:
        return jsonify({"error": "Invalid path"}), 400

    if not safe.exists():
        return jsonify({"error": "File not found"}), 404

    if is_directory(safe):
        return jsonify({"error": "Cannot serve directory"}), 400

    mime_type = get_mime_type(safe)
    return send_file(safe, mimetype=mime_type, as_attachment=False)


# Import BytesIO at the end to avoid circular imports
from io import BytesIO
