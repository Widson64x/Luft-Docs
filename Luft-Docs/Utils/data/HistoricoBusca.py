from __future__ import annotations

import json
import os
from collections import Counter

from Config import MAX_SEARCH_HISTORY, SEARCH_HISTORY_FILE, TOP_MOST_SEARCHED


def CarregarHistoricoBusca() -> list[str]:
    """Carrega o historico local de buscas realizado pela aplicacao."""
    if not os.path.exists(SEARCH_HISTORY_FILE):
        return []
    with open(SEARCH_HISTORY_FILE, encoding="utf-8") as arquivo_historico:
        try:
            return json.load(arquivo_historico)
        except json.JSONDecodeError:
            return []


def SalvarHistoricoBusca(historico: list[str]) -> None:
    """Persiste em disco o historico local de buscas."""
    with open(SEARCH_HISTORY_FILE, "w", encoding="utf-8") as arquivo_historico:
        json.dump(historico, arquivo_historico, ensure_ascii=False, indent=2)


def AdicionarTermoBusca(termo: str) -> None:
    """Adiciona um termo ao historico local mantendo o limite configurado."""
    termo_normalizado = termo.strip().lower()
    if not termo_normalizado:
        return

    historico = [
        item for item in CarregarHistoricoBusca() if item != termo_normalizado
    ]
    historico.insert(0, termo_normalizado)
    SalvarHistoricoBusca(historico[:MAX_SEARCH_HISTORY])


def ObterBuscasRecentes() -> list[str]:
    """Retorna a lista de termos pesquisados mais recentemente."""
    return CarregarHistoricoBusca()


def ObterBuscasMaisFrequentes() -> list[tuple[str, int]]:
    """Retorna os termos mais frequentes registrados localmente."""
    if not os.path.exists(SEARCH_HISTORY_FILE):
        return []
    with open(SEARCH_HISTORY_FILE, encoding="utf-8") as arquivo_historico:
        historico = json.load(arquivo_historico)
    return Counter(historico).most_common(TOP_MOST_SEARCHED)