import os
from waitress import serve
from App import app
import Config as cfg

HOST = os.getenv("LUFTDOCS_HOST", "127.0.0.1")
PORT = int(os.getenv("LUFTDOCS_PORT", "9100"))

if __name__ == "__main__":
    print(f"INFO: Iniciando servidor Waitress em http://{HOST}:{PORT}{cfg.BASE_PREFIX}")
    serve(app, host=HOST, port=PORT, threads=100, url_prefix=cfg.BASE_PREFIX)