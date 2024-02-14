from flask import Flask
import os
import logging

from . import content
from . import auth


def make_app(secret_key: str, data_path: str, tmp_path: str) -> Flask:
    """Generates the Flask app instance

    Args:
        secret_key (str): a string used for Cookies and stuff
        data_path (str): the directory where the media data is to be stored
        tmp_path (str): the directory where cache (e.g., for thumbnails) is to be stored

    Returns:
        Flask: Flask app instance
    """
    app = Flask(__name__)

    app.secret_key = secret_key

    # Link logger to gunicorn in deployment
    if os.getenv('FLASK_DEBUG') != '1':
        gunicorn_logger = logging.getLogger('gunicorn.error')
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

    auth_bp = auth.make_bp(tmp_path)
    app.register_blueprint(auth_bp)

    content_bp = content.make_bp(data_path, tmp_path)
    app.register_blueprint(content_bp)

    return app
