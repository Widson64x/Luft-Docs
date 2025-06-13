from fastapi import FastAPI, HTTPException, Query

'''
# --- API FAKE PARA TESTE LOCAL COM FASTAPI --- #

# Instale as dependências:
pip install fastapi uvicorn

# Crie um arquivo chamado `api.py` e cole o seguinte código:
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

# Execute o servidor:
python -m uvicorn api:app --reload --port 8000

# Acesse a documentação interativa em: http://localhost:8000/docs

# API de autenticação de usuários
# Esta API simula um serviço de autenticação de usuários.
# Exemplo de chamada:
URL: http://localhost:8000/api/user?user_name=admin&user_id=1

Para executar: uvicorn main:app --reload --port 8000


# Acesso da API na Render #
https://api-wikidocs.onrender.com/api/user?user_name=widson.araujo&user_id=12345 

'''

app = FastAPI()

USERS = [
    {"user_name": "widson.araujo", "user_id": "12345", "permission": "MASTER", "email": "admin@exemplo.com", "token": "tok455"},
    {"user_name": "luft.teste", "user_id": "12345", "permission": "ADM", "email": "joao@exemplo.com", "token": "tok456"},
    {"user_name": "luft", "user_id": "12345", "permission": "USER", "email": "joao@exemplo.com", "token": "tok457"},
]

@app.get("/api/user")
def api_user(user_name: str = Query(...), user_id: str = Query(...)):
    for u in USERS:
        if u["user_name"] == user_name and u["user_id"] == user_id:
            return u
    raise HTTPException(status_code=404, detail="Usuário não encontrado")

@app.get("/api/token")
def api_token(token: str = Query(...)):
    for u in USERS:
        if u["token"] == token:
            return u
    raise HTTPException(status_code=404, detail="Token inválido")