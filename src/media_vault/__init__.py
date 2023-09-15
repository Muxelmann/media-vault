from flask import Flask, render_template, redirect, url_for, abort, send_file, request, g
import os
from PIL import Image, ImageSequence, ImageFile
import subprocess

ImageFile.LOAD_TRUNCATED_IMAGES = True

def make_thumb(full_path: str, thumb_path:str) -> None:

    # Make folder structure to save thumb
    base_path = os.path.split(thumb_path)[0]
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    
    # Generate thumb
    if os.path.splitext(full_path)[1].lower() in ['.mp4', '.m4v']:
        subprocess.call([
            'ffmpeg',
            '-i', full_path,
            '-ss', '00:00:00.000',
            '-vframes', '1',
            # '-y',
            thumb_path
        ])
    else:
        with Image.open(full_path) as img:

            aspect_ratio = img.width / img.height
            if aspect_ratio > 1:
                new_height = 200
                new_width = int(200 * aspect_ratio)
            else:
                new_height = int(200 / aspect_ratio)
                new_width = 200
                
            if hasattr(img, "is_animated") and img.is_animated:
                frames = ImageSequence.Iterator(img)
                frames = [f.resize((new_width, new_height)) for f in frames]
                out_img = frames[0]
                out_img.info = img.info
                out_img.save(thumb_path, save_all=True, append_images=frames[1:], optimize=True)

            else:
                out_img = img.resize((new_width, new_height))
                out_img.save(thumb_path)
        
def send_thumb(full_path: str, thumb_path: str) -> str:
    if not os.path.isfile(full_path):
        return abort(404)
    
    # Make sure only images are sent as thumb
    thumb_path_without_suffix, suffix = os.path.splitext(thumb_path)
    if suffix.lower() in ['.mp4', '.m4v']:
        thumb_path = thumb_path_without_suffix + '.png'

    if not os.path.exists(thumb_path):
        make_thumb(full_path, thumb_path)

    return send_file(thumb_path)

def send_raw(full_path: str) -> str:
    if not os.path.isfile(full_path):
        return abort(404)
    return send_file(full_path)

def send_list(full_path: str, content_path: str, data_path: str) -> str:
    content_list = []
    for file in os.listdir(full_path):
        if file[0] == '.':
            continue
    
        content_list.append({
            'name': os.path.splitext(file)[0],
            'href': url_for('get_content', content_path=os.path.join(content_path, file)),
            'thumb': url_for('get_content', content_path=os.path.join(content_path, file), thumb=True)
        })

        if os.path.isdir(os.path.join(data_path, content_path, file)):
            content_list[-1]['thumb'] = None
    
    return render_template('content/list.html.jinja2', content_list=content_list)

def send_item(content_path: str) -> str:
    item = {
        'suffix': os.path.splitext(content_path)[1].replace('.', '')
    }
    
    if item['suffix'] == 'mp4':
        item['type'] = 'video'
    else:
        item['type'] = 'image'
    
    item['href'] = url_for('get_content', content_path=content_path, raw=True)

    return render_template('content/item.html.jinja2', item=item)

def make_app(secret_key: str, data_path: str, tmp_path: str) -> Flask:
    app = Flask(__name__)

    app.secret_key = secret_key

    @app.route("/", defaults={'content_path': ""})
    @app.route("/<path:content_path>")
    def get_content(content_path: str) -> str:
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
        
        return send_item(content_path)

    return app