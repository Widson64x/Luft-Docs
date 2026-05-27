"""Inicializador do servidor Uvicorn para a API LuftDocs."""

import os
from pathlib import Path

import uvicorn
from dotenv import load_dotenv


CAMINHO_DOTENV = Path(__file__).resolve().parents[1] / ".env"

load_dotenv(dotenv_path=CAMINHO_DOTENV, override=False)


def executarServidor() -> None:
    """Inicializa o servidor Uvicorn com o ponto de entrada oficial da aplicacao.

    Returns:
        None: Processo bloqueante do servidor em execucao.
    """
    hostAplicacao = os.getenv("APP_HOST") or os.getenv("HOST", "127.0.0.1")
    portaAplicacao = int(os.getenv("APP_PORT") or os.getenv("PORT", "9001"))

    uvicorn.run(
        "App.Main:aplicacao",
        host=hostAplicacao,
        port=portaAplicacao,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    executarServidor()