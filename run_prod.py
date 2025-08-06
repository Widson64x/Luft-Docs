from waitress import serve
from App import app # Garanta que 'app' é a instância do Flask no seu arquivo app.py

# run_prod.py
# Este script inicia o servidor de produção usando Waitress
local = False

def localhost():
    if local:
        host = 'localhost'
    else:
        host = '172.16.200.80'
    return host

if __name__ == "__main__":
    # Define o host e a porta para o servidor de produção
    host = localhost()
    port = 8001

    print(f"INFO: Iniciando servidor Waitress em http://{host}:{port}")
    
    # Inicia a aplicação 'app' usando o servidor Waitress
    serve(app, host=host, port=port)