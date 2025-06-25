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
    marca status como 'pendente'.
    """
    mod_id    = modulo['id']
    path_mod  = os.path.join(DATA_DIR, mod_id)
    os.makedirs(path_mod, exist_ok=True)

    # 1) Salva both pending files
    with open(os.path.join(path_mod, "pending_documentation.md"), "w", encoding="utf-8") as f:
        f.write(novo_conteudo)
    with open(os.path.join(path_mod, "pending_technical_documentation.md"), "w", encoding="utf-8") as f:
        f.write(novo_conteudo_tech)

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

@editor_bp.route('/')
def editor_index():
    # 2. Carrega flags de permissão vindas da sessão
    grupo, user_name = get_user_group()
    user_perms = session.get('permissions', {})
    can_edit_modules             = user_perms.get('can_edit_modules', False)
    can_delete_modules              = user_perms.get('can_delete_modules', False)
    can_versioning_modules   = user_perms.get('can_versioning_modules', False)
    can_module_control = user_perms.get('can_module_control', False)

    # FUNÇÃO E OBTÉM A CONTAGEM DE PENDENCIAS
    num_pendencias = get_pending_count()

    token = request.args.get('token', '')
    modulos, _ = carregar_modulos()
    return render_template(
        'editor/editor_index.html',
        modulos=modulos,
        token=token,
        can_edit_modules=can_edit_modules,
        can_delete_modules=can_delete_modules,
        can_versioning_modules=can_versioning_modules,
        can_module_control=can_module_control,
        num_pendencias=num_pendencias,
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
    token = request.args.get('token', '')
    modulos, _ = carregar_modulos()
    modulo = get_modulo_by_id(modulos, mid)
    if not modulo:
        abort(404)

    path_mod = os.path.join(DATA_DIR, mid)
    official_path      = os.path.join(path_mod, "documentation.md")
    pending_path       = os.path.join(path_mod, "pending_documentation.md")
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
        user_name = session.get('user_name', 'Anônimo')

        # 1) Atualiza metadados
        modulo['nome']          = request.form['nome']
        modulo['descricao']     = request.form['descricao']
        modulo['icone']         = request.form['icone']
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
            modulo, novo_conteudo, novo_conteudo_tech, user_name
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
    token = request.args.get('token', '')
    if request.method == 'POST':
        user_name = session.get('user_name', 'Anônimo')
        mid        = request.form['id']
        nome       = request.form['nome']
        descricao  = request.form['descricao']
        icone      = request.form['icone']
        palavras_chave = [k.strip() for k in request.form['palavras_chave'].split(',') if k.strip()]
        relacionados   = [k.strip() for k in request.form['relacionados'].split(',') if k.strip()]

        novo_modulo = {
            "id": mid,
            "nome": nome,
            "descricao": descricao,
            "icone": icone,
            "palavras_chave": palavras_chave,
            "relacionados": relacionados,
            "status": "aprovado",
            "ultima_edicao": {"user": user_name, "data": datetime.now().isoformat()}
        }

        # Limpa quebras antes de salvar
        doc_content  = limpar_linhas_em_branco(request.form.get('doc_content', '# Novo módulo\n'))
        tech_content = limpar_linhas_em_branco(request.form.get('tech_content', '# Documentação técnica inicial\n'))

        # Atualiza config.json
        with open(CONFIG_FILE, "r", encoding='utf-8') as f:
            config = json.load(f)
        config['modulos'].append(novo_modulo)
        with open(CONFIG_FILE, "w", encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        # Salva arquivos com backup
        salvar_edicao_modulo_com_tecnico(novo_modulo, doc_content, tech_content, user_name)

        # flash("Módulo criado e publicado!", "success")
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

# Lista de pendências (agora visível para todos, mas provavelmente estará sempre vazia)
@editor_bp.route('/pendentes')
def pendentes():
    token = request.args.get('token', '')
    modulos, _ = carregar_modulos()
    pendentes = []
    for m in modulos:
        mod_id = m['id']
        path_mod = os.path.join(DATA_DIR, mod_id)
        pend_doc = os.path.join(path_mod, "pending_documentation.md")
        pend_tech = os.path.join(path_mod, "pending_technical_documentation.md")
        pendente_normal = os.path.exists(pend_doc)
        pendente_tecnico = os.path.exists(pend_tech)
        if pendente_normal or pendente_tecnico:
            pendentes.append({
                "modulo": m,
                "pendente_normal": pendente_normal,
                "pendente_tecnico": pendente_tecnico
            })
    return render_template(
        'editor/pending.html',
        pendentes=pendentes,
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

    # Sempre mostra os dois lados, com destaque nas diferenças
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

# Aprovar pendência (agora visível para todos)
@editor_bp.route('/aprovar/<mid>', methods=['POST'])
def aprovar(mid):
    token = request.args.get('token', '')
    modulos, _ = carregar_modulos()
    modulo = get_modulo_by_id(modulos, mid)
    path_mod = os.path.join(DATA_DIR, mid)
    pending_path = os.path.join(path_mod, "pending_documentation.md")
    official_path = os.path.join(path_mod, "documentation.md")
    tech_pending_path = os.path.join(path_mod, "pending_technical_documentation.md")
    tech_official_path = os.path.join(path_mod, "technical_documentation.md")
    user_name = session.get("user_name", "Anônimo")

    # Backup dos vigentes
    history_dir = os.path.join(path_mod, "history")
    os.makedirs(history_dir, exist_ok=True)
    data = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    if os.path.exists(official_path):
        backup_name = f"{data}_{user_name}_documentation.md"
        backup_path = os.path.join(history_dir, backup_name)
        shutil.copyfile(official_path, backup_path)
    if os.path.exists(tech_official_path):
        backup_name_tech = f"{data}_{user_name}_technical.md"
        backup_path_tech = os.path.join(history_dir, backup_name_tech)
        shutil.copyfile(tech_official_path, backup_path_tech)

    # Aprova ambos se existirem
    if os.path.exists(pending_path):
        shutil.move(pending_path, official_path)
    if os.path.exists(tech_pending_path):
        shutil.move(tech_pending_path, tech_official_path)

    modulo['status'] = 'aprovado'
    modulo['ultima_edicao'] = {"user": user_name, "data": datetime.now().isoformat()}

    with open(CONFIG_FILE, "r", encoding='utf-8') as f:
        config = json.load(f)
    for idx, m in enumerate(config['modulos']):
        if m['id'] == mid:
            config['modulos'][idx] = modulo
            break
    with open(CONFIG_FILE, "w", encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    # flash("Aprovação concluída!")
    return redirect(url_for('editor.pendentes', token=token))

# Rejeitar pendência (agora visível para todos)
@editor_bp.route('/rejeitar/<mid>', methods=['POST'])
def rejeitar(mid):
    token = request.args.get('token', '')
    modulos, _ = carregar_modulos()
    modulo = get_modulo_by_id(modulos, mid)
    path_mod = os.path.join(DATA_DIR, mid)
    pending_path = os.path.join(path_mod, "pending_documentation.md")
    tech_pending_path = os.path.join(path_mod, "pending_technical_documentation.md")

    # Remove ambos se existirem
    if os.path.exists(pending_path):
        os.remove(pending_path)
    if os.path.exists(tech_pending_path):
        os.remove(tech_pending_path)

    modulo['status'] = 'aprovado'
    with open(CONFIG_FILE, "r", encoding='utf-8') as f:
        config = json.load(f)
    for idx, m in enumerate(config['modulos']):
        if m['id'] == mid:
            config['modulos'][idx] = modulo
            break
    with open(CONFIG_FILE, "w", encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    # flash("Pendência rejeitada.")
    return redirect(url_for('editor.pendentes', token=token))

@editor_bp.route('/historico/<mid>', methods=['GET', 'POST'])
def historico_modulo(mid):
    # A lógica desta rota permanece a mesma, mas agora está acessível a todos.
    token = request.args.get('token', '')
    path_mod = os.path.join(DATA_DIR, mid)
    history_dir = os.path.join(path_mod, "history")
    official_path = os.path.join(path_mod, "documentation.md")
    tech_official_path = os.path.join(path_mod, "technical_documentation.md")

    historicos = []
    historicos_tech = []
    if os.path.isdir(history_dir):
        for fname in sorted(os.listdir(history_dir), reverse=True):
            fpath = os.path.join(history_dir, fname)
            if fname.endswith('_documentation.md'):
                with open(fpath, encoding='utf-8') as f:
                    content = f.read()
                historicos.append({'filename': fname, 'content': content})
            elif fname.endswith('_technical.md'):
                with open(fpath, encoding='utf-8') as f:
                    content = f.read()
                historicos_tech.append({'filename': fname, 'content': content})

    if request.method == 'POST':
        tipo = request.form.get('tipo')
        versao = request.form.get('versao')
        if tipo == 'doc':
            vigente_path = official_path
        else:
            vigente_path = tech_official_path

        versao_path = os.path.join(history_dir, versao)
        if os.path.exists(versao_path):
            # Salva vigente atual no histórico antes de trocar
            if os.path.exists(vigente_path):
                data = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
                if tipo == 'doc':
                    backup_name = f"{data}_vigente_documentation.md"
                else:
                    backup_name = f"{data}_vigente_technical.md"
                backup_path = os.path.join(history_dir, backup_name)
                shutil.copyfile(vigente_path, backup_path)
            # Troca vigente
            shutil.copyfile(versao_path, vigente_path)
            #flash(f'Versão selecionada agora é a vigente!', 'success')
        else:
            flash('Arquivo de versão não encontrado.', 'danger')
        return redirect(url_for('editor.historico_modulo', mid=mid, token=token))

    vigente = open(official_path, encoding='utf-8').read() if os.path.exists(official_path) else ""
    vigente_tech = open(tech_official_path, encoding='utf-8').read() if os.path.exists(tech_official_path) else ""

    return render_template(
        'editor/historical_module.html',
        mid=mid,
        historicos=historicos,
        historicos_tech=historicos_tech,
        vigente=vigente,
        vigente_tech=vigente_tech,
        token=token
    )
