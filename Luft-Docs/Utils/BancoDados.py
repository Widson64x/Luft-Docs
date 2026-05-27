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


def _ListarTabelas(cursor: sqlite3.Cursor) -> set[str]:
    cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    return {linha[0] for linha in cursor.fetchall()}


def _ListarColunas(cursor: sqlite3.Cursor, tabela: str) -> set[str]:
    cursor.execute(f'PRAGMA table_info("{tabela}")')
    return {coluna[1] for coluna in cursor.fetchall()}


def _RenomearTabelaSeExistir(cursor: sqlite3.Cursor, tabela_atual: str, tabela_nova: str) -> None:
    tabelas_existentes = _ListarTabelas(cursor)
    if tabela_atual in tabelas_existentes and tabela_nova not in tabelas_existentes:
        cursor.execute(f'ALTER TABLE "{tabela_atual}" RENAME TO "{tabela_nova}"')


def _RenomearColunaSeExistir(cursor: sqlite3.Cursor, tabela: str, coluna_atual: str, coluna_nova: str) -> None:
    colunas_existentes = _ListarColunas(cursor, tabela)
    if coluna_atual in colunas_existentes and coluna_nova not in colunas_existentes:
        cursor.execute(
            f'ALTER TABLE "{tabela}" RENAME COLUMN "{coluna_atual}" TO "{coluna_nova}"'
        )


def CriarTabelaReportesBug(cursor: sqlite3.Cursor) -> None:
    """Cria ou atualiza a tabela de reportes de bug da aplicacao."""
    tabela = "Tb_Docs_ReportesBug"
    _RenomearTabelaSeExistir(cursor, "bug_reports", tabela)

    colunas_existentes = _ListarColunas(cursor, tabela)

    if not colunas_existentes:
        cursor.execute(
            """
            CREATE TABLE Tb_Docs_ReportesBug (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                UsuarioId INTEGER NOT NULL,
                TipoReporte TEXT NOT NULL,
                EntidadeAlvo TEXT,
                CategoriaErro TEXT,
                Descricao TEXT NOT NULL,
                Status TEXT NOT NULL DEFAULT 'aberto',
                CriadoEm TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        return

    _RenomearColunaSeExistir(cursor, tabela, "id", "Id")
    _RenomearColunaSeExistir(cursor, tabela, "user_id", "UsuarioId")
    _RenomearColunaSeExistir(cursor, tabela, "usuario_id", "UsuarioId")
    _RenomearColunaSeExistir(cursor, tabela, "report_type", "TipoReporte")
    _RenomearColunaSeExistir(cursor, tabela, "tipo_reporte", "TipoReporte")
    _RenomearColunaSeExistir(cursor, tabela, "target_entity", "EntidadeAlvo")
    _RenomearColunaSeExistir(cursor, tabela, "entidade_alvo", "EntidadeAlvo")
    _RenomearColunaSeExistir(cursor, tabela, "error_category", "CategoriaErro")
    _RenomearColunaSeExistir(cursor, tabela, "categoria_erro", "CategoriaErro")
    _RenomearColunaSeExistir(cursor, tabela, "description", "Descricao")
    _RenomearColunaSeExistir(cursor, tabela, "descricao", "Descricao")
    _RenomearColunaSeExistir(cursor, tabela, "status", "Status")
    _RenomearColunaSeExistir(cursor, tabela, "created_at", "CriadoEm")
    _RenomearColunaSeExistir(cursor, tabela, "criado_em", "CriadoEm")

    colunas_existentes = _ListarColunas(cursor, tabela)
    if "TipoReporte" not in colunas_existentes:
        cursor.execute(
            f'ALTER TABLE "{tabela}" ADD COLUMN "TipoReporte" TEXT NOT NULL DEFAULT \"geral\"'
        )
    if "EntidadeAlvo" not in colunas_existentes:
        cursor.execute(f'ALTER TABLE "{tabela}" ADD COLUMN "EntidadeAlvo" TEXT')
    if "CategoriaErro" not in colunas_existentes:
        cursor.execute(f'ALTER TABLE "{tabela}" ADD COLUMN "CategoriaErro" TEXT')


def InicializarBanco() -> None:
    """Inicializa as tabelas auxiliares do banco local da aplicacao."""
    banco = sqlite3.connect(ObterCaminhoBanco())
    cursor = banco.cursor()

    _RenomearTabelaSeExistir(cursor, "document_access", "Tb_Docs_LogAcessosDocumentos")
    _RenomearTabelaSeExistir(cursor, "search_log", "Tb_Docs_LogBuscas")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Tb_Docs_LogAcessosDocumentos (
            DocumentoId TEXT PRIMARY KEY,
            QuantidadeAcessos INTEGER NOT NULL DEFAULT 1,
            UltimoAcessoEm TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    _RenomearColunaSeExistir(cursor, "Tb_Docs_LogAcessosDocumentos", "document_id", "DocumentoId")
    _RenomearColunaSeExistir(cursor, "Tb_Docs_LogAcessosDocumentos", "documento_id", "DocumentoId")
    _RenomearColunaSeExistir(cursor, "Tb_Docs_LogAcessosDocumentos", "access_count", "QuantidadeAcessos")
    _RenomearColunaSeExistir(cursor, "Tb_Docs_LogAcessosDocumentos", "quantidade_acessos", "QuantidadeAcessos")
    _RenomearColunaSeExistir(cursor, "Tb_Docs_LogAcessosDocumentos", "last_access", "UltimoAcessoEm")
    _RenomearColunaSeExistir(cursor, "Tb_Docs_LogAcessosDocumentos", "ultimo_acesso_em", "UltimoAcessoEm")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Tb_Docs_LogBuscas (
            TermoBusca TEXT PRIMARY KEY,
            QuantidadeBuscas INTEGER NOT NULL DEFAULT 1,
            UltimaBuscaEm TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    _RenomearColunaSeExistir(cursor, "Tb_Docs_LogBuscas", "query_term", "TermoBusca")
    _RenomearColunaSeExistir(cursor, "Tb_Docs_LogBuscas", "termo_busca", "TermoBusca")
    _RenomearColunaSeExistir(cursor, "Tb_Docs_LogBuscas", "search_count", "QuantidadeBuscas")
    _RenomearColunaSeExistir(cursor, "Tb_Docs_LogBuscas", "quantidade_buscas", "QuantidadeBuscas")
    _RenomearColunaSeExistir(cursor, "Tb_Docs_LogBuscas", "last_searched", "UltimaBuscaEm")
    _RenomearColunaSeExistir(cursor, "Tb_Docs_LogBuscas", "ultima_busca_em", "UltimaBuscaEm")

    CriarTabelaReportesBug(cursor)
    banco.commit()
    banco.close()


def InicializarAplicacao(aplicacao) -> None:
    """Registra os hooks de abertura e fechamento do banco com o Flask."""
    aplicacao.teardown_appcontext(FecharBanco)