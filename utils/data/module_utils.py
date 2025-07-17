# utils/modulo_utils.py

import os
import json
import string
import markdown
from pathlib import Path
from config import DATA_DIR, CONFIG_FILE, GLOBAL_DATA_DIR, MODULE_ACCESS_FILE

def carregar_config():
    with open(CONFIG_FILE, encoding='utf-8') as f:
        return json.load(f)

def carregar_modulos():
    config = carregar_config()
    return config["modulos"], config["palavras_globais"]

def carregar_modulos_aprovados():
    config = carregar_config()
    modulos_aprovados = [m for m in config["modulos"] if m.get("status") == "aprovado"]
    return modulos_aprovados, config["palavras_globais"]

def carregar_markdown(modulo_id):
    path = os.path.join(DATA_DIR, modulo_id, 'documentation.md')
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        markdown_text = f.read()
        return markdown.markdown(markdown_text, extensions=['fenced_code', 'tables'])

def carregar_markdown_tecnico(modulo_id):
    path = os.path.join(DATA_DIR, modulo_id, 'technical_documentation.md')
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        return f.read()
    
def carregar_markdown_submodulo(nome: str) -> str | None:
    """
    Lê o arquivo <nome>.md dentro de data/global ou de qualquer uma de suas subpastas.
    A busca é feita recursivamente.
    """
    nome_arquivo = nome.replace(" ", "_") + ".md"

    # --- INÍCIO DA DEPURAÇÃO ---
    print("\n--- [DEBUG] Iniciando busca por submódulo ---")
    print(f"Nome do arquivo procurado: '{nome_arquivo}'")
    print(f"Diretório de busca (caminho absoluto): '{GLOBAL_DATA_DIR.resolve()}'")

    found_files = list(GLOBAL_DATA_DIR.rglob(nome_arquivo))
    print(f"Arquivos encontrados na busca: {found_files}")

    path_arquivo = next(iter(found_files), None)
    # --- FIM DA DEPURAÇÃO ---

    if path_arquivo:
        print(f"Arquivo correspondente selecionado: '{path_arquivo}'")
        print("--- [DEBUG] Fim da busca ---\n")
        return path_arquivo.read_text(encoding='utf-8')

    print("Nenhum arquivo correspondente foi encontrado.")
    print("--- [DEBUG] Fim da busca ---\n")
    return None

def get_modulo_by_id(modulos, mid):
    return next((m for m in modulos if m["id"] == mid), None)

def limpar_texto(texto):
    texto = texto.lower()
    return texto.translate(str.maketrans('', '', string.punctuation))

def calcula_score(paragrafo, termos_query):
    paragrafo_limpo = limpar_texto(paragrafo)
    palavras = set(paragrafo_limpo.split())
    score = sum(1 for termo in termos_query if termo in palavras)
    return score