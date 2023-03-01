import os
from media_vault import make_app

secret_key = os.environ.get("FLASK_SECRET", None)
if secret_key is None:
    raise Exception("Specify a valid `FLASK_SECRET`")

data_path = os.environ.get("DATA_PATH", "/data")

log_file = os.environ.get("LOG_FILE", None)

app = make_app(secret_key, data_path)