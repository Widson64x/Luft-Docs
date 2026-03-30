from __future__ import annotations

import os
from typing import Any

import requests

from Config import (
    USER_API_CREDENTIAL_PARAMS as PARAMETROS_CREDENCIAIS_API_USUARIO,
    USER_API_TOKEN_PARAMS as PARAMETROS_TOKEN_API_USUARIO,
    USER_API_URL as URL_API_USUARIO_CONFIG,
)

URL_API_USUARIO = os.environ.get("USER_API_URL", URL_API_USUARIO_CONFIG)


def ObterUsuarioPorCredenciais(*argumentos: str) -> dict[str, Any] | None:
    """Consulta a API de usuarios usando os parametros de credenciais configurados."""
    try:
        parametros = dict(zip(PARAMETROS_CREDENCIAIS_API_USUARIO, argumentos))
        resposta = requests.get(f"{URL_API_USUARIO}/user", params=parametros, timeout=5)
        resposta.raise_for_status()
        return resposta.json()
    except (requests.RequestException, ValueError) as erro:
        print(f"Erro ao acessar API: {erro}")
        return None


def ObterUsuarioPorToken(valorToken: str) -> dict[str, Any] | None:
    """Consulta a API de usuarios usando o token informado."""
    try:
        parametros = {PARAMETROS_TOKEN_API_USUARIO[0]: valorToken}
        resposta = requests.get(f"{URL_API_USUARIO}/token", params=parametros, timeout=5)
        resposta.raise_for_status()
        return resposta.json()
    except (requests.RequestException, ValueError) as erro:
        print(f"Erro ao validar token: {erro}")
        return None