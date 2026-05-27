import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from waitress import serve
from App import app
import Config as cfg

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "9000"))

if __name__ == "__main__":
    print(f"INFO: Iniciando servidor Waitress em http://{HOST}:{PORT}{cfg.BASE_PREFIX}")
    serve(app, host=HOST, port=PORT, threads=100, url_prefix=cfg.BASE_PREFIX)