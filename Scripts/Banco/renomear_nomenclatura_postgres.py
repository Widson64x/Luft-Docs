from __future__ import annotations

import argparse
import importlib.util
import logging
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from Config import DATABASE_URL
from Scripts.Banco.mapa_renomeacao_docs import MAPA_COLUNAS, MAPA_TABELAS, obter_mapa_reverso

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("renomear_nomenclatura_postgres")

SCHEMA_PADRAO = "luftdocst"


def _identificador(nome: str) -> str:
    return '"' + nome.replace('"', '""') + '"'


def _nome_qualificado(schema: str, nome: str) -> str:
    return f"{_identificador(schema)}.{_identificador(nome)}"


def _carregar_mapas(reverter: bool) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    if reverter:
        return obter_mapa_reverso()
    return MAPA_TABELAS, MAPA_COLUNAS


def _normalizar_url_banco(url_banco: str) -> str:
    if "+psycopg" not in url_banco:
        return url_banco

    if importlib.util.find_spec("psycopg") is not None:
        return url_banco

    if importlib.util.find_spec("psycopg2") is not None:
        logger.warning(
            "Driver 'psycopg' indisponivel no ambiente atual. Usando fallback automatico para 'psycopg2'."
        )
        return url_banco.replace("+psycopg", "+psycopg2")

    return url_banco


def _listar_colunas(engine, schema: str, tabela: str) -> set[str]:
    inspetor = inspect(engine)
    return {coluna["name"] for coluna in inspetor.get_columns(tabela, schema=schema)}


def _montar_sql(engine, schema: str, reverter: bool) -> list[str]:
    mapa_tabelas, mapa_colunas = _carregar_mapas(reverter)
    inspetor = inspect(engine)
    tabelas_existentes = set(inspetor.get_table_names(schema=schema))
    mapa_tabelas_inverso = {destino: origem for origem, destino in mapa_tabelas.items()}
    comandos_tabelas: list[str] = []
    comandos_colunas: list[str] = []

    for tabela_atual, tabela_nova in mapa_tabelas.items():
        if tabela_atual in tabelas_existentes and tabela_nova not in tabelas_existentes:
            comandos_tabelas.append(
                f"ALTER TABLE {_nome_qualificado(schema, tabela_atual)} RENAME TO {_identificador(tabela_nova)};"
            )

    for tabela_execucao, colunas in mapa_colunas.items():
        tabela_consulta = tabela_execucao
        if tabela_consulta not in tabelas_existentes:
            tabela_origem = mapa_tabelas_inverso.get(tabela_execucao)
            if not tabela_origem or tabela_origem not in tabelas_existentes:
                continue
            tabela_consulta = tabela_origem

        colunas_existentes = _listar_colunas(engine, schema, tabela_consulta)
        if not colunas_existentes:
            continue

        for coluna_atual, coluna_nova in colunas.items():
            candidatos = coluna_atual if isinstance(coluna_atual, tuple) else (coluna_atual,)
            coluna_encontrada = next(
                (candidato for candidato in candidatos if candidato in colunas_existentes),
                None,
            )

            if coluna_encontrada and coluna_nova not in colunas_existentes:
                comandos_colunas.append(
                    f"ALTER TABLE {_nome_qualificado(schema, tabela_execucao)} RENAME COLUMN {_identificador(coluna_encontrada)} TO {_identificador(coluna_nova)};"
                )
                colunas_existentes.remove(coluna_encontrada)
                colunas_existentes.add(coluna_nova)

    if reverter:
        return comandos_colunas + comandos_tabelas
    return comandos_tabelas + comandos_colunas


def executar(schema: str, aplicar: bool, reverter: bool, url_banco: str) -> int:
    engine = create_engine(_normalizar_url_banco(url_banco))
    comandos = _montar_sql(engine, schema=schema, reverter=reverter)

    if not comandos:
        logger.info("Nenhum comando pendente para o schema '%s'.", schema)
        return 0

    logger.info("Comandos planejados para o schema '%s':", schema)
    for comando in comandos:
        logger.info(comando)

    if not aplicar:
        logger.info("Modo dry-run ativo. Nenhuma alteracao foi aplicada.")
        return 0

    with engine.begin() as conexao:
        for comando in comandos:
            conexao.execute(text(comando))

    logger.info("Renomeacao concluida com sucesso.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Renomeia tabelas e colunas do PostgreSQL para o padrao PascalCase do schema luftdocst sem perda de dados."
    )
    parser.add_argument(
        "--schema",
        default=SCHEMA_PADRAO,
        help=f"Schema alvo do PostgreSQL. Padrao: {SCHEMA_PADRAO}",
    )
    parser.add_argument("--url", default=DATABASE_URL, help="URL do banco. Padrao: Config.DATABASE_URL")
    parser.add_argument("--aplicar", action="store_true", help="Aplica as alteracoes. Sem esta flag, roda apenas em dry-run.")
    parser.add_argument("--reverter", action="store_true", help="Reverte a renomeacao usando o mapa inverso.")
    args = parser.parse_args()
    return executar(schema=args.schema, aplicar=args.aplicar, reverter=args.reverter, url_banco=args.url)


if __name__ == "__main__":
    raise SystemExit(main())