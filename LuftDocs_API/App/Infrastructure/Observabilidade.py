"""Ferramentas de logging, seguranca e monitoramento da API."""

import logging
import time
from typing import Optional, Tuple

from fastapi import FastAPI, Request, Response
from fastapi.openapi.utils import get_openapi
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, Info, REGISTRY, generate_latest
from prometheus_fastapi_instrumentator import Instrumentator, metrics

from App.Config.ConfiguracoesApi import ConfiguracoesApi


logger = logging.getLogger(__name__)
faixasLatencia = (
    0.005,
    0.01,
    0.025,
    0.05,
    0.075,
    0.1,
    0.25,
    0.5,
    0.75,
    1.0,
    2.5,
    5.0,
    10.0,
)


def configurarLogging(caminhoArquivoLog: str = "server.log") -> logging.Logger:
    """Configura o logging base da aplicacao.

    Args:
        caminhoArquivoLog: Caminho do arquivo de log utilizado em ambiente local e servidor.

    Returns:
        logging.Logger: Logger padrao da API ja configurado.
    """
    logging.basicConfig(
        filename=caminhoArquivoLog,
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s",
        encoding="utf-8",
    )
    return logging.getLogger("LuftDocsApi")


def aplicarCabecalhosSeguranca(aplicacaoApi: FastAPI) -> None:
    """Registra um middleware com cabecalhos HTTP basicos de seguranca.

    Args:
        aplicacaoApi: Subaplicacao FastAPI montada sob o prefixo principal.

    Returns:
        None: Middleware registrado diretamente na aplicacao.
    """

    @aplicacaoApi.middleware("http")
    async def adicionarCabecalhosSeguranca(requisicao: Request, chamarProximo):
        """Aplica cabecalhos de seguranca em todas as respostas da API."""
        resposta = await chamarProximo(requisicao)
        resposta.headers.setdefault("X-Content-Type-Options", "nosniff")
        resposta.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        resposta.headers.setdefault("Referrer-Policy", "no-referrer-when-downgrade")
        resposta.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return resposta


def aplicarMonitoramentoPrometheus(aplicacaoApi: FastAPI, configuracoes: ConfiguracoesApi) -> None:
    """Configura metricas Prometheus e o middleware de observabilidade.

    Args:
        aplicacaoApi: Subaplicacao FastAPI montada sob o prefixo principal.
        configuracoes: Configuracoes centralizadas da aplicacao.

    Returns:
        None: Componentes de monitoramento registrados na aplicacao.
    """
    instrumentador = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=False,
    )
    instrumentador.add(metrics.default(custom_labels={"app_name": configuracoes.nomeAplicacao}))
    instrumentador.instrument(aplicacaoApi)

    contadorRequisicoes = Counter(
        "fastapi_requests_total",
        "Total de requisicoes por metodo, path e status.",
        labelnames=("app_name", "method", "path", "status"),
    )
    contadorRespostas = Counter(
        "fastapi_responses_total",
        "Total de respostas por metodo, path e status_code.",
        labelnames=("app_name", "method", "path", "status_code"),
    )
    histogramaLatencia = Histogram(
        "fastapi_requests_duration_seconds",
        "Latencia das requisicoes em segundos por metodo e path.",
        labelnames=("app_name", "method", "path"),
        buckets=faixasLatencia,
    )
    gaugeEmAndamento = Gauge(
        "fastapi_requests_in_progress",
        "Quantidade de requisicoes em andamento.",
        labelnames=("app_name", "method", "path"),
    )
    contadorExcecoes = Counter(
        "fastapi_exceptions_total",
        "Excecoes nao tratadas por tipo e path.",
        labelnames=("app_name", "type", "path"),
    )
    informacoesAplicacao = Info("fastapi_app_info", "Informacoes da aplicacao.")
    informacoesAplicacao.info(
        {
            "app_name": configuracoes.nomeAplicacao,
            "version": configuracoes.versaoAplicacao,
            "env": configuracoes.ambienteAplicacao,
        }
    )
    gaugeInicioProcesso = Gauge(
        "fastapi_process_start_time_seconds",
        "Epoch de inicializacao do processo da API.",
    )
    gaugeInicioProcesso.set_to_current_time()

    contadorRegistrosLog = Counter(
        "app_log_records_total",
        "Total de registros de log por nivel.",
        labelnames=("app_name", "level"),
    )
    contadorErrosHttp = Counter(
        "app_http_error_total",
        "Total de respostas de erro HTTP.",
        labelnames=("app_name", "endpoint", "method", "status"),
    )
    gaugeUltimoErro = Gauge(
        "app_last_error_timestamp_seconds",
        "Timestamp do ultimo erro HTTP observado.",
        labelnames=("app_name", "endpoint", "method", "status"),
    )

    class ManipuladorLogPrometheus(logging.Handler):
        """Atualiza contadores Prometheus para cada registro de log emitido."""

        def __init__(self, nomeAplicacao: str):
            """Inicializa o manipulador de logs associado a aplicacao.

            Args:
                nomeAplicacao: Nome da aplicacao utilizado nos labels Prometheus.
            """
            super().__init__()
            self.nomeAplicacao = nomeAplicacao

        def emit(self, registro: logging.LogRecord) -> None:
            """Incrementa o contador de logs para cada registro recebido."""
            if registro.name == "uvicorn.access":
                return

            contadorRegistrosLog.labels(
                self.nomeAplicacao,
                registro.levelname.upper(),
            ).inc()

    raizLogger = logging.getLogger()
    if not any(isinstance(manipulador, ManipuladorLogPrometheus) for manipulador in raizLogger.handlers):
        raizLogger.addHandler(ManipuladorLogPrometheus(configuracoes.nomeAplicacao))

    def obterCaminhoTemplate(requisicao: Request) -> str:
        """Resolve o caminho template da rota para rotular metricas de forma consistente."""
        rotaAtual = requisicao.scope.get("route")
        return getattr(rotaAtual, "path", requisicao.url.path)

    @aplicacaoApi.middleware("http")
    async def monitorarRequisicoes(requisicao: Request, chamarProximo):
        """Captura latencia, erros e quantidade de requisicoes em andamento."""
        caminhoTemplate = obterCaminhoTemplate(requisicao)
        if caminhoTemplate == "/metrics":
            return await chamarProximo(requisicao)

        metodoHttp = requisicao.method
        labelsEmAndamento: Tuple[str, str, str] = (
            configuracoes.nomeAplicacao,
            metodoHttp,
            caminhoTemplate,
        )
        gaugeEmAndamento.labels(*labelsEmAndamento).inc()
        instanteInicio = time.perf_counter()
        statusHttp: Optional[int] = None

        try:
            resposta: Response = await chamarProximo(requisicao)
            statusHttp = resposta.status_code
            return resposta
        except Exception as erro:
            statusHttp = 500
            contadorExcecoes.labels(
                configuracoes.nomeAplicacao,
                type(erro).__name__,
                caminhoTemplate,
            ).inc()
            logger.exception("Excecao nao tratada durante o processamento da requisicao.")
            raise
        finally:
            duracaoRequisicao = time.perf_counter() - instanteInicio
            statusSerializado = str(statusHttp or 500)
            contadorRequisicoes.labels(
                configuracoes.nomeAplicacao,
                metodoHttp,
                caminhoTemplate,
                statusSerializado,
            ).inc()
            contadorRespostas.labels(
                configuracoes.nomeAplicacao,
                metodoHttp,
                caminhoTemplate,
                statusSerializado,
            ).inc()
            histogramaLatencia.labels(
                configuracoes.nomeAplicacao,
                metodoHttp,
                caminhoTemplate,
            ).observe(duracaoRequisicao)
            gaugeEmAndamento.labels(*labelsEmAndamento).dec()

            if (statusHttp or 500) >= 400:
                contadorErrosHttp.labels(
                    configuracoes.nomeAplicacao,
                    caminhoTemplate,
                    metodoHttp,
                    statusSerializado,
                ).inc()
                gaugeUltimoErro.labels(
                    configuracoes.nomeAplicacao,
                    caminhoTemplate,
                    metodoHttp,
                    statusSerializado,
                ).set(time.time())

    @aplicacaoApi.get("/metrics")
    def obterMetricas() -> Response:
        """Expõe o endpoint unico de metricas Prometheus da aplicacao."""
        return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


def registrarOpenApiCustomizado(aplicacaoApi: FastAPI, prefixoApi: str) -> None:
    """Ajusta o documento OpenAPI para refletir o prefixo real da aplicacao.

    Args:
        aplicacaoApi: Subaplicacao FastAPI montada sob o prefixo principal.
        prefixoApi: Prefixo publico utilizado na exposicao da API.

    Returns:
        None: Funcao geradora de OpenAPI substituida na aplicacao.
    """

    def gerarOpenApiCustomizado():
        """Gera o schema OpenAPI informando o servidor base montado no host."""
        if aplicacaoApi.openapi_schema:
            return aplicacaoApi.openapi_schema

        schemaOpenApi = get_openapi(
            title=aplicacaoApi.title,
            version=aplicacaoApi.version,
            description=aplicacaoApi.description,
            routes=aplicacaoApi.routes,
        )
        schemaOpenApi["servers"] = [{"url": prefixoApi}]
        aplicacaoApi.openapi_schema = schemaOpenApi
        return aplicacaoApi.openapi_schema

    aplicacaoApi.openapi = gerarOpenApiCustomizado