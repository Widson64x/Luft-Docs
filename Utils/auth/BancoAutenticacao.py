from __future__ import annotations

import sqlite3

from Config import DB_PATH


def ConectarBanco() -> sqlite3.Connection:
    """Abre uma conexao com o banco local utilizado na autenticacao."""
    return sqlite3.connect(DB_PATH)


def VerificarUsuario(nomeUsuario: str, identificadorUsuario: str) -> bool:
    """Verifica se o usuario informado existe na tabela local de usuarios."""
    conexao = ConectarBanco()
    cursor = conexao.cursor()
    cursor.execute(
        "SELECT 1 FROM users WHERE user_name = ? AND user_id = ?",
        (nomeUsuario, identificadorUsuario),
    )
    resultado = cursor.fetchone()
    conexao.close()
    return resultado is not None