# /utils/data/search_utils.py
import os
import re
from flask import current_app
from Utils.data.module_utils import carregar_modulos, carregar_markdown, carregar_markdown_tecnico
from Config import GLOBAL_DATA_DIR

# Lista de pastas de submódulos com acesso restrito.
RESTRICTED_SUBMODULE_FOLDERS = ['Integradores']

def extract_media_preview(content):
    """
    Extrai a primeira imagem ou vídeo do conteúdo para usar como preview.
    Suporta tanto URLs absolutas (externas) quanto caminhos relativos (locais).
    Retorna um dicionário com o tipo, o caminho e um booleano 'is_absolute'.
    """
    def is_absolute(url):
        return url.startswith(('http://', 'https://', '//'))

    def get_relative_path(path, media_type_folder):
        target_path = f'/data/{media_type_folder}/'
        if target_path in path:
            return path.split(target_path)[-1]
        return None

    # Prioridade 1: Tag <video> com <source> dentro
    video_tag_match = re.search(r'<video.*?>.*?<source.*?src=["\'](.*?)["\'].*?</video>', content, re.IGNORECASE | re.DOTALL)
    if video_tag_match:
        path = video_tag_match.group(1)
        if is_absolute(path):
            return {'type': 'video', 'path': path, 'is_absolute': True}
        relative_path = get_relative_path(path, 'videos')
        if relative_path:
            return {'type': 'video', 'path': relative_path, 'is_absolute': False}

    # Prioridade 2: Tag <img>
    img_tag_match = re.search(r'<img.*?src=["\'](.*?)["\']', content, re.IGNORECASE)
    if img_tag_match:
        path = img_tag_match.group(1)
        if is_absolute(path):
            return {'type': 'image', 'path': path, 'is_absolute': True}
        relative_path = get_relative_path(path, 'img')
        if relative_path:
            return {'type': 'image', 'path': relative_path, 'is_absolute': False}

    # Prioridade 3: Imagem em Markdown ![alt](path)
    md_image_match = re.search(r'!\[.*?\]\((.*?)\)', content)
    if md_image_match:
        path = md_image_match.group(1)
        if is_absolute(path):
            return {'type': 'image', 'path': path, 'is_absolute': True}
        relative_path = get_relative_path(path, 'img')
        if relative_path:
            return {'type': 'image', 'path': relative_path, 'is_absolute': False}
            
    # Prioridade 4: Vídeo em sintaxe customizada [video](path)
    md_video_match = re.search(r'\[video\]\((.*?)\)', content, re.IGNORECASE)
    if md_video_match:
        path = md_video_match.group(1)
        if is_absolute(path):
            return {'type': 'video', 'path': path, 'is_absolute': True}
        relative_path = get_relative_path(path, 'videos')
        if relative_path:
            return {'type': 'video', 'path': relative_path, 'is_absolute': False}

    return None

def search_all_documents(query: str, token: str, module_filter: str = None, can_view_tecnico: bool = False):
    """
    Realiza uma busca completa em todos os documentos Markdown, aplicando filtros de permissão
    e propagando o token de autenticação nas URLs de resultado.
    """
    if not query: return []
    safe_query = re.escape(query)
    all_modules, _ = carregar_modulos()
    results = []
    
    # Cria o parâmetro do token para ser anexado às URLs.
    token_param = f"&token={token}" if token else ""

    modules_to_search = all_modules
    if module_filter:
        modules_to_search = [m for m in all_modules if m['id'] == module_filter]

    # 1. Busca nos Módulos Principais
    for module in modules_to_search:
        module_id = module['id']
        
        content_doc = carregar_markdown(module_id)
        if content_doc and re.search(safe_query, content_doc, re.IGNORECASE):
            results.append({
                'module_id': module_id, 'module_nome': module['nome'],
                'module_icon': module.get('icon', 'fas fa-file-alt'), 'doc_type': 'Documentação',
                'url': f"/modulo?modulo={module_id}&q={query}{token_param}",
                'content': content_doc,
                'preview': extract_media_preview(content_doc)
            })

        if can_view_tecnico:
            content_tech = carregar_markdown_tecnico(module_id)
            if content_tech and re.search(safe_query, content_tech, re.IGNORECASE):
                results.append({
                    'module_id': module_id, 'module_nome': module['nome'],
                    'module_icon': module.get('icon', 'fas fa-cogs'), 'doc_type': 'Técnico',
                    'url': f"/modulo?modulo_tecnico={module_id}&q={query}{token_param}",
                    'content': content_tech,
                    'preview': extract_media_preview(content_tech)
                })

    # 2. Busca Dinâmica nos Submódulos Globais
    if not module_filter:
        global_path = GLOBAL_DATA_DIR
        for root, _, files in os.walk(global_path):
            
            if not can_view_tecnico:
                normalized_root = root.replace('\\', '/')
                path_components = normalized_root.split('/')
                if any(folder in path_components for folder in RESTRICTED_SUBMODULE_FOLDERS):
                    continue

            for filename in files:
                if filename.endswith('.md'):
                    try:
                        full_path = os.path.join(root, filename)
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        if re.search(safe_query, content, re.IGNORECASE):
                            relative_path = os.path.relpath(root, global_path)
                            file_id = os.path.splitext(filename)[0]
                            sub_path_for_url = os.path.join(relative_path, file_id).replace('\\', '/')
                            if sub_path_for_url.startswith('./'):
                                sub_path_for_url = sub_path_for_url[2:]
                            doc_type = os.path.basename(root)
                            
                            results.append({
                                'module_id': sub_path_for_url,
                                'module_nome': file_id.replace('_', ' ').capitalize(),
                                'module_icon': 'fas fa-globe', 'doc_type': doc_type,
                                'url': f"/modulo?submodulo={sub_path_for_url}&q={query}{token_param}",
                                'content': content,
                                'preview': extract_media_preview(content)
                            })
                    except Exception as e:
                        current_app.logger.error(f"Erro ao ler o arquivo de submódulo {filename}: {e}")

    return results