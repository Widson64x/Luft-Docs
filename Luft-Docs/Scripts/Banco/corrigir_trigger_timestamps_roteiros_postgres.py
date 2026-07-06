from __future__ import annotations

"""
Aplica correcao idempotente no trigger de timestamps da tabela Tb_Docs_Roteiros.

Problema alvo:
- Trigger legado referencia colunas antigas (created_at/updated_at).
- Schema atual usa colunas renomeadas (CriadoEm/AtualizadoEm).

Uso:
    python .\Scripts\Banco\corrigir_trigger_timestamps_roteiros_postgres.py
"""

import importlib.util
import logging
from pathlib import Path
import sys

from sqlalchemy import create_engine, text

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from Config import DATABASE_URL

logger = logging.getLogger("corrigir_trigger_timestamps_roteiros_postgres")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def NormalizarUrlBanco(urlBanco: str) -> str:
    """
    Resolve fallback de driver para ambientes sem psycopg.

    Parameters
    ----------
    urlBanco : str
        URL de conexao do PostgreSQL.

    Returns
    -------
    str
        URL normalizada com driver disponivel no ambiente.
    """
    if "+psycopg" not in urlBanco:
        return urlBanco

    if importlib.util.find_spec("psycopg") is not None:
        return urlBanco

    if importlib.util.find_spec("psycopg2") is not None:
        logger.warning(
            "Driver 'psycopg' indisponivel no ambiente atual. Usando fallback para 'psycopg2'."
        )
        return urlBanco.replace("+psycopg", "+psycopg2")

    return urlBanco


def AplicarCorrecaoTriggerRoteiros(urlBanco: str = DATABASE_URL) -> None:
    """
    Recria a funcao de trigger de timestamps dos roteiros com os nomes atuais de colunas.

    Parameters
    ----------
    urlBanco : str, optional
        URL de conexao ao PostgreSQL, por padrao Config.DATABASE_URL.

    Returns
    -------
    None
        Executa DDL no banco e apenas registra logs.
    """
    sqlCorrecao = """
CREATE OR REPLACE FUNCTION luftdocst.trg_roteiros_timestamps()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        NEW."CriadoEm" = COALESCE(NEW."CriadoEm", CURRENT_TIMESTAMP);
        NEW."AtualizadoEm" = COALESCE(NEW."AtualizadoEm", CURRENT_TIMESTAMP);
    ELSIF (TG_OP = 'UPDATE') THEN
        NEW."AtualizadoEm" = CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$function$;
"""

    engine = create_engine(NormalizarUrlBanco(urlBanco))
    with engine.begin() as conexao:
        conexao.execute(text(sqlCorrecao))

    logger.info("Correcao do trigger 'trg_roteiros_timestamps' aplicada com sucesso.")


def Main() -> int:
    """
    Ponto de entrada do script de correcao do trigger.

    Returns
    -------
    int
        Codigo de saida do processo (0 em caso de sucesso).
    """
    AplicarCorrecaoTriggerRoteiros()
    return 0


if __name__ == "__main__":
    raise SystemExit(Main())
