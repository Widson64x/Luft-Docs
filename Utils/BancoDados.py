from __future__ import annotations

import os
import sqlite3

from flask import current_app, g

from Config import BASE_DIR

NOME_BANCO_DADOS = BASE_DIR / "DATA" / "luftdocs.db"


def ObterCaminhoBanco() -> str:
    """Retorna o caminho absoluto do banco SQLite da aplicacao."""
    return os.path.join(current_app.root_path, str(NOME_BANCO_DADOS))


def ObterBanco() -> sqlite3.Connection:
    """Abre uma conexao SQLite por requisicao quando necessario."""
    if "db" not in g:
        g.db = sqlite3.connect(
            ObterCaminhoBanco(), detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db


def FecharBanco(erro: Exception | None = None) -> None:
    """Fecha a conexao SQLite associada ao contexto atual."""
    del erro
    banco = g.pop("db", None)
    if banco is not None:
        banco.close()


def CriarTabelaReportesBug(cursor: sqlite3.Cursor) -> None:
    """Cria ou atualiza a tabela de reportes de bug da aplicacao."""
    cursor.execute("PRAGMA table_info(bug_reports)")
    colunas_existentes = [coluna[1] for coluna in cursor.fetchall()]

    if not colunas_existentes:
        cursor.execute(
            """
            CREATE TABLE bug_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                report_type TEXT NOT NULL,
                target_entity TEXT,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'aberto',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        return

    if "report_type" not in colunas_existentes:
        cursor.execute(
            "ALTER TABLE bug_reports ADD COLUMN report_type TEXT NOT NULL DEFAULT 'geral'"
        )
    if "target_entity" not in colunas_existentes:
        cursor.execute("ALTER TABLE bug_reports ADD COLUMN target_entity TEXT")


def InicializarBanco() -> None:
    """Inicializa as tabelas auxiliares do banco local da aplicacao."""
    banco = sqlite3.connect(ObterCaminhoBanco())
    cursor = banco.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS document_access (
            document_id TEXT PRIMARY KEY,
            access_count INTEGER NOT NULL DEFAULT 1,
            last_access TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS search_log (
            query_term TEXT PRIMARY KEY,
            search_count INTEGER NOT NULL DEFAULT 1,
            last_searched TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    CriarTabelaReportesBug(cursor)
    banco.commit()
    banco.close()


def InicializarAplicacao(aplicacao) -> None:
    """Registra os hooks de abertura e fechamento do banco com o Flask."""
    aplicacao.teardown_appcontext(FecharBanco)