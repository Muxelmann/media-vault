"""Video streaming support with HTTP Range requests."""
from pathlib import Path
from flask import Response, make_response, request, send_file


def parse_range_header(range_header: str, file_size: int) -> tuple[int, int] | None:
    """
    Parse Range header and return (start, end) tuple.

    Handles:
    - bytes=0-     (from start to end)
    - bytes=-500   (last 500 bytes)
    - bytes=100-   (from byte 100 to end)
    - bytes=0-499  (bytes 0 to 499)

    Args:
        range_header: The Range header value from the request
        file_size: Total size of the file in bytes

    Returns:
        Tuple of (start, end) byte positions, or None if invalid
    """
    if not range_header or not range_header.startswith('bytes='):
        return None

    range_spec = range_header[6:]  # Remove 'bytes='

    if '-' in range_spec:
        parts = range_spec.split('-')

        # bytes=0- (from start to end)
        if parts[0] and not parts[1]:
            start = int(parts[0])
            end = file_size - 1
        # bytes=-500 (last 500 bytes)
        elif not parts[0] and parts[1]:
            end = file_size - 1
            start = max(0, file_size - int(parts[1]))
        # bytes=0-499 (specific range)
        else:
            start = int(parts[0])
            end = min(int(parts[1]), file_size - 1)

        # Validate range
        if start > end or start < 0:
            return None
        return (start, end)

    return None


def stream_file_with_ranges(filepath: Path, mimetype: str, cache_max_age: int = 31536000) -> Response:
    """
    Serve a file with HTTP Range request support.

    Args:
        filepath: Path to the file to serve
        mimetype: MIME type of the file
        cache_max_age: Cache control max-age in seconds (default: 1 year)

    Returns:
        Flask response with appropriate headers for streaming

    The function handles:
    - 200 OK with full file if no Range header
    - 206 Partial Content with requested range if Range header present
    - 416 Range Not Satisfiable if range is invalid
    """
    from io import BytesIO
    from flask import make_response

    file_size = filepath.stat().st_size

    # Check for Range header
    range_header = request.headers.get('Range')

    if range_header:
        range_tuple = parse_range_header(range_header, file_size)

        if range_tuple is None:
            # Invalid range - return 416
            response = make_response("Range Not Satisfiable", 416)
            response.headers['Content-Range'] = f'bytes */{file_size}'
            return response

        start, end = range_tuple
        content_length = end - start + 1

        # Read only the requested range
        with open(filepath, 'rb') as f:
            f.seek(start)
            data = f.read(content_length)

        response = make_response(data, 206)
        response.headers['Content-Type'] = mimetype
        response.headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
        response.headers['Content-Length'] = str(content_length)
        response.headers['Accept-Ranges'] = 'bytes'
        response.headers['Cache-Control'] = f'public, max-age={cache_max_age}'
        return response

    # No range request - serve full file
    response = make_response(send_file(filepath, mimetype=mimetype), 200)
    response.headers['Accept-Ranges'] = 'bytes'
    response.headers['Content-Length'] = str(file_size)
    response.headers['Cache-Control'] = f'public, max-age={cache_max_age}'
    return response
