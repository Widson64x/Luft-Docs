from __future__ import annotations

import json
import os
from pathlib import Path

from Config import ARQ


def CarregarAcessos() -> dict:
    """Carrega o historico agregado de acessos aos modulos."""
    if not os.path.exists(ARQ):
        return {}
    with open(ARQ, encoding="utf-8") as arquivo_acesso:
        try:
            return json.load(arquivo_acesso)
        except json.JSONDecodeError:
            return {}


def SalvarAcessos(dadosAcesso: dict) -> None:
    """Persiste o historico agregado de acessos em disco."""
    Path(ARQ).parent.mkdir(parents=True, exist_ok=True)
    with open(ARQ, "w", encoding="utf-8") as arquivo_acesso:
        json.dump(dadosAcesso, arquivo_acesso, indent=4, ensure_ascii=False)


def RegistrarAcesso(identificadorModulo: str) -> None:
    """Incrementa o historico de acesso do modulo informado."""
    from datetime import datetime

    dados_acesso = CarregarAcessos()
    data_atual = datetime.now().strftime("%Y-%m-%d")
    if identificadorModulo not in dados_acesso:
        dados_acesso[identificadorModulo] = {"total": 0, "historico": {}}
    dados_acesso[identificadorModulo]["total"] += 1
    dados_acesso[identificadorModulo]["historico"][data_atual] = (
        dados_acesso[identificadorModulo]["historico"].get(data_atual, 0) + 1
    )
    SalvarAcessos(dados_acesso)


def CalcularTendencia(historico: dict[str, int], dias: int = 7) -> int:
    """Calcula a tendencia recente de acessos de um modulo."""
    datas = sorted(historico.keys())
    if len(datas) < 2:
        return 0

    datas = datas[-dias:]
    acessos = [historico.get(data, 0) for data in datas]
    metade = len(acessos) // 2
    periodo_anterior = acessos[:metade]
    periodo_atual = acessos[metade:]
    media_anterior = sum(periodo_anterior) / len(periodo_anterior) if periodo_anterior else 0
    media_atual = sum(periodo_atual) / len(periodo_atual) if periodo_atual else 0

    if media_atual > media_anterior:
        return 1
    if media_atual < media_anterior:
        return -1
    return 0


def ObterMaisAcessadosComTendencia(
    modulos: list[dict], limite: int = 7, diasTendencia: int = 7
) -> list[tuple[dict, int, int | str]]:
    """Retorna os modulos mais acessados com tendencia calculada."""
    acessos = CarregarAcessos()
    modulos_por_id = {modulo["id"]: modulo for modulo in modulos}
    resultados = []

    for identificador, valor in acessos.items():
        if identificador not in modulos_por_id:
            continue

        if isinstance(valor, int):
            total = valor
            historico = {}
        else:
            total = valor.get("total", 0)
            historico = valor.get("historico", {})

        tendencia = (
            CalcularTendencia(historico, diasTendencia) if historico else "Sem dados"
        )
        resultados.append((modulos_por_id[identificador], total, tendencia))

    return sorted(resultados, key=lambda item: -item[1])[:limite]