import requests
import os
from Config import USER_API_URL, USER_API_CREDENTIAL_PARAMS, USER_API_TOKEN_PARAMS

print(f"[INFO] Usando USER_API_URL: {USER_API_URL}")

USER_API_URL = os.environ.get("USER_API_URL", USER_API_URL)

"""

Toda vez que eu chego aqui eu me perco, E pior fui eu que fiz...

Mas e aqui que eu posso mudar o parâmetro de acesso do usuário.
"""

def get_user_by_credentials(*args):
    try:
        params = dict(zip(USER_API_CREDENTIAL_PARAMS, args))
        resp = requests.get(
            f"{USER_API_URL}/user",
            params=params,
            timeout=5
        )
        resp.raise_for_status()
        # A API deve retornar tanto os dados do usuário quanto do grupo (com permissões)
        # Eu espero né...
        return resp.json()  
    except (requests.RequestException, ValueError) as e:
        print(f"Erro ao acessar API: {str(e)}")
        return None

def get_user_by_token(token_value):
    try:
        params = {USER_API_TOKEN_PARAMS[0]: token_value}
        resp = requests.get(
            f"{USER_API_URL}/token",
            params=params,
            timeout=5
        )
        resp.raise_for_status()
        # A API deve retornar os dados completos (usuário, grupo e permissões)
        # Se já funcionou com 'Credenciais' tem que fucnionar aqui também. Eu esper...
        return resp.json()  
    except (requests.RequestException, ValueError) as e:
        print(f"Erro ao validar token: {str(e)}")
        return None
