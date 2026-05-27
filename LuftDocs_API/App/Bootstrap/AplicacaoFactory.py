"""Fabrica responsavel por compor a aplicacao FastAPI principal."""

from typing import Any, Dict
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware

from App.Config.ConfiguracoesApi import carregarConfiguracoesApi
from App.Controllers.UsuarioController import roteadorUsuario
from App.Infrastructure.Observabilidade import (
    aplicarCabecalhosSeguranca,
    aplicarMonitoramentoPrometheus,
    configurarLogging,
    registrarOpenApiCustomizado,
)
from App.Views.PortalView import gerarHtmlPortal


configuracoesApi = carregarConfiguracoesApi()
logger = configurarLogging()


def criarSubAplicacao() -> FastAPI:
    """Cria a subaplicacao montada sob o prefixo publico da API.

    Returns:
        FastAPI: Subaplicacao com middlewares, rotas e monitoramento configurados.
    """
    aplicacaoApi = FastAPI(
        title="API LuftDocs",
        description=(
            "API responsavel pela autenticacao e integracoes essenciais do LuftDocs, "
            "com observabilidade, portal tecnico e documentacao interativa."
        ),
        version=configuracoesApi.versaoAplicacao,
        contact={"name": "Time de Desenvolvimento", "email": "widson.araujo@luftlogistics.com"},
        license_info={"name": "MIT License"},
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        swagger_ui_parameters={
            "docExpansion": "none",
            "displayRequestDuration": True,
            "persistAuthorization": True,
            "deepLinking": True,
            "tryItOutEnabled": True,
            "filter": True,
        },
    )

    aplicacaoApi.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    aplicacaoApi.add_middleware(GZipMiddleware, minimum_size=1024)
    aplicacaoApi.add_middleware(SessionMiddleware, secret_key=configuracoesApi.segredoSessao)

    aplicarCabecalhosSeguranca(aplicacaoApi)
    aplicarMonitoramentoPrometheus(aplicacaoApi, configuracoesApi)

    @aplicacaoApi.get("/")
    def obterStatusApi() -> Dict[str, str]:
        """Retorna o status simplificado da API montada sob o prefixo principal."""
        logger.info("Health check executado com sucesso.")
        return {"status": "API LuftDocs esta online"}

    @aplicacaoApi.get("/portal", response_class=HTMLResponse)
    def exibirPortal() -> HTMLResponse:
        """Renderiza a pagina HTML de navegacao tecnica da API."""
        return HTMLResponse(gerarHtmlPortal(configuracoesApi))

    @aplicacaoApi.get("/links")
    def listarLinksUteis() -> Dict[str, Any]:
        """Publica os principais atalhos operacionais da API montada."""
        baseApi = configuracoesApi.prefixoApi
        return {
            "app_name": configuracoesApi.nomeAplicacao,
            "version": configuracoesApi.versaoAplicacao,
            "env": configuracoesApi.ambienteAplicacao,
            "useful": {
                "portal": f"{baseApi}/portal",
                "health": f"{baseApi}/",
                "docs_swagger": f"{baseApi}/docs",
                "docs_redoc": f"{baseApi}/redoc",
                "openapi": f"{baseApi}/openapi.json",
                "metrics": f"{baseApi}/metrics",
            },
        }

    try:
        aplicacaoApi.include_router(roteadorUsuario)
        logger.info("Rotas do modulo de usuario carregadas com sucesso.")
    except Exception as erro:
        logger.critical("Falha critica ao carregar as rotas de usuario: %s", erro)
        raise

    registrarOpenApiCustomizado(aplicacaoApi, configuracoesApi.prefixoApi)
    return aplicacaoApi


def criarAplicacaoPrincipal() -> FastAPI:
    """Cria a aplicacao raiz que hospeda a subaplicacao publica da API.

    Returns:
        FastAPI: Aplicacao ASGI principal do projeto.
    """
    subAplicacao = criarSubAplicacao()
    aplicacaoPrincipal = FastAPI(
        title="Root - LuftDocs host",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    @aplicacaoPrincipal.get("/")
    def obterRaiz() -> Dict[str, Any]:
        """Mantem a raiz do host enxuta e aponta para o prefixo oficial da API."""
        return {
            "ok": True,
            "msg": f"Host root. API disponivel em {configuracoesApi.prefixoApi}/",
        }

    aplicacaoPrincipal.mount(configuracoesApi.prefixoApi, subAplicacao)
    return aplicacaoPrincipal