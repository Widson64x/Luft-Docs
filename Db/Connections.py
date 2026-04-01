from __future__ import annotations

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from Config import ConfiguracaoAtual


BasePostgres = declarative_base()
BaseSqlServer = declarative_base()


@lru_cache(maxsize=1)
def obterEnginePostgres() -> Engine:
    opcoesEngine: dict[str, object] = {
        "pool_pre_ping": True,
        "echo": ConfiguracaoAtual.mostrarLogsDb,
        "future": True,
    }

    schemaPostgres = (ConfiguracaoAtual.schemaPostgres or "").strip()
    if schemaPostgres:
        opcoesEngine["connect_args"] = {"options": f"-c search_path={schemaPostgres}"}

    return create_engine(
        ConfiguracaoAtual.obterUrlPostgres(),
        **opcoesEngine,
        poolclass=NullPool,
    )


@lru_cache(maxsize=1)
def obterEngineSqlServer() -> Engine | None:
    urlBanco = ConfiguracaoAtual.obterUrlSqlServer()
    if not urlBanco:
        return None

    return create_engine(
        urlBanco,
        poolclass=NullPool,
        echo=ConfiguracaoAtual.mostrarLogsDb,
        future=True,
    )


@lru_cache(maxsize=1)
def obterFabricaSessaoPostgres() -> sessionmaker[Session]:
    return sessionmaker(
        bind=obterEnginePostgres(),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )


@lru_cache(maxsize=1)
def obterFabricaSessaoSqlServer() -> sessionmaker[Session] | None:
    engineSqlServer = obterEngineSqlServer()
    if engineSqlServer is None:
        return None

    return sessionmaker(
        bind=engineSqlServer,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )


def obterSessaoPostgres() -> Session:
    return obterFabricaSessaoPostgres()()


def obterSessaoSqlServer() -> Session | None:
    fabricaSessao = obterFabricaSessaoSqlServer()
    if fabricaSessao is None:
        return None
    return fabricaSessao()


def fecharSessoesAtivas() -> None:
    # Nao executar fechamento global de sessoes: isso invalida sessoes ativas
    # de outras requisicoes concorrentes e pode causar "This Connection is closed".
    return None
