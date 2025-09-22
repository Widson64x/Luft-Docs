# utils/module_utils.py (Refatorado com SQLAlchemy)

import os
import string
import markdown
from Config import DATA_DIR, GLOBAL_DATA_DIR

# Importa os novos modelos do SQLAlchemy
from models import db, Modulo, PalavraGlobal

def _format_modulo_to_dict(modulo: Modulo) -> dict:
    """
    Converte um objeto Modulo do SQLAlchemy para o formato de dicionário aninhado
    que a aplicação espera, usando os relacionamentos do ORM.
    """
    if not modulo:
        return None
        
    modulo_dict = {c.name: getattr(modulo, c.name) for c in modulo.__table__.columns}
    
    # Usa os relacionamentos para preencher os dados aninhados
    modulo_dict['palavras_chave'] = [p.palavra for p in modulo.palavras_chave]
    modulo_dict['relacionados'] = [r.id for r in modulo.relacionados]
    modulo_dict['edit_history'] = [
        {
            'event': h.event, 'version': h.version, 'editor': h.editor,
            'approver': h.approver, 'timestamp': h.timestamp,
            'backup_file_doc': h.backup_file_doc, 'backup_file_tech': h.backup_file_tech
        } for h in modulo.edit_history
    ]
    
    # Recria as estruturas aninhadas para compatibilidade com o frontend
    modulo_dict['ultima_edicao'] = {
        "user": modulo.ultima_edicao_user,
        "data": modulo.ultima_edicao_data
    }
    modulo_dict['pending_edit_info'] = {
        "user": modulo.pending_edit_user,
        "data": modulo.pending_edit_data
    }
    modulo_dict['version_info'] = {
        "current_version": modulo.current_version,
        "last_approved_by": modulo.last_approved_by,
        "last_approved_on": modulo.last_approved_on
    }
    
    # Remove as chaves "achatadas" que agora estão aninhadas
    for key in ['ultima_edicao_user', 'ultima_edicao_data', 'pending_edit_user', 'pending_edit_data', 'current_version', 'last_approved_by', 'last_approved_on']:
        del modulo_dict[key]
        
    return modulo_dict

def carregar_modulos():
    """Carrega todos os módulos e palavras-chave globais do banco de dados usando o ORM."""
    # Carregar módulos
    modulos_obj = Modulo.query.all()
    
    # Converte cada objeto Modulo em um dicionário, incluindo a 'current_version'
    modulos = []
    for mod in modulos_obj:
        # Assumindo que seu objeto 'mod' tenha os atributos .id, .nome, etc.
        # e também o .current_version que você quer exibir.
        modulos.append({ # Cria um dicionário aninhado para cada módulo
            'id': mod.id,
            'nome': mod.nome,
            'descricao': mod.descricao,
            'icone': mod.icone,
            'status': mod.status,   
            'current_version': mod.current_version,  # Inclui a versão atual
            'edit_history': mod.edit_history, # Mantenha os outros campos necessários
            'pending_edit_info': mod.pending_edit_info
        })
    
    # Carregar palavras globais
    palavras_globais_obj = PalavraGlobal.query.all()
    palavras_globais = {p.palavra: p.descricao for p in palavras_globais_obj}
    
    return modulos, palavras_globais

def carregar_modulos_aprovados():
    """Carrega módulos com status 'aprovado' e palavras-chave globais usando o ORM."""
    # Carregar módulos aprovados
    modulos_aprovados_obj = Modulo.query.filter_by(status='aprovado').all()
    modulos_aprovados = [_format_modulo_to_dict(mod) for mod in modulos_aprovados_obj]

    # Carregar palavras globais
    palavras_globais_obj = PalavraGlobal.query.all()
    palavras_globais = {p.palavra: p.descricao for p in palavras_globais_obj}
    
    return modulos_aprovados, palavras_globais

def get_modulo_by_id(mid: str):
    """Busca um único módulo pelo seu ID usando o ORM."""
    # .get() é a forma mais eficiente de buscar pela chave primária
    modulo_obj = Modulo.query.get(mid)
    return _format_modulo_to_dict(modulo_obj)

# --- Funções que não precisam de alteração ---

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
    nome_arquivo = nome.replace(" ", "_") + ".md"
    path_arquivo = next(iter(GLOBAL_DATA_DIR.rglob(nome_arquivo)), None)
    if path_arquivo:
        return path_arquivo.read_text(encoding='utf-8')
    return None

def limpar_texto(texto):
    texto = texto.lower()
    return texto.translate(str.maketrans('', '', string.punctuation))

def calcula_score(paragrafo, termos_query):
    paragrafo_limpo = limpar_texto(paragrafo)
    palavras = set(paragrafo_limpo.split())
    score = sum(1 for termo in termos_query if termo in palavras)
    return score
