"""Script utilitario para testes manuais do endpoint de usuario."""

import hashlib
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv


CAMINHO_DOTENV = Path(__file__).resolve().parents[2] / ".env"

load_dotenv(dotenv_path=CAMINHO_DOTENV, override=False)


urlApi = os.getenv("URL_API", "http://127.0.0.1:9006/luft-api/api/user")
nomeCabecalhoChaveApi = os.getenv("API_ACCESS_KEY_HEADER", "X-API-Key")
chaveAcessoApi = (os.getenv("API_ACCESS_KEY") or "").strip()


def testarApiComUsuario(loginUsuario: str) -> None:
    """Gera o hash MD5 do usuario, chama a API e imprime o resultado.

    Args:
        loginUsuario: Login do usuario que deve ser consultado na API.

    Returns:
        None: Resultado impresso diretamente no console.
    """
    print(f"--- Iniciando teste para o usuario: '{loginUsuario}' ---")
    hashLogin = hashlib.md5(loginUsuario.encode("utf-8")).hexdigest()
    print(f"Hash MD5 gerado: {hashLogin}")

    if not chaveAcessoApi:
        raise RuntimeError("Defina API_ACCESS_KEY no .env antes de executar o teste manual.")

    parametrosRequisicao = {"login_hash": hashLogin}
    cabecalhosRequisicao = {nomeCabecalhoChaveApi: chaveAcessoApi}

    try:
        print(f"Enviando requisicao GET para: {urlApi}")
        resposta = requests.get(
            urlApi,
            params=parametrosRequisicao,
            headers=cabecalhosRequisicao,
            timeout=30,
        )
        resposta.raise_for_status()
        print(f"Resposta recebida com sucesso. Status: {resposta.status_code}")
        print(json.dumps(resposta.json(), indent=4, ensure_ascii=False))
    except requests.exceptions.HTTPError as erroHttp:
        print(f"Erro HTTP: {erroHttp}")
        print(f"Resposta do servidor: {erroHttp.response.text}")
    except requests.exceptions.RequestException as erroRequisicao:
        print(f"Erro de conexao: {erroRequisicao}")
    finally:
        print("-" * 50 + "\n")


def executarTestesPadrao() -> None:
    """Executa dois cenarios basicos de validacao manual da API.

    Returns:
        None: Testes executados sequencialmente no terminal local.
    """
    testarApiComUsuario("teste.ti")
    testarApiComUsuario("usuario.inexistente")


if __name__ == "__main__":
    executarTestesPadrao()