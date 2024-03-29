import os
from flask import Blueprint, redirect, url_for, abort, request, render_template, g

from .item import Item
from .. import auth

from ..database import Database


def make_bp(data_path: str, tmp_path: str) -> Blueprint:

    bp = Blueprint('content', __name__)

    Item.DATA_PATH = data_path
    Item.THUMB_PATH = os.path.join(tmp_path, 'thumb')

    @bp.route("/", defaults={'content_path': ""})
    @bp.route("/<path:content_path>")
    @auth.check_access
    def get(content_path: str) -> str:
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

        # ... remove thumbnails to reload them
        if request.args.get('reload_thumbs') is not None:
            item.delete_thumb()
            return redirect(url_for(
                'content.get',
                content_path=item.content_path
            ))

        # ... list favorites
        if request.args.get('favorites') is not None:
            return render_template(
                'content/item-list.html.jinja2',
                item=item,
                item_list=Item.get_favorites_list()
            )

        # ... if searching
        if request.args.get('search') is not None:
            return render_template(
                'content/item-search.html.jinja2',
                item_list=Item.get_search_results(),
                search_keyword=Item.get_searched_keyword(),
                search_duration=Item.get_search_duration(),
                item=item
            )

        # ... raw file
        if request.args.get('raw') is not None:
            return item.raw

        # ... thumb file
        if request.args.get('thumb') is not None:
            return item.thumb

        # ... poster file
        if request.args.get('poster') is not None:
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

    @bp.route("/:/", defaults={'content_path': ""}, methods=['POST'])
    @bp.route("/:/<path:content_path>", methods=['POST'])
    @auth.check_access
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
            url_for('content.get', content_path=content_path)
        )

        if request.args.get('toggle_favorite') is not None:
            item = Item(request.args.get('toggle_favorite'))
            is_favorite = request.form.get('toggle-favorite') == 'on'
            item.set_favorite(is_favorite)
            return "OK"

        elif request.args.get('search') is not None:
            search_keyword = request.form.get('keyword', default='')
            if search_keyword == '':
                return default_redirect

            Item.search(search_keyword.lower())

            return redirect(
                url_for('content.get', content_path=content_path, search=True)
            )

        elif request.args.get('generate_all_thumbs') is not None:
            Item.generate_all_thumbs()
            return "OK"

        return default_redirect

    return bp
