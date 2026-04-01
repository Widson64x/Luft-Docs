from __future__ import annotations

import logging
from typing import Any

import requests

from Config import (
    USER_API_ACCESS_KEY as CHAVE_ACESSO_API_USUARIO_CONFIG,
    USER_API_ACCESS_KEY_HEADER as NOME_CABECALHO_CHAVE_API_USUARIO_CONFIG,
    USER_API_CREDENTIAL_PARAMS as PARAMETROS_CREDENCIAIS_API_USUARIO,
    USER_API_TOKEN_PARAMS as PARAMETROS_TOKEN_API_USUARIO,
    USER_API_URL as URL_API_USUARIO_CONFIG,
)

logger = logging.getLogger(__name__)

URL_API_USUARIO = URL_API_USUARIO_CONFIG
CHAVE_ACESSO_API_USUARIO = CHAVE_ACESSO_API_USUARIO_CONFIG
NOME_CABECALHO_CHAVE_API_USUARIO = NOME_CABECALHO_CHAVE_API_USUARIO_CONFIG


def ObterCabecalhosApiUsuario(
    cabecalhosAdicionais: dict[str, str] | None = None,
) -> dict[str, str]:
    """Monta os cabecalhos padrao exigidos pela API de usuarios."""
    cabecalhos = dict(cabecalhosAdicionais or {})

    if CHAVE_ACESSO_API_USUARIO:
        cabecalhos[NOME_CABECALHO_CHAVE_API_USUARIO] = CHAVE_ACESSO_API_USUARIO

    return cabecalhos


def ExecutarRequisicaoApiUsuario(
    metodo: str,
    rota: str,
    **kwargs: Any,
) -> requests.Response:
    """Executa chamadas HTTP para a API de usuarios com os cabecalhos padrao."""
    cabecalhosInformados = kwargs.pop("headers", None)
    rotaNormalizada = rota if rota.startswith("/") else f"/{rota}"

    return requests.request(
        method=metodo,
        url=f"{URL_API_USUARIO}{rotaNormalizada}",
        headers=ObterCabecalhosApiUsuario(cabecalhosInformados),
        **kwargs,
    )


def ObterUsuarioPorCredenciais(*argumentos: str) -> dict[str, Any] | None:
    """Consulta a API de usuarios usando os parametros de credenciais configurados."""
    try:
        parametros = dict(zip(PARAMETROS_CREDENCIAIS_API_USUARIO, argumentos))
        resposta = ExecutarRequisicaoApiUsuario(
            "get",
            "/user",
            params=parametros,
            timeout=5,
        )
        resposta.raise_for_status()
        return resposta.json()
    except (requests.RequestException, ValueError) as erro:
        logger.error("Erro ao acessar API de usuarios por credenciais: %s", erro)
        return None


def ObterUsuarioPorToken(valorToken: str) -> dict[str, Any] | None:
    """Consulta a API de usuarios usando o token informado."""
    try:
        parametros = {PARAMETROS_TOKEN_API_USUARIO[0]: valorToken}
        resposta = ExecutarRequisicaoApiUsuario(
            "get",
            "/token",
            params=parametros,
            timeout=5,
        )
        resposta.raise_for_status()
        return resposta.json()
    except (requests.RequestException, ValueError) as erro:
        logger.error("Erro ao validar token do usuario na API: %s", erro)
        return None