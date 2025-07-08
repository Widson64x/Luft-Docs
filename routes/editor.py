# routes/editor.py

from flask import Blueprint, render_template, request, redirect, url_for, abort, session, flash, jsonify
from werkzeug.utils import secure_filename
from utils.data.module_utils import carregar_modulos, get_modulo_by_id
from routes.permissions import load_permissions, get_user_group
# a menos que você o use em outro lugar. Se não, pode ser removido.
from config import DATA_DIR, CONFIG_FILE, BASE_DIR
import os
import re
import json
import markdown
import diff_match_patch as dmp_module
import shutil
from datetime import datetime

editor_bp = Blueprint('editor', __name__, url_prefix='/editor')

def limpar_linhas_em_branco(md: str) -> str:
    """
    - Normaliza CRLF para LF
    - Remove espaços em branco no fim do texto
    - Colapsa 3+ quebras de linha em exatamente 2 (\n\n)
    """
    text = md.replace('\r\n', '\n').rstrip()
    return re.sub(r'\n{3,}', '\n\n', text)


def processar_e_salvar_imagens(markdown, modulo_id, token):
    """
    Move imagens usadas do tmp para a pasta oficial.
    Ajusta os links no markdown para o novo caminho.
    Retorna o markdown ajustado.
    """
    padrao = re.compile(
        r'\!\[.*?\]\(/data/tmp_img_uploads/' + re.escape(token) + '/' + re.escape(modulo_id) + r'/([^)]+)\)'
    )
    img_dir = os.path.join(BASE_DIR, 'data', 'img', modulo_id)
    os.makedirs(img_dir, exist_ok=True)

    def mover(match):
        nome_arquivo = match.group(1)
        origem = os.path.join(BASE_DIR, 'data', 'tmp_img_uploads', token, modulo_id, nome_arquivo)
        base, ext = os.path.splitext(nome_arquivo)
        destino = os.path.join(img_dir, nome_arquivo)
        nome_final = nome_arquivo
        if os.path.exists(origem):
            # Se já existe, incrementa o sufixo numérico
            i = 1
            while os.path.exists(destino):
                nome_final = f"{base}_{i}{ext}"
                destino = os.path.join(img_dir, nome_final)
                i += 1
            shutil.move(origem, destino)
        # Retorna o novo link
        return f'![{nome_final}](\/data\/img\/{modulo_id}\/{nome_final})'

    markdown_novo = padrao.sub(mover, markdown)
    return markdown_novo

# MODIFICADO: Função simplificada para não verificar permissão.
# Sempre salva diretamente e cria backup.
def salvar_edicao_modulo(modulo, novo_conteudo, user_name):
    """
    Grava em pending_documentation.md e marca status como 'pendente'.
    """
    mod_id    = modulo['id']
    path_mod  = os.path.join(DATA_DIR, mod_id)
    os.makedirs(path_mod, exist_ok=True)

    # 1) Salva no pending
    pending_path  = os.path.join(path_mod, "pending_documentation.md")
    with open(pending_path, "w", encoding="utf-8") as f:
        f.write(novo_conteudo)

    # 2) Atualiza status para pendente
    modulo['status'] = 'pendente'
    modulo['ultima_edicao'] = {"user": user_name, "data": datetime.now().isoformat()}

    # 3) Atualiza config.json
    with open(CONFIG_FILE, "r", encoding='utf-8') as f:
        config = json.load(f)
    for idx, m in enumerate(config['modulos']):
        if m['id'] == mod_id:
            config['modulos'][idx] = modulo
            break
    with open(CONFIG_FILE, "w", encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def salvar_edicao_modulo_com_tecnico(modulo, novo_conteudo, novo_conteudo_tech, user_name):
    """
    Grava em pending_documentation.md e pending_technical_documentation.md,
    marca status como 'pendente' e registra quem editou no campo 'pending_edit_info'.
    """
    mod_id = modulo['id']
    path_mod = os.path.join(DATA_DIR, mod_id)
    os.makedirs(path_mod, exist_ok=True)

    # 1) Salva os arquivos pendentes
    with open(os.path.join(path_mod, "pending_documentation.md"), "w", encoding="utf-8") as f:
        f.write(novo_conteudo)
    with open(os.path.join(path_mod, "pending_technical_documentation.md"), "w", encoding="utf-8") as f:
        f.write(novo_conteudo_tech)

    # 2) ATUALIZADO: Atualiza o status e as informações da edição pendente
    # Em vez de 'ultima_edicao', usamos um campo específico para pendências.
    modulo['status'] = 'pendente'
    modulo['pending_edit_info'] = {"user": user_name, "data": datetime.now().isoformat()}

    # 3) Atualiza config.json
    with open(CONFIG_FILE, "r", encoding='utf-8') as f:
        config = json.load(f)
    for idx, m in enumerate(config['modulos']):
        if m['id'] == mod_id:
            config['modulos'][idx] = modulo
            break
    with open(CONFIG_FILE, "w", encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

@editor_bp.route('/')
def editor_index():
    # 2. Carrega flags de permissão vindas da sessão
    grupo, user_name = get_user_group()
    user_perms = session.get('permissions', {})
    can_access_editor           = user_perms.get('can_access_editor', False)
    can_edit_modules           = user_perms.get('can_edit_modules', False)
    can_delete_modules             = user_perms.get('can_delete_modules', False)
    can_create_modules = user_perms.get('can_create_modules', False)
    can_versioning_modules = user_perms.get('can_versioning_modules', False)
    can_module_control = user_perms.get('can_module_control', False)
    # FUNÇÃO E OBTÉM A CONTAGEM DE PENDENCIAS
    num_pendencias = get_pending_count()

    token = request.args.get('token', '')
    modulos, _ = carregar_modulos()
    return render_template(
        'editor/editor_index.html',
        modulos=modulos,
        token=token,
        can_access_editor=can_edit_modules,
        can_delete_modules=can_delete_modules,
        can_versioning_modules=can_versioning_modules,
        can_module_control=can_module_control,
        num_pendencias=num_pendencias,
        can_create_modules=can_create_modules
    )

@editor_bp.route('/upload_image/<modulo_id>', methods=['POST'])
def upload_image(modulo_id):
    token = request.args.get('token', '')
    if not token:
        return jsonify({'error': 'Token obrigatório'}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    file = request.files['file']
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
        return jsonify({'error': 'Formato não suportado'}), 400

    dest_dir = os.path.join(BASE_DIR, 'data', 'img', modulo_id)
    os.makedirs(dest_dir, exist_ok=True)

    # Gera nome sequencial: img1.png, img2.png, etc.
    i = 1
    while True:
        filename = f"img{i}{ext}"
        safe_name = secure_filename(filename)
        file_path = os.path.join(dest_dir, safe_name)
        if not os.path.exists(file_path):
            break
        i += 1

    file.save(file_path)

    return jsonify({
        'url': f'/data/img/{modulo_id}/{safe_name}'
    })

@editor_bp.route('/upload_video/<modulo_id>', methods=['POST'])
def upload_video(modulo_id):
    token = request.args.get('token', '')
    if not token:
        return jsonify({'error': 'Token obrigatório'}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    file = request.files['file']
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.mp4', '.webm', '.ogg']:
        return jsonify({'error': 'Formato de vídeo não suportado'}), 400

    dest_dir = os.path.join(BASE_DIR, 'data', 'videos', modulo_id)
    os.makedirs(dest_dir, exist_ok=True)
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(dest_dir, filename)
    
    file.save(file_path)
    
    return jsonify({
        'url': f'/data/videos/{modulo_id}/{filename}',
        'type': f'video/{ext[1:]}'
    })

@editor_bp.route('/upload_anexo', methods=['POST'])
def upload_anexo():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    file = request.files['file']
    filename = secure_filename(file.filename)
    dest_folder = os.path.join(BASE_DIR, 'data', 'downloads', 'docs')
    os.makedirs(dest_folder, exist_ok=True)
    file_path = os.path.join(dest_folder, filename)
    file.save(file_path)
    url = f'/download?token=__TOKEN_PLACEHOLDER__&download={filename}'
    return jsonify({'url': url})


@editor_bp.route('/modulo/<mid>', methods=['GET', 'POST'])
def editar_modulo(mid):
    # <<< INÍCIO DA VERIFICAÇÃO DE PERMISSÃO >>>
    grupo, user_name = get_user_group()
    perms = load_permissions().get('can_access_editor', {})
    allowed = (grupo in perms.get('groups', []) or user_name in perms.get('users', []))
    if not allowed:
        return render_template('access_denied.html', reason="Você não tem permissão para editar módulos."), 403
    # <<< FIM DA VERIFICAÇÃO DE PERMISSÃO >>>

    token = request.args.get('token', '')
    modulos, _ = carregar_modulos()
    modulo = get_modulo_by_id(modulos, mid)
    if not modulo:
        abort(404)

    path_mod = os.path.join(DATA_DIR, mid)
    official_path       = os.path.join(path_mod, "documentation.md")
    pending_path        = os.path.join(path_mod, "pending_documentation.md")
    tech_official_path = os.path.join(path_mod, "technical_documentation.md")
    tech_pending_path  = os.path.join(path_mod, "pending_technical_documentation.md")

    # Leitura + limpeza das quebras de linha
    if os.path.exists(official_path):
        raw = open(official_path, encoding='utf-8').read()
    elif os.path.exists(pending_path):
        raw = open(pending_path, encoding='utf-8').read()
    else:
        raw = ""
    doc_content = limpar_linhas_em_branco(raw)

    if os.path.exists(tech_official_path):
        raw_tech = open(tech_official_path, encoding='utf-8').read()
    elif os.path.exists(tech_pending_path):
        raw_tech = open(tech_pending_path, encoding='utf-8').read()
    else:
        raw_tech = ""
    tech_content = limpar_linhas_em_branco(raw_tech)

    pendente      = os.path.exists(pending_path)
    pendente_tech = os.path.exists(tech_pending_path)

    if request.method == 'POST':
        user_name_session = session.get('user_name', 'Anônimo')

        # 1) Atualiza metadados
        modulo['nome']           = request.form['nome']
        modulo['descricao']      = request.form['descricao']
        modulo['icone']          = request.form['icone']
        modulo['palavras_chave'] = [
            k.strip() for k in request.form['palavras_chave'].split(',') if k.strip()
        ]
        modulo['relacionados'] = [
            k.strip() for k in request.form['relacionados'].split(',') if k.strip()
        ]

        # 2) Lê + limpa novo Markdown
        novo_conteudo      = limpar_linhas_em_branco(request.form['doc_content'])
        novo_conteudo_tech = limpar_linhas_em_branco(request.form['tech_content'])

        # 3) Salva direto (com backup)  
        salvar_edicao_modulo_com_tecnico(
            modulo, novo_conteudo, novo_conteudo_tech, user_name_session
        )

        # 4) Feedback
        # flash("Alteração aprovada e publicada!", "success")
        return redirect(url_for('.editor_index', token=token))

    return render_template(
        'editor/module_edit.html',
        modulo=modulo,
        doc_content=doc_content,
        tech_content=tech_content,
        token=token,
        pendente=pendente,
        pendente_tech=pendente_tech
    )

@editor_bp.route('/novo', methods=['GET', 'POST'])
def criar_modulo():
    # <<< INÍCIO DA VERIFICAÇÃO DE PERMISSÃO >>>
    grupo, user_name = get_user_group()
    perms = load_permissions().get('can_create_modules', {})
    allowed = (grupo in perms.get('groups', []) or user_name in perms.get('users', []))
    if not allowed:
        return render_template('access_denied.html', reason="Você não tem permissão para criar novos módulos."), 403
    # <<< FIM DA VERIFICAÇÃO DE PERMISSÃO >>>

    token = request.args.get('token', '')
    if request.method == 'POST':
        user_name_session = session.get('user_name', 'Anônimo')
        mid = request.form['id']
        nome = request.form['nome']
        descricao = request.form['descricao']
        icone = request.form['icone']
        palavras_chave = [k.strip() for k in request.form['palavras_chave'].split(',') if k.strip()]
        relacionados = [k.strip() for k in request.form['relacionados'].split(',') if k.strip()]
        agora = datetime.now().isoformat()

        # ATUALIZADO: Estrutura completa do novo módulo com versionamento
        novo_modulo = {
            "id": mid,
            "nome": nome,
            "descricao": descricao,
            "icone": icone,
            "palavras_chave": palavras_chave,
            "relacionados": relacionados,
            "status": "aprovado", # Começa como aprovado
            "version_info": {
                "current_version": "1.0",
                "last_approved_by": user_name_session, # O criador é o primeiro "aprovador"
                "last_approved_on": agora
            },
            "pending_edit_info": { # Nenhuma edição pendente ao criar
                "user": None,
                "data": None
            },
            "edit_history": [ # O primeiro evento do histórico é a criação
                {
                    "event": "criado",
                    "version": "1.0",
                    "user": user_name_session,
                    "timestamp": agora
                }
            ]
        }

        # Limpa quebras antes de salvar
        doc_content = limpar_linhas_em_branco(request.form.get('doc_content', '# Novo módulo\n'))
        tech_content = limpar_linhas_em_branco(request.form.get('tech_content', '# Documentação técnica inicial\n'))

        # Atualiza config.json
        with open(CONFIG_FILE, "r", encoding='utf-8') as f:
            config = json.load(f)
        config['modulos'].append(novo_modulo)
        with open(CONFIG_FILE, "w", encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        # Salva os arquivos de documentação iniciais (sem pendência)
        path_mod = os.path.join(DATA_DIR, mid)
        os.makedirs(path_mod, exist_ok=True)
        with open(os.path.join(path_mod, "documentation.md"), "w", encoding="utf-8") as f:
            f.write(doc_content)
        with open(os.path.join(path_mod, "technical_documentation.md"), "w", encoding="utf-8") as f:
            f.write(tech_content)

        return redirect(url_for('.editor_index', token=token))

    return render_template('editor/module_new.html', token=token)

@editor_bp.route('/options', methods=['GET'])
def editor_options():
    # 1) Módulos do config.json
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    modules = [{'id': m['id'], 'nome': m['nome']} for m in cfg.get('modulos', [])]

    # 2) Ícones
    icons_file = os.path.join(BASE_DIR, 'data', 'icons.json')
    if os.path.exists(icons_file):
        with open(icons_file, 'r', encoding='utf-8') as f:
            icons = json.load(f)
    else:
        icons = [
            'bi-alarm','bi-bag','bi-gear','bi-activity',
            'bi-chat-dots','bi-code','bi-file-earmark-text',
            'bi-graph-up','bi-lock','bi-people'
        ]

    # 3) Sugestões de keywords
    keywords = ['tutorial','referência','exemplo','guia','API','como usar']
    
    return jsonify({
        'modules':   modules,
        'icons':     icons,
        'keywords':  keywords
    })


@editor_bp.route('/delete/<mid>', methods=['POST'])
def delete_modulo(mid):
    # <<< INÍCIO DA VERIFICAÇÃO DE PERMISSÃO >>>
    grupo, user_name = get_user_group()
    # Usando a permissão 'can_delete_modules' para esta ação específica
    perms = load_permissions().get('can_delete_modules', {})
    allowed = (grupo in perms.get('groups', []) or user_name in perms.get('users', []))
    if not allowed:
        return render_template('access_denied.html', reason="Você não tem permissão para deletar módulos."), 403
    # <<< FIM DA VERIFICAÇÃO DE PERMISSÃO >>>

    token = request.args.get('token', '')

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    modulos = config.get('modulos', [])
    novos = [m for m in modulos if m['id'] != mid]
    
    if len(novos) == len(modulos):
        flash(f"Módulo {mid} não encontrado.", "warning")
    else:
        config['modulos'] = novos
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        # Remove arquivos/diretório do módulo
        mod_path = os.path.join(DATA_DIR, mid)
        if os.path.isdir(mod_path):
            shutil.rmtree(mod_path)
            
        # Remove também as imagens desse módulo
        img_path = os.path.join(BASE_DIR, 'data', 'img', mid)
        if os.path.isdir(img_path):
            shutil.rmtree(img_path)

        # flash(f"Módulo {mid} deletado com sucesso!", "success")

    return redirect(url_for('.editor_index', token=token))

def get_pending_count():
    """Conta e retorna o número de módulos com pendências."""
    modulos, _ = carregar_modulos()
    count = 0
    for m in modulos:
        mod_id = m['id']
        path_mod = os.path.join(DATA_DIR, mod_id)
        # Verifica se existe um arquivo de pendência normal OU técnico
        if os.path.exists(os.path.join(path_mod, "pending_documentation.md")) or \
           os.path.exists(os.path.join(path_mod, "pending_technical_documentation.md")):
            count += 1
    return count

@editor_bp.route('/pendentes')
def pendentes():
    # <<< INÍCIO DA VERIFICAÇÃO DE PERMISSÃO >>>
    grupo, user_name = get_user_group()
    perms = load_permissions().get('can_module_control', {})
    allowed = (grupo in perms.get('groups', []) or user_name in perms.get('users', []))
    if not allowed:
        return render_template('access_denied.html', reason="Você não tem permissão para visualizar ou gerenciar pendências."), 403
    # <<< FIM DA VERIFICAÇÃO DE PERMISSÃO >>>

    token = request.args.get('token', '')
    modulos, _ = carregar_modulos()
    lista_pendentes = [] # Usando um novo nome de variável para clareza
    
    for m in modulos:
        mod_id = m['id']
        path_mod = os.path.join(DATA_DIR, mod_id)
        pend_doc_path = os.path.join(path_mod, "pending_documentation.md")
        pend_tech_path = os.path.join(path_mod, "pending_technical_documentation.md")
        
        pendente_normal = os.path.exists(pend_doc_path)
        pendente_tecnico = os.path.exists(pend_tech_path)

        # Se houver qualquer pendência, adiciona à lista
        if pendente_normal or pendente_tecnico:
            # Pega o nome do editor de forma segura a partir de 'pending_edit_info'
            editor_info = m.get('pending_edit_info', {})
            editor_name = editor_info.get('user', 'N/A') # 'N/A' como fallback

            lista_pendentes.append({
                "modulo": m,
                "editor": editor_name, # <-- Adiciona o nome do editor diretamente aqui
                "pendente_normal": pendente_normal,
                "pendente_tecnico": pendente_tecnico
            })
            
    return render_template(
        'editor/pending.html',
        pendentes=lista_pendentes, # Passa a lista preparada para o template
        token=token
    )

def render_diff_html(old, new):
    dmp = dmp_module.diff_match_patch()
    diffs = dmp.diff_main(old, new)
    dmp.diff_cleanupSemantic(diffs)
    html = ""
    for (op, data) in diffs:
        safe = markdown.markdown(data) if data.strip() else ""
        if op == dmp.DIFF_INSERT:
            html += f'<mark style="background:#d4fcbc">{safe}</mark>'
        elif op == dmp.DIFF_DELETE:
            html += f'<mark style="background:#ffe6e6;text-decoration:line-through;">{safe}</mark>'
        else:
            html += safe
    return html

@editor_bp.route('/diff_pendente')
def diff_pendente():
    # <<< INÍCIO DA VERIFICAÇÃO DE PERMISSÃO >>>
    grupo, user_name = get_user_group()
    perms = load_permissions().get('can_module_control', {})
    allowed = (grupo in perms.get('groups', []) or user_name in perms.get('users', []))
    if not allowed:
        return jsonify({'error': 'Acesso negado. Você não tem permissão para visualizar esta diferença.'}), 403
    # <<< FIM DA VERIFICAÇÃO DE PERMISSÃO >>>

    mid = request.args.get('mid')
    path_mod = os.path.join(DATA_DIR, mid)
    doc_path = os.path.join(path_mod, "documentation.md")
    pend_doc_path = os.path.join(path_mod, "pending_documentation.md")
    tech_path = os.path.join(path_mod, "technical_documentation.md")
    pend_tech_path = os.path.join(path_mod, "pending_technical_documentation.md")

    def get_text(path):
        if os.path.exists(path):
            with open(path, encoding='utf-8') as f:
                return f.read()
        return ""

    doc = get_text(doc_path)
    pend_doc = get_text(pend_doc_path)
    tech = get_text(tech_path)
    pend_tech = get_text(pend_tech_path)

    doc_html_left = render_diff_html(doc, pend_doc) if doc or pend_doc else "<em>Não disponível</em>"
    doc_html_right = render_diff_html(pend_doc, doc) if doc or pend_doc else "<em>Não disponível</em>"
    tech_html_left = render_diff_html(tech, pend_tech) if tech or pend_tech else "<em>Não disponível</em>"
    tech_html_right = render_diff_html(pend_tech, tech) if tech or pend_tech else "<em>Não disponível</em>"

    return jsonify({
        "doc_html_left": doc_html_left,
        "doc_html_right": doc_html_right,
        "tech_html_left": tech_html_left,
        "tech_html_right": tech_html_right
    })

@editor_bp.route('/aprovar/<mid>', methods=['POST'])
def aprovar(mid):
    # <<< INÍCIO DA VERIFICAÇÃO DE PERMISSÃO >>>
    grupo, user_name_approver = get_user_group() # Este é o usuário que está APROVANDO
    perms = load_permissions().get('can_module_control', {})
    allowed = (grupo in perms.get('groups', []) or user_name_approver in perms.get('users', []))
    if not allowed:
        return render_template('access_denied.html', reason="Você não tem permissão para aprovar alterações."), 403
    # <<< FIM DA VERIFICAÇÃO DE PERMISSÃO >>>

    token = request.args.get('token', '')
    modulos, _ = carregar_modulos()
    modulo = get_modulo_by_id(modulos, mid)
    path_mod = os.path.join(DATA_DIR, mid)
    
    pending_path = os.path.join(path_mod, "pending_documentation.md")
    official_path = os.path.join(path_mod, "documentation.md")
    tech_pending_path = os.path.join(path_mod, "pending_technical_documentation.md")
    tech_official_path = os.path.join(path_mod, "technical_documentation.md")
    
    # Pega o nome do usuário que EDITOU (que estava na pendência)
    editor_info = modulo.get('pending_edit_info', {})
    user_name_editor = editor_info.get('user', 'Desconhecido')

    # Lógica de versionamento (ex: 1.0 -> 1.1, 1.9 -> 2.0)
    versao_atual = modulo.get('version_info', {}).get('current_version', '1.0').split('.')
    major, minor = int(versao_atual[0]), int(versao_atual[1])
    minor += 1
    # if minor >= 10: # Opcional: fazer bump da versão major
    #     major += 1
    #     minor = 0
    nova_versao = f"{major}.{minor}"
    agora = datetime.now()
    data_str = agora.strftime("%Y-%m-%dT%H-%M-%S")
    
    # Cria backups nomeados com a nova versão
    history_dir = os.path.join(path_mod, "history")
    os.makedirs(history_dir, exist_ok=True)
    backup_name, backup_name_tech = None, None
    if os.path.exists(official_path):
        backup_name = f"v{nova_versao}_{data_str}_{user_name_approver}_documentation.md"
        shutil.copyfile(official_path, os.path.join(history_dir, backup_name))
    if os.path.exists(tech_official_path):
        backup_name_tech = f"v{nova_versao}_{data_str}_{user_name_approver}_technical.md"
        shutil.copyfile(tech_official_path, os.path.join(history_dir, backup_name_tech))

    # Move os arquivos pendentes para oficiais
    if os.path.exists(pending_path):
        shutil.move(pending_path, official_path)
    if os.path.exists(tech_pending_path):
        shutil.move(tech_pending_path, tech_official_path)

    # ATUALIZADO: Atualiza o dicionário completo do módulo
    modulo['status'] = 'aprovado'
    modulo['version_info'] = {
        "current_version": nova_versao,
        "last_approved_by": user_name_approver,
        "last_approved_on": agora.isoformat()
    }
    modulo['pending_edit_info'] = {"user": None, "data": None} # Limpa a pendência
    
    if 'edit_history' not in modulo:
        modulo['edit_history'] = []
    
    # Adiciona o evento de aprovação ao histórico, incluindo quem editou e quem aprovou
    modulo['edit_history'].append({
        "event": "aprovado",
        "version": nova_versao,
        "editor": user_name_editor,
        "approver": user_name_approver,
        "timestamp": agora.isoformat(),
        "backup_file_doc": backup_name,
        "backup_file_tech": backup_name_tech
    })
    
    # Salva as alterações no config.json
    with open(CONFIG_FILE, "r", encoding='utf-8') as f:
        config = json.load(f)
    for idx, m in enumerate(config['modulos']):
        if m['id'] == mid:
            config['modulos'][idx] = modulo
            break
    with open(CONFIG_FILE, "w", encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    return redirect(url_for('editor.pendentes', token=token))

@editor_bp.route('/rejeitar/<mid>', methods=['POST'])
def rejeitar(mid):
    # <<< INÍCIO DA VERIFICAÇÃO DE PERMISSÃO >>>
    grupo, user_name_rejecter = get_user_group() # Este é o usuário que está REJEITANDO
    perms = load_permissions().get('can_module_control', {})
    allowed = (grupo in perms.get('groups', []) or user_name_rejecter in perms.get('users', []))
    if not allowed:
        return render_template('access_denied.html', reason="Você não tem permissão para rejeitar alterações."), 403
    # <<< FIM DA VERIFICAÇÃO DE PERMISSÃO >>>

    token = request.args.get('token', '')
    modulos, _ = carregar_modulos()
    modulo = get_modulo_by_id(modulos, mid)
    path_mod = os.path.join(DATA_DIR, mid)
    pending_path = os.path.join(path_mod, "pending_documentation.md")
    tech_pending_path = os.path.join(path_mod, "pending_technical_documentation.md")

    # Pega o nome do usuário que EDITOU (cuja edição foi rejeitada)
    editor_info = modulo.get('pending_edit_info', {})
    user_name_editor = editor_info.get('user', 'Desconhecido')

    if os.path.exists(pending_path):
        os.remove(pending_path)
    if os.path.exists(tech_pending_path):
        os.remove(tech_pending_path)

    # ATUALIZADO: Atualiza o status e limpa a pendência
    modulo['status'] = 'aprovado' # Volta ao estado anterior
    modulo['pending_edit_info'] = {"user": None, "data": None}
    
    if 'edit_history' not in modulo:
        modulo['edit_history'] = []

    # Adiciona o evento de rejeição ao histórico
    modulo['edit_history'].append({
        "event": "rejeitado",
        "editor": user_name_editor,
        "rejecter": user_name_rejecter,
        "timestamp": datetime.now().isoformat()
    })

    with open(CONFIG_FILE, "r", encoding='utf-8') as f:
        config = json.load(f)
    for idx, m in enumerate(config['modulos']):
        if m['id'] == mid:
            config['modulos'][idx] = modulo
            break
    with open(CONFIG_FILE, "w", encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    return redirect(url_for('editor.pendentes', token=token))

@editor_bp.route('/historico/<mid>', methods=['GET', 'POST'])
def historico_modulo(mid):
    """
    MODIFICADO: A lógica de restauração (POST) foi refeita para:
    1. Fazer backup da versão vigente antes de sobrescrever.
    2. Atualizar o 'version_info' no config.json para refletir a versão restaurada.
    3. Adicionar um evento 'restaurado' no 'edit_history' para auditoria completa.
    """
    # <<< INÍCIO DA VERIFICAÇÃO DE PERMISSÃO >>>
    grupo, user_name = get_user_group()
    perms = load_permissions().get('can_versioning_modules', {})
    allowed = (grupo in perms.get('groups', []) or user_name in perms.get('users', []))
    if not allowed:
        return render_template('access_denied.html', reason="Você não tem permissão para acessar o histórico de versões."), 403
    # <<< FIM DA VERIFICAÇÃO DE PERMISSÃO >>>

    token = request.args.get('token', '')
    modulos, _ = carregar_modulos()
    modulo = get_modulo_by_id(modulos, mid)
    if not modulo:
        abort(404)

    path_mod = os.path.join(DATA_DIR, mid)
    history_dir = os.path.join(path_mod, "history")
    
    # --- LÓGICA DE RESTAURAÇÃO (POST) ATUALIZADA ---
    if request.method == 'POST':
        versao_filename = request.form.get('versao_filename')
        tipo = request.form.get('tipo')  # 'doc' ou 'tech'
        
        if not versao_filename or not tipo:
            flash('Informações de restauração incompletas.', 'danger')
            return redirect(url_for('editor.historico_modulo', mid=mid, token=token))

        vigente_path = os.path.join(path_mod, "documentation.md" if tipo == 'doc' else "technical_documentation.md")
        versao_path = os.path.join(history_dir, versao_filename)

        if os.path.exists(versao_path):
            agora = datetime.now()
            
            # 1. Fazer backup da versão atual antes de sobrescrevê-la (segurança)
            if os.path.exists(vigente_path):
                backup_vigente_name = f"{agora.strftime('%Y-%m-%dT%H-%M-%S')}_backup_antes_da_restauracao.md"
                shutil.copyfile(vigente_path, os.path.join(history_dir, backup_vigente_name))

            # 2. Restaurar o arquivo da versão escolhida
            shutil.copyfile(versao_path, vigente_path)

            # 3. Extrair a informação da versão do nome do arquivo (ex: 'v1.2_...')
            try:
                versao_restaurada = versao_filename.split('_')[0].replace('v', '')
            except IndexError:
                versao_restaurada = "desconhecida"

            # 4. Atualizar o estado do módulo no dicionário
            modulo['version_info']['current_version'] = versao_restaurada
            modulo['version_info']['last_approved_by'] = user_name # O restaurador é o "aprovador" deste estado
            modulo['version_info']['last_approved_on'] = agora.isoformat()
            
            # 5. Adicionar um evento de "restaurado" ao histórico
            if 'edit_history' not in modulo:
                modulo['edit_history'] = []
            modulo['edit_history'].append({
                "event": "restaurado",
                "version": versao_restaurada,
                "restorer": user_name,
                "timestamp": agora.isoformat(),
                "restored_from_file": versao_filename
            })
            
            # 6. Salvar o config.json atualizado
            with open(CONFIG_FILE, "r", encoding='utf-8') as f:
                config = json.load(f)
            for idx, m in enumerate(config['modulos']):
                if m['id'] == mid:
                    config['modulos'][idx] = modulo
                    break
            with open(CONFIG_FILE, "w", encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            flash(f'Módulo revertido para a versão {versao_restaurada} com sucesso!', 'success')
        else:
            flash('Arquivo de versão não encontrado.', 'danger')
        
        return redirect(url_for('editor.historico_modulo', mid=mid, token=token))

    # --- LÓGICA DE EXIBIÇÃO (GET) - SEM ALTERAÇÕES ---
    historico_eventos = sorted(modulo.get('edit_history', []), key=lambda x: x['timestamp'], reverse=True)

    official_path = os.path.join(path_mod, "documentation.md")
    tech_official_path = os.path.join(path_mod, "technical_documentation.md")
    vigente = open(official_path, encoding='utf-8').read() if os.path.exists(official_path) else ""
    vigente_tech = open(tech_official_path, encoding='utf-8').read() if os.path.exists(tech_official_path) else ""

    return render_template(
        'editor/historical_module.html',
        modulo=modulo,
        historico_eventos=historico_eventos,
        vigente=vigente,
        vigente_tech=vigente_tech,
        token=token
    )

@editor_bp.route('/diff_historico')
def diff_historico():
    """
    Gera um diff entre dois arquivos de backup do histórico.
    """
    # Verificação de permissão
    grupo, user_name = get_user_group()
    perms = load_permissions().get('can_versioning_modules', {})
    if not (grupo in perms.get('groups', []) or user_name in perms.get('users', [])):
        return jsonify({'error': 'Acesso negado.'}), 403

    # Obtenção dos parâmetros
    mid = request.args.get('mid')
    file1 = request.args.get('file1')
    file2 = request.args.get('file2')

    if not all([mid, file1, file2]):
        return jsonify({'error': 'Parâmetros ausentes para a comparação.'}), 400

    history_dir = os.path.join(DATA_DIR, mid, "history")
    path1 = os.path.join(history_dir, secure_filename(file1))
    path2 = os.path.join(history_dir, secure_filename(file2))

    if not os.path.exists(path1) or not os.path.exists(path2):
        return jsonify({'error': 'Um ou mais arquivos da versão não foram encontrados.'}), 404
        
    with open(path1, 'r', encoding='utf-8') as f1, open(path2, 'r', encoding='utf-8') as f2:
        content1 = f1.read()
        content2 = f2.read()

    # Gera o diff no formato necessário para a biblioteca diff2html
    dmp = dmp_module.diff_match_patch()
    diffs = dmp.diff_main(content1, content2)
    dmp.diff_cleanupSemantic(diffs)
    
    # A biblioteca diff2html espera um formato de patch, então criamos um
    patch = dmp.patch_make(content1, diffs)
    diff_text = dmp.patch_toText(patch)

    return jsonify({'diff': diff_text})

@editor_bp.route('/get_historical_content')
def get_historical_content():
    # ... (código de permissão e obtenção de parâmetros) ...
    mid = request.args.get('mid')
    filename = request.args.get('filename')

    if not mid or not filename:
        print(f"!!! ERRO: Parâmetros ausentes! mid={mid}, filename={filename}") # DEBUG
        return jsonify({'error': 'Parâmetros ausentes (módulo ou nome do arquivo).'}), 400

    history_dir = os.path.join(DATA_DIR, mid, "history")
    filepath = os.path.join(history_dir, secure_filename(filename))
    
    print(f"--- DEBUG: Tentando ler o arquivo: {filepath}") # DEBUG

    if not os.path.exists(filepath):
        print(f"!!! ERRO: Arquivo não encontrado em {filepath}") # DEBUG
        return jsonify({'error': 'Arquivo da versão histórica não encontrado.'}), 404
        
    with open(filepath, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    print(f"--- DEBUG: Conteúdo Markdown Lido (tamanho: {len(markdown_content)})") # DEBUG
    
    html_content = markdown.markdown(markdown_content, extensions=['fenced_code', 'tables'])
    
    print(f"--- DEBUG: Conteúdo HTML Gerado (tamanho: {len(html_content)})") # DEBUG

    return jsonify({'html': html_content})