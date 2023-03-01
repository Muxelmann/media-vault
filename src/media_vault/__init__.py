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

class ContentElement:

    root_content_path = None
    href_dict = dict[str, "ContentElement"]()

    def __init__(self, name: str, sub_path: str = "", parent: "ContentElement" = None) -> None:
        self.name = name
        self.sub_path = sub_path
        self.parent = parent
        self.children = list["ContentElement"]()
        self.is_open = parent is None

        self._parse_tree()
        self.href_dict[self.href] = self

    @property
    def content_path(self) -> str:
        if self.parent is None:
            return os.path.join(self.root_content_path, self.sub_path)
        return os.path.join(self.parent.content_path, self.sub_path)

    @property
    def href(self) -> str:
        if self.parent is None:
            return self.sub_path
        href = self.parent.href + "/" + self.sub_path
        return href[1:] if href[0] == "/" else href

    def _parse_tree(self) -> None:
        content = [c for c in os.listdir(self.content_path) if c[0] != "."]
        content.sort()
        for sub_path in content:
            if os.path.isdir(os.path.join(self.content_path, sub_path)):
                self.children.append(ContentElement(sub_path, sub_path, self))

    def _close_children(self) -> None:
        for child in self.children:
            child.is_open = False
            child._close_children()

    def _open(self) -> None:
        self.is_open = True
        if self.parent is not None:
            self.parent._open()
        
    def open_path(self, path: str) -> None:
        self._close_children()

        if path not in self.href_dict.keys():
            return
        
        self.href_dict[path]._open()

def get_thumbs(root_content_path: str, content_path: str = None) -> list[dict]:

    thumbs = list[dict]()

    full_content_path = os.path.join(root_content_path, content_path)

    contents = [c for c in os.listdir(full_content_path) if c[0] != "."]
    contents.sort()
    for content_name in contents:
        
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
    contents.sort()
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

    ContentElement.root_content_path = instance_path
    content_tree = ContentElement("home")

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
            content_tree.open_path(content_path)
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