from flask import Flask, render_template, url_for, abort, send_file, request, g, redirect
from werkzeug.utils import secure_filename
import os
import shutil

from .content import Item


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

    Item.DATA_PATH = data_path
    Item.THUMB_PATH = os.path.join(tmp_path, 'thumb')
    Item.FAV_LIST_PATH = os.path.join(tmp_path, 'favorites.json')

    @app.route("/", defaults={'content_path': ""})
    @app.route("/<path:content_path>")
    def get_content(content_path: str) -> str:
        """A route returning content at the content path.

        If the content path is a directory, a list of folders is returned.
        If the content path is a file (like an image or video), a page showing its content is returned.

        When passing a GET argument of:
        - `raw` the raw file is returned.
        - `thumb` a thumbnail is returned.

        Args:
            content_path (str): The path to the content returned by this route.

        Returns:
            str: Response page of a list of folders or the content of an item
        """

        # Remove trailing path separators
        while len(content_path) > 0 and content_path[-1] == os.path.sep:
            content_path = content_path[:-1]

        item = Item(content_path)

        # If nothing exists for the item, abort
        if not item.exists:
            return abort(404)

        # Populate the breadcrumbs based on the content path for navigation
        g.breadcrumbs = content_path.split('/')
        if g.breadcrumbs[0] == '':
            del g.breadcrumbs

        # Test what is requested based on arguments of GET request...

        # ... list favorites
        if request.args.get('favorites', default=None) is not None:
            return render_template(
                'content/item-list.html.jinja2',
                item=item,
                item_list=Item.get_favorites_list()
            )

        # ... raw file
        if request.args.get('raw', default=None) is not None:
            return item.raw

        # ... thumb file
        if request.args.get('thumb', default=None) is not None:
            return item.thumb

        # ... poster file
        if request.args.get('poster', default=None) is not None:
            return item.poster

        if content_path != '':
            item = Item(content_path, find_neighbors=True)

        # ... list of dir content
        if item.is_dir:
            return render_template(
                'content/item-list.html.jinja2',
                item=item,
                item_list=item.content_list
            )

        # ... page of content
        return render_template(
            'content/item-single.html.jinja2',
            item=item
        )

    @app.route("/:/", defaults={'content_path': ""}, methods=['POST'])
    @app.route("/:/<path:content_path>", methods=['POST'])
    def manage(content_path: str) -> str:
        """A POST-only route to upload files, create folders and delete items at the content path.

        When passing a POST argument of:

        - `upload` one or more passed files can be uploaded to the content path.
        - `new_folder` a folder of `folder-name` (form value) is added.
        - `delete` an folder or file of `item-name` (form value) is deleted.

        Args:
            content_path (str): The path to the content managed by this route.

        Returns:
            str: Redirection to new folder, `OK` acknowledgemet or default redirection
        """
        default_redirect = redirect(
            url_for('.get_content', content_path=content_path))

        if request.args.get('toggle_favorite') is not None:
            item = Item(request.args.get('toggle_favorite'))
            is_favorite = request.form.get('toggle-favorite') == 'on'
            item.set_favorite(is_favorite)

        return default_redirect
    return app
