import os

from media_vault import make_app

secret_key = os.environ.get("FLASK_SECRET", None)
if secret_key is None:
    raise Exception("Specify a valid `FLASK_SECRET`")

instance_path = os.environ.get("FLASK_DATA", "/data")

app = make_app(secret_key, instance_path)