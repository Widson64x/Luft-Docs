# run_prod.py
from waitress import serve
    # Se você REALMENTE tem App.py / pacote App, deixe esta linha:
from App import app

import os

HOST = os.getenv("LUFTDOCS_HOST", "127.0.0.1")  # aceita localhost + IP da rede
PORT = int(os.getenv("LUFTDOCS_PORT", "9100"))

if __name__ == "__main__":
    print(f"INFO: Iniciando servidor Waitress em http://{HOST}:{PORT}")
    serve(app, host=HOST, port=PORT, threads=100)
