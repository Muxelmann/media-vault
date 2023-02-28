# FIXME: Store tree in memory to speed up loading times

# TODO: Oder content alphabetically

import os

from flask import Flask, render_template, abort, redirect, url_for, send_file

def get_content_type(root_content_path: str, content_path: str = "") -> str:
    if os.path.isdir(os.path.join(root_content_path, content_path )):
        return "dir"
    if os.path.splitext(content_path)[1].lower() in [".png", ".jpg", ".gif"]:
        return "image"
    if os.path.splitext(content_path)[1].lower() in [".mp4", ".m4v"]:
        return "video"
    return "unknown"

def get_breadcrumbs(content_path: str) -> list[dict]:
    
    breadcrumbs = list[dict]()
    breadcrumbs.append({"href": None, "name": "home"})

    path_elements = content_path.split("/")
    for i in range(len(path_elements)):
        sub_path = "/".join(path_elements[:i+1])
        breadcrumbs.append({"href": sub_path, "name": path_elements[i]})
    
    return breadcrumbs

def get_content_tree(root_content_path: str, content_path: str = "", is_root: bool = True, is_selected: bool = True, href: str = "") -> dict:
    content_tree = {
        "name": "home" if is_root else os.path.split(root_content_path)[-1],
        "selected": is_selected,
        "href": href,
        "sub_content": []
    }

    for sub_content_name in [c for c in os.listdir(root_content_path) if c[0] != "."]:
        root_sub_content_path = os.path.join(root_content_path, sub_content_name)
        if os.path.isdir(root_sub_content_path):

            sub_content_path = ""
            is_selected = False
            if content_path != "" and sub_content_name == content_path.split("/")[0]:
                sub_content_path = "/".join(content_path.split("/")[1:])
                is_selected = True

            sub_href = sub_content_name if href == "" else href + "/" + sub_content_name

            content_tree["sub_content"].append(get_content_tree(root_sub_content_path, sub_content_path, False, is_selected, sub_href))

    return content_tree

def get_thumbs(root_content_path: str, content_path: str = None) -> list[dict]:

    thumbs = list[dict]()

    full_content_path = os.path.join(root_content_path, content_path)

    for content_name in [c for c in os.listdir(full_content_path) if c[0] != "."]:
        
        content_type = get_content_type(full_content_path, content_name)
        href = None
        data_src = None
        match content_type:
            case "dir":
                href = url_for("content", content_path=content_name if content_path == "" else content_path + "/" + content_name)
            case "image":
                href = url_for("content", content_path=content_name if content_path == "" else content_path + "/" + content_name)
                data_src = url_for("get_content", content_path=content_name if content_path == "" else content_path + "/" + content_name)
            case "video":
                href = url_for("content", content_path=content_name if content_path == "" else content_path + "/" + content_name)
            case _:
                href = "#"

        thumbs.append({
            "name": content_name,
            "content_type": content_type,
            "href": href,
            "data_src": data_src
        })

    return thumbs

def get_neighboring(root_content_path: str, content_path: str) -> dict:
    content_name = content_path.split("/")[-1]
    parent_path = "/".join(content_path.split("/")[:-1])
    full_path = os.path.join(root_content_path, parent_path)

    contents = [c for c in os.listdir(full_path) if c[0] != "."]
    content_index = contents.index(content_name)

    content_url_previous = None
    content_index_previous = content_index - 1 if content_index > 0 else None
    if content_index_previous is not None:
        content_name_previous = contents[content_index_previous]
        content_url_previous = url_for("content", content_path=(content_name_previous if parent_path == "" else parent_path + "/" + content_name_previous))

    content_url_next = None
    content_index_next = content_index + 1 if content_index < len(contents) - 1 else None
    if content_index_next is not None:
        content_name_next = contents[content_index_next]
        content_url_next = url_for("content", content_path=(content_name_next if parent_path == "" else parent_path + "/" + content_name_next))

    return {
        "previous": content_url_previous,
        "next": content_url_next
    }

def make_app(secret_key: str, instance_path: str) -> Flask:
    app = Flask(__name__)

    app.secret_key = secret_key
    app.instance_path = instance_path

    @app.route("/")
    def index():
        return redirect(url_for("base_content"))

    @app.route("/c/")
    def base_content():
        return return_content()

    @app.route("/c/<path:content_path>")
    def content(content_path: str):
        return return_content(content_path)
    
    def return_content(content_path: str = ""):
        full_content_path = os.path.join(app.instance_path, content_path)
        if not os.path.exists(full_content_path):
            return abort(404)

        breadcrumbs = get_breadcrumbs(content_path)

        if os.path.isdir(full_content_path):
            content_tree = get_content_tree(app.instance_path, content_path)
            thumbs = get_thumbs(app.instance_path, content_path)

            return render_template(
                "content-tree.html.jinja2",
                breadcrumbs=breadcrumbs,
                content_tree=content_tree,
                thumbs=thumbs
                )

        else:

            neighbors = get_neighboring(app.instance_path, content_path)
            content = {
                "src": url_for("get_content", content_path=content_path),
                "type": get_content_type(app.instance_path, content_path)
            }

            return render_template(
                "content-file.html.jinja2",
                breadcrumbs = breadcrumbs,
                neighbors = neighbors,
                content=content
                )


    @app.route("/g/<path:content_path>")
    def get_content(content_path):
        full_path = os.path.join(app.instance_path, content_path)
        return send_file(full_path)

    return app