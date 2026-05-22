import os
from pathlib import Path
from flask import Flask


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True)

    # Ensure instance directory exists
    instance_path = Path(app.instance_path)
    instance_path.mkdir(exist_ok=True)

    # Ensure media directory exists
    media_path = instance_path / "media"
    media_path.mkdir(exist_ok=True)

    # Ensure thumbnail cache directory exists
    thumbnail_cache_path = instance_path / "thumbnails"
    thumbnail_cache_path.mkdir(exist_ok=True)

    # Configuration
    app.config["MEDIA_ROOT"] = str(media_path)
    app.config["THUMBNAIL_CACHE_ROOT"] = str(thumbnail_cache_path)
    app.config["MAX_CONTENT_LENGTH"] = 512 * 1024 * 1024  # 512MB max file size

    if config:
        app.config.update(config)

    # Initialize thumbnail cache
    from app.media_handler import set_thumbnail_cache_root
    set_thumbnail_cache_root(app.config["THUMBNAIL_CACHE_ROOT"])

    # Register blueprints
    from app.routes import bp
    app.register_blueprint(bp)

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Not found"}, 404

    @app.errorhandler(400)
    def bad_request(error):
        return {"error": "Bad request"}, 400

    @app.errorhandler(500)
    def internal_error(error):
        return {"error": "Internal server error"}, 500

    return app
