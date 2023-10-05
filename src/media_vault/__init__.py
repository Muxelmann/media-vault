from flask import Flask, render_template, url_for, abort, send_file, request, g, redirect
from werkzeug.utils import secure_filename
import os

from . import utils


def send_thumb(full_path: str, thumb_path: str) -> str:
    """Sends a thumb version of the actual media file.

    If the thumb does not exist, it will be generated upon first call.
    If media file is a dir (i.e., not a file as such), the function returns a 404 error response.
    The thumb of a video file is stored as a PNG, despite the file suffix in the URL indicating e.g., MP4.

    Args:
        full_path (str): full path e.g. starting with `/user/...` to the actual media file
        thumb_path (str): full path e.g. starting with `/tmp/...` to the thumb media file

    Returns:
        str: Flask response string of `send_file()`
    """

    if not os.path.isfile(full_path):
        return abort(404)

    # Make sure only images are sent as thumb
    thumb_path_without_suffix, suffix = os.path.splitext(thumb_path)
    if suffix.lower() in utils.VIDEO_SUFFIX:
        thumb_path = thumb_path_without_suffix + '.png'

    if not os.path.exists(thumb_path):
        utils.make_thumb(full_path, thumb_path)

    return send_file(thumb_path)


def send_raw(full_path: str) -> str:
    """Sends the actual media file.

    If media file is a dir (i.e., not a file as such), the function returns a 404 error response.

    Args:
        full_path (str): full path e.g. starting with `/user/...` to the actual media file

    Returns:
        str: Flask response string of `send_file()`
    """

    if not os.path.isfile(full_path):
        return abort(404)
    return send_file(full_path)


def send_list(full_path: str, content_path: str, data_path: str) -> str:
    """Sends a page corresponding list of files at the current directory.

    A `content_list` variable is made available to the template, wherein each element
    comprises parameters like `name`, `href` (url) and `thumb` (url), necessary for
    displaying the list grid.

    Args:
        full_path (str): full path e.g. starting with `/user/...` to the actual media file
        content_path (str): path to media file according to URL
        data_path (str): full path e.g. starting with `/user/...` to the content directory

    Returns:
        str: Flask response string of `render_template()` with `content_path`
    """

    content_list = []
    for file in utils.get_file_list(full_path):

        content_list.append({
            'name': os.path.splitext(file)[0],
            'href': url_for('.get_content', content_path=os.path.join(content_path, file)),
            'thumb': url_for('.get_content', content_path=os.path.join(content_path, file), thumb=True)
        })

        if os.path.isdir(os.path.join(data_path, content_path, file)):
            content_list[-1]['thumb'] = None

    return render_template('content/list.html.jinja2', content_list=content_list)


def send_item(full_path: str, content_path: str) -> str:
    """Sends a page for displaying the media file.

    An `item` variable is made available to the template.
    It contains arguments like `suffix`, `type`, `href` (url), `neighbors` ([url | None, url | None]).

    Args:
        full_path (str): full path e.g. starting with `/user/...` to the actual media file
        content_path (str): path to media file according to URL

    Returns:
        str: _description_
    """
    item = {
        'suffix': os.path.splitext(content_path)[1].replace('.', '')
    }
    if item['suffix'] == 'mov':
        item['suffix'] = 'mp4'

    if os.path.splitext(content_path)[1] in utils.VIDEO_SUFFIX:
        item['type'] = 'video'
    else:
        item['type'] = 'image'

    item['href'] = url_for('.get_content', content_path=content_path, raw=True)

    item['neighbors'] = utils.get_neighbors(full_path, content_path)
    for idx, cp in enumerate(item['neighbors']):
        if cp is None:
            continue
        item['neighbors'][idx] = url_for('.get_content', content_path=cp)

    return render_template('content/item.html.jinja2', item=item)


def make_app(secret_key: str, data_path: str, tmp_path: str) -> Flask:
    app = Flask(__name__)

    app.secret_key = secret_key

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

        while len(content_path) > 0 and content_path[-1] == os.path.sep:
            content_path = content_path[:-1]

        full_path = os.path.join(data_path, content_path)
        thumb_path = os.path.join(tmp_path, content_path)

        if not os.path.exists(full_path):
            return abort(404)

        g.breadcrumbs = content_path.split('/')
        if g.breadcrumbs[0] == '':
            del g.breadcrumbs

        if request.args.get('raw', default=None) is not None:
            return send_raw(full_path)

        if request.args.get('thumb', default=None) is not None:
            return send_thumb(full_path, thumb_path)

        if os.path.isdir(full_path):
            return send_list(full_path, content_path, data_path)

        return send_item(full_path, content_path)

    @app.route("/:/", defaults={'content_path': ""}, methods=['POST'])
    @app.route("/:/<path:content_path>", methods=['POST'])
    def manage(content_path: str) -> str:
        """A POST-only route to upload files, create folders and delete items at the content path.

        When passing a GET argument of:

        - `upload` one or more passed files can be uploaded to the content path.
        - `new_folder` a folder of `folder-name` (form value) is added.
        - `delete` an folder or file of `item-name` (form value) is deleted.

        Args:
            content_path (str): The path to the content managed by this route.

        Returns:
            str: Redirection to new folder, `OK` acknowledgemet or 500 error
        """

        if request.args.get('upload', None) is not None:
            file = request.files['file']
            full_path = os.path.join(
                data_path, content_path, secure_filename(file.filename))
            file.save(full_path)
            return "OK"

        elif request.args.get('new_folder', None) is not None:
            folder_name = request.form.get('folder-name')
            if folder_name is None:
                return abort(500)

            folder_name = secure_filename(folder_name)

            full_path = os.path.join(data_path, content_path, folder_name)

            if os.path.exists(full_path):
                return abort(500)

            os.makedirs(full_path)
            return redirect(url_for('.get_content', content_path=os.path.join(content_path, folder_name)))

        return redirect(url_for('.get_content', content_path=content_path))
    return app
