# utils/module_access.py

import json
import os
from collections import Counter
from config import DATA_DIR, CONFIG_FILE, GLOBAL_DATA_DIR, MODULE_ACCESS_FILE
# ou importe ARQ se necessário
from config import ARQ

def load_access():
    if not os.path.exists(ARQ):
        return {}
    with open(ARQ, encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            # Arquivo está vazio ou corrompido, recomeça zerado
            return {}


def save_access(data):
    with open(ARQ, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

from datetime import datetime, timedelta
def register_access(modulo_id):
    data = load_access()
    hoje = datetime.now().strftime("%Y-%m-%d")
    if modulo_id not in data:
        data[modulo_id] = {"total": 0, "historico": {}}
    data[modulo_id]["total"] += 1
    data[modulo_id]["historico"][hoje] = data[modulo_id]["historico"].get(hoje, 0) + 1
    save_access(data)

def get_most_accessed_with_trend(modulos, top=7, trend_days=7):
    access = load_access()
    modulos_by_id = {m['id']: m for m in modulos}
    results = []

    def calc_trend(historico, days=7):
        # Pega os dias disponíveis no histórico, ordenados do mais antigo para o mais recente
        dias = sorted(historico.keys())
        if len(dias) < 2:
            return 0  # Não tem como calcular tendência

        # Só pega os últimos N dias pedidos
        dias = dias[-days:]
        acessos = [historico.get(d, 0) for d in dias]

        metade = len(acessos) // 2
        anterior = acessos[:metade]
        atual = acessos[metade:]

        # Cálculo seguro das médias
        media_anterior = sum(anterior) / len(anterior) if anterior else 0
        media_atual = sum(atual) / len(atual) if atual else 0

        if media_atual > media_anterior:
            return 1
        elif media_atual < media_anterior:
            return -1
        else:
            return 0


    # Monta lista [(modulo, total, tendência)], ordenada pelo total
    for mid, val in access.items():
        if mid in modulos_by_id:
            # Se estiver no formato antigo, converte
            if isinstance(val, int):
                total = val
                historico = {}
            else:
                total = val.get("total", 0)
                historico = val.get("historico", {})

            tendencia = calc_trend(historico) if historico else "Sem dados"
            results.append( (modulos_by_id[mid], total, tendencia) )

    # Ordena pelo total
    results = sorted(results, key=lambda x: -x[1])[:top]
    return results
