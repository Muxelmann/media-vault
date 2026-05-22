import os
from pathlib import Path
from urllib.parse import unquote


def secure_path(base_dir, user_path):
    """
    Validate and normalize a user-provided path to prevent directory traversal attacks.

    Args:
        base_dir: The root directory (e.g., media root)
        user_path: User-provided path (may contain /)

    Returns:
        Absolute Path object if valid, None if invalid/outside base_dir
    """
    base_dir = Path(base_dir).resolve()

    # Decode URL-encoded path
    if isinstance(user_path, str):
        user_path = unquote(user_path).strip()

    # Handle empty or relative traversal attempts
    if not user_path or user_path in (".", ".."):
        return base_dir

    # Build the full path
    try:
        full_path = (base_dir / user_path).resolve()
    except (ValueError, OSError):
        return None

    # Ensure the resolved path is within base_dir
    try:
        full_path.relative_to(base_dir)
        return full_path
    except ValueError:
        # Path is outside base_dir
        return None
