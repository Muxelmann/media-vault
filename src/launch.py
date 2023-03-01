import os
import logging
from media_vault import make_app

secret_key = os.environ.get("FLASK_SECRET", None)
if secret_key is None:
    raise Exception("Specify a valid `FLASK_SECRET`")

data_path = os.environ.get("DATA_PATH", "/data")

log_file = os.environ.get("LOG_FILE", None)
if log_file is not None:
    logging.basicConfig(filename=log_file, encoding="utf-8", level=logging.DEBUG, format="[%(asctime)s] %(levelname)s:%(message)s")
else:
    logging.basicConfig(encoding="utf-8", level=logging.DEBUG, format="[%(asctime)s] %(levelname)s:%(message)s")


app = make_app(secret_key, data_path)