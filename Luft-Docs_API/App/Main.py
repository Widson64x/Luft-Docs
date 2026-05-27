"""Ponto de entrada ASGI da aplicacao LuftDocs."""

from fastapi import FastAPI

from App.Bootstrap.AplicacaoFactory import criarAplicacaoPrincipal


def criarAplicacao() -> FastAPI:
    """
    Cria a aplicacao ASGI principal utilizada pelo servidor Uvicorn.

    Returns:
        FastAPI: Aplicacao completa pronta para servir requisicoes HTTP.
    """
    return criarAplicacaoPrincipal()


aplicacao = criarAplicacao()
