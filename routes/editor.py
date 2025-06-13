# routes/editor.py

from flask import Blueprint, render_template, request, redirect, url_for, abort, session, flash, jsonify
from werkzeug.utils import secure_filename
from utils.data.module_utils import carregar_modulos, get_modulo_by_id
from utils.auth.menu_required import menu_required
from config import DATA_DIR, CONFIG_FILE, BASE_DIR
import os
import re
import json
import shutil
from datetime import datetime

editor_bp = Blueprint('editor', __name__, url_prefix='/editor')

def limpar_linhas_em_branco(md):
    # Remove TODAS as linhas em branco (inclusive entre parágrafos)
    return re.sub(r'\n\\n', 's*', md)

def processar_e_salvar_imagens(markdown, modulo_id, token):
    """
    Move imagens usadas do tmp para a pasta oficial.
    Ajusta os links no markdown para o novo caminho.
    Retorna o markdown ajustado.
    """
    # Regex que captura todas as imagens do tmp deste token/modulo
    padrao = re.compile(r'\!\[.*?\]\(/data/tmp_img_uploads/' + re.escape(token) + '/' + re.escape(modulo_id) + r'/([^)]+)\)')
    img_dir = os.path.join(BASE_DIR, 'data', 'img', modulo_id)
    os.makedirs(img_dir, exist_ok=True)

    def mover(match):
        nome_arquivo = match.group(1)
        origem = os.path.join(BASE_DIR, 'data', 'tmp_img_uploads', token, modulo_id, nome_arquivo)
        destino = os.path.join(img_dir, nome_arquivo)
        if os.path.exists(origem):
            shutil.move(origem, destino)
        # Retorna o novo link
        return f'![{nome_arquivo}](\/data\/img\/{modulo_id}\/{nome_arquivo})'

    markdown_novo = padrao.sub(mover, markdown)
    return markdown_novo

def salvar_edicao_modulo(modulo, novo_conteudo, user_name, user_permission):
    mod_id = modulo['id']
    path_mod = os.path.join(DATA_DIR, mod_id)
    os.makedirs(path_mod, exist_ok=True)

    pending_path = os.path.join(path_mod, "pending_documentation.md")
    official_path = os.path.join(path_mod, "documentation.md")

    if user_permission != "MASTER":
        with open(pending_path, "w", encoding="utf-8") as f:
            f.write(novo_conteudo)
        modulo['status'] = 'pendente'
        modulo['ultima_edicao'] = {"user": user_name, "data": datetime.now().isoformat()}
    else:
        # backup oficial
        if os.path.exists(official_path):
            history_dir = os.path.join(path_mod, "history")
            os.makedirs(history_dir, exist_ok=True)
            backup_name = datetime.now().strftime("%Y-%m-%dT%H-%M-%S") + f"_{user_name}.md"
            backup_path = os.path.join(history_dir, backup_name)
            shutil.copyfile(official_path, backup_path)
        with open(official_path, "w", encoding="utf-8") as f:
            f.write(novo_conteudo)
        modulo['status'] = 'aprovado'
        modulo['ultima_edicao'] = {"user": user_name, "data": datetime.now().isoformat()}
        if os.path.exists(pending_path):
            os.remove(pending_path)

    with open(CONFIG_FILE, "r", encoding='utf-8') as f:
        config = json.load(f)
    for idx, m in enumerate(config['modulos']):
        if m['id'] == mod_id:
            config['modulos'][idx] = modulo
            break
    with open(CONFIG_FILE, "w", encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def salvar_edicao_modulo_com_tecnico(modulo, novo_conteudo, novo_conteudo_tech, user_name, user_permission):
    mod_id = modulo['id']
    path_mod = os.path.join(DATA_DIR, mod_id)
    os.makedirs(path_mod, exist_ok=True)

    # PRINCIPAL
    pending_path = os.path.join(path_mod, "pending_documentation.md")
    official_path = os.path.join(path_mod, "documentation.md")
    # TÉCNICO
    tech_pending_path = os.path.join(path_mod, "pending_technical_documentation.md")
    tech_official_path = os.path.join(path_mod, "technical_documentation.md")

    if user_permission != "MASTER":
        with open(pending_path, "w", encoding="utf-8") as f:
            f.write(novo_conteudo)
        with open(tech_pending_path, "w", encoding="utf-8") as f:
            f.write(novo_conteudo_tech)
        modulo['status'] = 'pendente'
        modulo['ultima_edicao'] = {"user": user_name, "data": datetime.now().isoformat()}
    else:
        # backup oficial
        history_dir = os.path.join(path_mod, "history")
        os.makedirs(history_dir, exist_ok=True)
        nowstr = datetime.now().strftime("%Y-%m-%dT%H-%M-%S") + f"_{user_name}"
        if os.path.exists(official_path):
            shutil.copyfile(official_path, os.path.join(history_dir, nowstr + "_documentation.md"))
        if os.path.exists(tech_official_path):
            shutil.copyfile(tech_official_path, os.path.join(history_dir, nowstr + "_technical.md"))
        with open(official_path, "w", encoding="utf-8") as f:
            f.write(novo_conteudo)
        with open(tech_official_path, "w", encoding="utf-8") as f:
            f.write(novo_conteudo_tech)
        modulo['status'] = 'aprovado'
        modulo['ultima_edicao'] = {"user": user_name, "data": datetime.now().isoformat()}
        if os.path.exists(pending_path): os.remove(pending_path)
        if os.path.exists(tech_pending_path): os.remove(tech_pending_path)

    with open(CONFIG_FILE, "r", encoding='utf-8') as f:
        config = json.load(f)
    for idx, m in enumerate(config['modulos']):
        if m['id'] == mod_id:
            config['modulos'][idx] = modulo
            break
    with open(CONFIG_FILE, "w", encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def adm_required(func):
    def wrapper(*args, **kwargs):
        if session.get('permission') != 'ADM' and session.get('permission') != 'MASTER':
            abort(403)
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

def master_required(func):
    def wrapper(*args, **kwargs):
        if session.get('permission') != 'MASTER':
            abort(403)
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@editor_bp.route('/')
@menu_required('seguranca')
def editor_index():
    token = request.args.get('token', '')
    modulos, _ = carregar_modulos()
    return render_template(
        'editor/editor_index.html',
        modulos=modulos,
        token=token,
        menus=session.get('menus', [])
    )

@editor_bp.route('/upload_image/<modulo_id>', methods=['POST'])
@menu_required('seguranca')
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

    # Pasta de destino permanente: data/img/<modulo_id>/
    dest_dir = os.path.join(BASE_DIR, 'data', 'img', modulo_id)
    os.makedirs(dest_dir, exist_ok=True)

    # Padroniza o nome do arquivo para "img.png" (ou mantém a extensão original)
    filename = f"img{ext}"
    safe_name = secure_filename(filename)
    file_path = os.path.join(dest_dir, safe_name)

    # Salva o arquivo na pasta de destino
    file.save(file_path)

    # Retorna o link público (ajuste a rota estática conforme sua configuração)
    return jsonify({
        'url': f'/data/img/{modulo_id}/{safe_name}'
    })

@editor_bp.route('/upload_video/<modulo_id>', methods=['POST'])
@menu_required('seguranca')
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

    # Pasta de destino: data/videos/<modulo_id>/
    dest_dir = os.path.join(BASE_DIR, 'data', 'videos', modulo_id)
    os.makedirs(dest_dir, exist_ok=True)

    # Nome seguro e único para o vídeo
    filename = secure_filename(file.filename)
    file_path = os.path.join(dest_dir, filename)

    # Salva o arquivo na pasta de destino
    file.save(file_path)

    # Retorna o link público
    return jsonify({
        'url': f'/data/videos/{modulo_id}/{filename}',
        'type': f'video/{ext[1:]}'
    })

@editor_bp.route('/upload_anexo', methods=['POST'])
@menu_required('seguranca')
def upload_anexo():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    file = request.files['file']
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    dest_folder = os.path.join(BASE_DIR, 'data', 'downloads', 'docs')
    os.makedirs(dest_folder, exist_ok=True)
    file_path = os.path.join(dest_folder, filename)
    file.save(file_path)
    url = f'/download?token=__TOKEN_PLACEHOLDER__&download={filename}'
    return jsonify({'url': url})


@editor_bp.route('/modulo/<mid>', methods=['GET', 'POST'])
@menu_required('seguranca')
def editar_modulo(mid):
    token = request.args.get('token', '')
    modulos, _ = carregar_modulos()
    modulo = get_modulo_by_id(modulos, mid)
    if not modulo:
        abort(404)

    path_mod = os.path.join(DATA_DIR, mid)
    official_path = os.path.join(path_mod, "documentation.md")
    pending_path = os.path.join(path_mod, "pending_documentation.md")
    tech_official_path = os.path.join(path_mod, "technical_documentation.md")
    tech_pending_path = os.path.join(path_mod, "pending_technical_documentation.md")

    # Lê conteúdo (prioriza pendente, depois oficial)
    doc_content = ""
    if os.path.exists(pending_path):
        doc_content = open(pending_path, encoding='utf-8').read()
    elif os.path.exists(official_path):
        doc_content = open(official_path, encoding='utf-8').read()

    tech_content = ""
    if os.path.exists(tech_pending_path):
        tech_content = open(tech_pending_path, encoding='utf-8').read()
    elif os.path.exists(tech_official_path):
        tech_content = open(tech_official_path, encoding='utf-8').read()

    pendente = os.path.exists(pending_path)
    pendente_tech = os.path.exists(tech_pending_path)

    if request.method == 'POST':
        user_name = session.get('user_name', 'Anônimo')
        user_permission = session.get('permission', '')

        # 1) Atualiza metadados do módulo
        modulo['nome'] = request.form['nome']
        modulo['descricao'] = request.form['descricao']
        modulo['icone'] = request.form['icone']
        modulo['palavras_chave'] = [
            k.strip() for k in request.form['palavras_chave'].split(',') if k.strip()
        ]
        modulo['relacionados'] = [
            k.strip() for k in request.form['relacionados'].split(',') if k.strip()
        ]

        # 2) Lê o novo conteúdo Markdown e limpa linhas em branco duplicadas
        novo_conteudo = limpar_linhas_em_branco(request.form['doc_content'])
        novo_conteudo_tech = limpar_linhas_em_branco(request.form['tech_content'])

        # 3) Salva arquivos e também persiste o módulo atualizado no config.json
        salvar_edicao_modulo_com_tecnico(
            modulo, novo_conteudo, novo_conteudo_tech, user_name, user_permission
        )

        flash(
            "Alteração salva! (aguardando aprovação)" 
            if user_permission != "MASTER" 
            else "Alteração aprovada e publicada!"
        )
        return redirect(url_for('.editor_index', token=token))

    return render_template(
        'editor/modulo_edit.html',
        modulo=modulo,
        doc_content=doc_content,
        tech_content=tech_content,
        token=token,
        pendente=pendente,
        pendente_tech=pendente_tech
    )

@editor_bp.route('/options', methods=['GET'])
@menu_required('seguranca')
def editor_options():
    """
    Retorna:
      - modules: lista de {id, nome} para preencher o select de relacionados
      - icons: array de strings (classes do Bootstrap Icons) para o datalist
      - keywords: array de sugestões de palavras‐chave
    """
    # 1) Módulos do config.json
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    modules = [
        {'id': m['id'], 'nome': m['nome']}
        for m in cfg.get('modulos', [])
    ]

    # 2) Ícones (pode vir de um arquivo icons.json em config/ ou de lista fixa)
    icons_file = os.path.join(BASE_DIR, 'data', 'icons.json')
    if os.path.exists(icons_file):
        with open(icons_file, 'r', encoding='utf-8') as f:
            icons = json.load(f)
    else:
        # fallback básico
        icons = [
            'bi-alarm','bi-bag','bi-gear','bi-activity',
            'bi-chat-dots','bi-code','bi-file-earmark-text',
            'bi-graph-up','bi-lock','bi-people'
        ]

    # 3) Sugestões de keywords
    keywords = ['tutorial','referência','exemplo','guia','API','como usar']

    return jsonify({
        'modules': modules,
        'icons': icons,
        'keywords': keywords
    })

@editor_bp.route('/novo', methods=['GET', 'POST'])
@menu_required('seguranca')
def criar_modulo():
    token = request.args.get('token', '')
    if request.method == 'POST':
        user_name = session.get('user_name', 'Anônimo')
        user_permission = session.get('permission', '')
        mid = request.form['id']
        nome = request.form['nome']
        descricao = request.form['descricao']
        icone = request.form['icone']
        palavras_chave = [k.strip() for k in request.form['palavras_chave'].split(',')]
        relacionados = [k.strip() for k in request.form['relacionados'].split(',') if k.strip()]
        novo_modulo = {
            "id": mid,
            "nome": nome,
            "descricao": descricao,
            "icone": icone,
            "palavras_chave": palavras_chave,
            "relacionados": relacionados,
            # Sempre pendente, a não ser que seja MASTER criando
            "status": "aprovado" if user_permission == "MASTER" else "pendente",
            "ultima_edicao": {"user": user_name, "data": datetime.now().isoformat()}
        }
        doc_content = limpar_linhas_em_branco(request.form.get('doc_content', '# Novo módulo\n'))
        tech_content = limpar_linhas_em_branco(request.form.get('tech_content', '# Documentação técnica inicial\n'))

        # 1. Adiciona o novo módulo ao config.json
        with open(CONFIG_FILE, "r", encoding='utf-8') as f:
            config = json.load(f)
        config['modulos'].append(novo_modulo)
        with open(CONFIG_FILE, "w", encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        # 2. Salva arquivos (com aprovação ou pendência)
        salvar_edicao_modulo_com_tecnico(novo_modulo, doc_content, tech_content, user_name, user_permission)

        if user_permission == "MASTER":
            flash("Módulo criado e publicado!")
        else:
            flash("Módulo criado! Aguarda aprovação do MASTER.")

        return redirect(url_for('.editor_index', token=token))
    return render_template('editor/modulo_novo.html', token=token)

@editor_bp.route('/delete/<mid>', methods=['POST'])
@menu_required('seguranca')
def delete_modulo(mid):
    token = request.args.get('token', '')

    # 1. Carrega config
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    # 2. Remove o módulo do JSON
    modulos = config.get('modulos', [])
    novos = [m for m in modulos if m['id'] != mid]
    if len(novos) == len(modulos):
        flash(f"Módulo {mid} não encontrado.", "warning")
    else:
        config['modulos'] = novos
        # 3. Salva o config atualizado
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        # 4. Remove arquivos/diretório do módulo (docs, pendências, history…)
        mod_path = os.path.join(DATA_DIR, mid)
        if os.path.isdir(mod_path):
            shutil.rmtree(mod_path)

        # 5. Remove também as imagens desse módulo
        img_path = os.path.join(BASE_DIR, 'data', 'img', mid)
        if os.path.isdir(img_path):
            shutil.rmtree(img_path)

        flash(f"Módulo {mid} deletado com sucesso!", "success")

    return redirect(url_for('.editor_index', token=token))


# Lista de pendências (apenas MASTER)
@editor_bp.route('/pendentes')
@menu_required('parametros')
def pendentes():
    token = request.args.get('token', '')
    modulos, _ = carregar_modulos()
    pendentes = []
    for m in modulos:
        if m.get('status') == 'pendente':
            mod_id = m['id']
            pending_path = os.path.join(DATA_DIR, mod_id, "pending_documentation.md")
            official_path = os.path.join(DATA_DIR, mod_id, "documentation.md")
            tech_pending_path = os.path.join(DATA_DIR, mod_id, "pending_technical_documentation.md")
            tech_official_path = os.path.join(DATA_DIR, mod_id, "technical_documentation.md")
            m['pending_content'] = open(pending_path, encoding='utf-8').read() if os.path.exists(pending_path) else ""
            m['official_content'] = open(official_path, encoding='utf-8').read() if os.path.exists(official_path) else ""
            m['pending_tech_content'] = open(tech_pending_path, encoding='utf-8').read() if os.path.exists(tech_pending_path) else ""
            m['official_tech_content'] = open(tech_official_path, encoding='utf-8').read() if os.path.exists(tech_official_path) else ""
            pendentes.append(m)
    return render_template('editor/pendentes.html', pendentes=pendentes, token=token)

# Aprovar pendência
@editor_bp.route('/aprovar/<mid>', methods=['POST'])
@menu_required('parametros')
def aprovar(mid):
    token = request.args.get('token', '')
    modulos, _ = carregar_modulos()
    modulo = get_modulo_by_id(modulos, mid)
    path_mod = os.path.join(DATA_DIR, mid)
    pending_path = os.path.join(path_mod, "pending_documentation.md")
    official_path = os.path.join(path_mod, "documentation.md")
    user_name = session.get("user_name", "MASTER")
    # backup oficial
    if os.path.exists(official_path):
        history_dir = os.path.join(path_mod, "history")
        os.makedirs(history_dir, exist_ok=True)
        backup_name = datetime.now().strftime("%Y-%m-%dT%H-%M-%S") + f"_{user_name}.md"
        backup_path = os.path.join(history_dir, backup_name)
        shutil.copyfile(official_path, backup_path)
    # aprova pendente
    if os.path.exists(pending_path):
        shutil.move(pending_path, official_path)
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
    flash("Aprovação concluída!")
    return redirect(url_for('editor.pendentes', token=token))

# Rejeitar pendência
@editor_bp.route('/rejeitar/<mid>', methods=['POST'])
@menu_required('parametros')
def rejeitar(mid):
    token = request.args.get('token', '')
    modulos, _ = carregar_modulos()
    modulo = get_modulo_by_id(modulos, mid)
    path_mod = os.path.join(DATA_DIR, mid)
    pending_path = os.path.join(path_mod, "pending_documentation.md")
    if os.path.exists(pending_path):
        os.remove(pending_path)
    modulo['status'] = 'aprovado'
    with open(CONFIG_FILE, "r", encoding='utf-8') as f:
        config = json.load(f)
    for idx, m in enumerate(config['modulos']):
        if m['id'] == mid:
            config['modulos'][idx] = modulo
            break
    with open(CONFIG_FILE, "w", encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    flash("Pendência rejeitada.")
    return redirect(url_for('editor.pendentes', token=token))

@editor_bp.route('/historico/<mid>', methods=['GET', 'POST'])
@menu_required('parametros')
def historico_modulo(mid):
    token = request.args.get('token', '')
    path_mod = os.path.join(DATA_DIR, mid)
    history_dir = os.path.join(path_mod, "history")
    official_path = os.path.join(path_mod, "documentation.md")
    tech_official_path = os.path.join(path_mod, "technical_documentation.md")

    # Lista arquivos de histórico
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

    # POST: definir vigente
    if request.method == 'POST':
        tipo = request.form.get('tipo')
        versao = request.form.get('versao')
        if tipo == 'doc':
            vigente_path = official_path
            historico_list = historicos
        else:
            vigente_path = tech_official_path
            historico_list = historicos_tech

        versao_path = os.path.join(history_dir, versao)
        if os.path.exists(versao_path):
            # Salva vigente atual no histórico ANTES de trocar
            if os.path.exists(vigente_path):
                with open(vigente_path, encoding='utf-8') as f:
                    atual = f.read()
                data = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
                if tipo == 'doc':
                    backup_name = f"{data}_vigente.md"
                else:
                    backup_name = f"tech_{data}_vigente.md"
                backup_path = os.path.join(history_dir, backup_name)
                with open(backup_path, "w", encoding="utf-8") as f:
                    f.write(atual)
            # Troca vigente
            shutil.copyfile(versao_path, vigente_path)
            flash(f'Versão selecionada agora é a vigente ({ "Documentação Técnica" if tipo=="tech" else "Documentação" })!', 'success')
        else:
            flash('Arquivo de versão não encontrado.', 'danger')
        return redirect(url_for('editor.historico_modulo', mid=mid, token=token))

    # Carrega as vigentes atuais
    vigente = ''
    vigente_tech = ''
    if os.path.exists(official_path):
        with open(official_path, encoding='utf-8') as f:
            vigente = f.read()
    if os.path.exists(tech_official_path):
        with open(tech_official_path, encoding='utf-8') as f:
            vigente_tech = f.read()

    return render_template(
        'editor/historico_modulo.html',
        mid=mid,
        historicos=historicos,
        historicos_tech=historicos_tech,
        vigente=vigente,
        vigente_tech=vigente_tech,
        token=token
    )