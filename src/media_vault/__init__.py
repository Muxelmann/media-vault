from flask import Flask, render_template, url_for, abort, send_file, request, g
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
    if suffix.lower() in ['.mp4', '.m4v']:
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
    
    if item['suffix'] == 'mp4':
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
        while len(content_path) > 0 and content_path[-1] == os.path.sep:
            content_path = content_path[:-1]

        full_path = os.path.join(data_path, content_path)
        thumb_path = os.path.join(tmp_path, content_path)

        if not os.path.exists(full_path):
            return abort(404)

        g.breadcrumbs = content_path.split('/')

        if request.args.get('raw', default=None) is not None:
            return send_raw(full_path)

        if request.args.get('thumb', default=None) is not None:
            return send_thumb(full_path, thumb_path)

        if os.path.isdir(full_path):
            return send_list(full_path, content_path, data_path)
        
        return send_item(full_path, content_path)

    return app