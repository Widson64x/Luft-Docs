import requests
import os
from config import USER_API_URL, USER_API_CREDENTIAL_PARAMS, USER_API_TOKEN_PARAMS

print(f"[INFO] Usando USER_API_URL: {USER_API_URL}")

USER_API_URL = os.environ.get("USER_API_URL", USER_API_URL)

def get_user_by_credentials(*args):
    try:
        params = dict(zip(USER_API_CREDENTIAL_PARAMS, args))
        resp = requests.get(
            f"{USER_API_URL}/user",
            params=params,
            timeout=5
        )
        resp.raise_for_status()
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
        return resp.json()
    except (requests.RequestException, ValueError) as e:
        print(f"Erro ao validar token: {str(e)}")
        return None