# routes/editor.py (Versão Final e Completa com SQLAlchemy)

from flask import Blueprint, render_template, request, redirect, url_for, abort, session, flash, jsonify
from werkzeug.utils import secure_filename
import os
import re
import json
import markdown
import diff_match_patch as dmp_module
import shutil
from datetime import datetime
from pathlib import Path
import uuid

# --- Importações Refatoradas ---
# Remove get_db e importa os modelos e a sessão do SQLAlchemy
from Models import db, Modulo, PalavraChave, HistoricoEdicao
# Importa as funções de utilitários já refatoradas
from Utils.data.module_utils import get_modulo_by_id, carregar_modulos
# Importa a função de verificação de permissão refatorada
from Routes.API.Permissions import check_permission as has_perm
from Config import DATA_DIR, BASE_DIR, IMAGES_DIR, VIDEOS_DIR, ICONS_FILE, DOCS_DOWNLOAD_DIR
editor_bp = Blueprint('editor', __name__, url_prefix='/editor')


# --- Funções Auxiliares (Lógica de arquivos e texto, sem alteração de DB) ---

def limpar_linhas_em_branco(md: str) -> str:
    """Normaliza quebras de linha e remove espaços extras."""
    if not md: return ""
    text = md.replace('\r\n', '\n').rstrip()
    return re.sub(r'\n{3,}', '\n\n', text)

def get_pending_count():
    """Conta e retorna o número de módulos com status 'pendente' usando o ORM."""
    return Modulo.query.filter_by(status='pendente').count()

def carregar_template_documentacao():
    """Carrega o conteúdo do template de documentação padrão."""
    try:
        # Ajustado para um caminho mais provável
        path = os.path.join(DATA_DIR, 'templates', 'template_documentation.md')
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "# Documentação do Módulo\n"

def carregar_template_tecnico():
    """Carrega o conteúdo do template de documentação técnica."""
    try:
        # Ajustado para um caminho mais provável
        path = os.path.join(DATA_DIR, 'templates', 'template_technical_documentation.md')
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "# Documentação Técnica\n"

def render_diff_html(old, new):
    """Renderiza a diferença entre dois textos como HTML."""
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

def build_dir_tree(path):
    """Cria uma árvore de diretórios em formato de dicionário."""
    tree = {}
    for item in os.scandir(path):
        if item.is_dir():
            tree[item.name] = build_dir_tree(item.path)
    return tree

# --- Rotas Principais do Editor ---

@editor_bp.route('/')
def editor_index():
    """Página principal do editor, listando todos os módulos."""
    if not has_perm('can_access_editor').get_json().get('allowed'):
        abort(403, "Acesso negado ao editor.")

    token = request.args.get('token', '')
    modulos, _ = carregar_modulos()
    num_pendencias = get_pending_count()
    user_perms = session.get('permissions', {})

    return render_template(
        'Editor/EDT_ModuleList.html',
        modulos=modulos,
        token=token,
        num_pendencias=num_pendencias,
        can_delete_modules=user_perms.get('can_delete_modules', False),
        can_versioning_modules=user_perms.get('can_versioning_modules', False),
        can_module_control=user_perms.get('can_module_control', False),
        can_create_modules=user_perms.get('can_create_modules', False)
    )

@editor_bp.route('/novo', methods=['GET', 'POST'])
def criar_modulo():
    """Rota para criar um novo módulo."""
    if not has_perm('can_create_modules').get_json().get('allowed'):
        abort(403, "Você não tem permissão para criar novos módulos.")

    token = request.args.get('token', '')
    
    if request.method == 'POST':
        mid = request.form['id'].strip().lower().replace(" ", "-")
        
        if Modulo.query.get(mid):
            flash(f"O ID de módulo '{mid}' já existe. Por favor, escolha outro.", "danger")
            return redirect(url_for('.criar_modulo', token=token))

        try:
            agora = datetime.now().isoformat()
            user_name = session.get('user_name', 'Anônimo')

            novo_modulo = Modulo(
                id=mid, nome=request.form['nome'], descricao=request.form['descricao'],
                icone=request.form['icone'], status='aprovado', current_version='1.0',
                last_approved_by=user_name, last_approved_on=agora
            )

            palavras_chave_str = request.form['palavras_chave']
            palavras_chave = [k.strip() for k in palavras_chave_str.split(',') if k.strip()]
            for p in palavras_chave:
                novo_modulo.palavras_chave.append(PalavraChave(palavra=p))

            relacionados_str = request.form['relacionados']
            relacionados_ids = [k.strip() for k in relacionados_str.split(',') if k.strip()]
            if relacionados_ids:
                novo_modulo.relacionados = Modulo.query.filter(Modulo.id.in_(relacionados_ids)).all()

            novo_modulo.edit_history.append(HistoricoEdicao(
                event='criado', version='1.0', editor=user_name, timestamp=agora
            ))
            
            db.session.add(novo_modulo)
            db.session.commit()

            # Lógica de salvar arquivos .md
            path_mod = os.path.join(DATA_DIR, mid)
            os.makedirs(path_mod, exist_ok=True)
            doc_content = limpar_linhas_em_branco(request.form.get('doc_content') or carregar_template_documentacao())
            tech_content = limpar_linhas_em_branco(request.form.get('tech_content') or carregar_template_tecnico())
            with open(os.path.join(path_mod, "documentation.md"), "w", encoding="utf-8") as f: f.write(doc_content)
            with open(os.path.join(path_mod, "technical_documentation.md"), "w", encoding="utf-8") as f: f.write(tech_content)

            flash(f"Módulo '{mid}' criado com sucesso!", "success")
            return redirect(url_for('.editor_index', token=token))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao criar o módulo: {e}", "danger")

    return render_template('Editor/EDT_ModuleNew.html', token=token, 
        doc_content=carregar_template_documentacao(), tech_content=carregar_template_tecnico())

@editor_bp.route('/modulo/<mid>', methods=['GET', 'POST'])
def editar_modulo(mid):
    if not has_perm('can_edit_modules').get_json().get('allowed'):
        abort(403, "Você não tem permissão para editar módulos.")

    token = request.args.get('token', '')
    modulo_obj = Modulo.query.get_or_404(mid)

    if request.method == 'POST':
        try:
            modulo_obj.nome = request.form['nome']
            modulo_obj.descricao = request.form['descricao']
            modulo_obj.icone = request.form['icone']
            modulo_obj.status = 'pendente'
            modulo_obj.pending_edit_user = session.get('user_name', 'Anônimo')
            modulo_obj.pending_edit_data = datetime.now().isoformat()

            novas_palavras = {k.strip() for k in request.form['palavras_chave'].split(',') if k.strip()}
            modulo_obj.palavras_chave = [PalavraChave(palavra=p) for p in novas_palavras]

            novos_relacionados_ids = {k.strip() for k in request.form['relacionados'].split(',') if k.strip()}
            modulo_obj.relacionados = Modulo.query.filter(Modulo.id.in_(novos_relacionados_ids)).all()

            db.session.commit()

            path_mod = os.path.join(DATA_DIR, mid)
            os.makedirs(path_mod, exist_ok=True)
            with open(os.path.join(path_mod, "pending_documentation.md"), "w", encoding="utf-8") as f: f.write(limpar_linhas_em_branco(request.form['doc_content']))
            with open(os.path.join(path_mod, "pending_technical_documentation.md"), "w", encoding="utf-8") as f: f.write(limpar_linhas_em_branco(request.form['tech_content']))

            flash("Alteração enviada para aprovação!", "success")
            return redirect(url_for('.editor_index', token=token))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao salvar o módulo: {e}", "danger")

    path_mod = os.path.join(DATA_DIR, mid)
    doc_content, tech_content = "", ""
    pending_path = os.path.join(path_mod, "pending_documentation.md")
    official_path = os.path.join(path_mod, "documentation.md")
    tech_pending_path = os.path.join(path_mod, "pending_technical_documentation.md")
    tech_official_path = os.path.join(path_mod, "technical_documentation.md")

    if os.path.exists(pending_path):
        with open(pending_path, encoding='utf-8') as f: doc_content = f.read()
    elif os.path.exists(official_path):
        with open(official_path, encoding='utf-8') as f: doc_content = f.read()

    if os.path.exists(tech_pending_path):
        with open(tech_pending_path, encoding='utf-8') as f: tech_content = f.read()
    elif os.path.exists(tech_official_path):
        with open(tech_official_path, encoding='utf-8') as f: tech_content = f.read()
        
    return render_template('Editor/EDT_ModuleEdit.html', modulo=get_modulo_by_id(mid), doc_content=doc_content, tech_content=tech_content, token=token)

@editor_bp.route('/delete/<mid>', methods=['POST'])
def delete_modulo(mid):
    if not has_perm('can_delete_modules').get_json().get('allowed'):
        abort(403, "Você não tem permissão para deletar módulos.")

    token = request.args.get('token', '')
    modulo = Modulo.query.get_or_404(mid)

    try:
        db.session.delete(modulo)
        db.session.commit()

        mod_path = os.path.join(DATA_DIR, mid)
        if os.path.isdir(mod_path): shutil.rmtree(mod_path)
        img_path  = IMAGES_DIR / mid
        if os.path.isdir(img_path): shutil.rmtree(img_path)

        flash(f"Módulo {mid} deletado com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao deletar o módulo: {e}", "danger")
        
    return redirect(url_for('.editor_index', token=token))

@editor_bp.route('/pendentes')
def pendentes():
    if not has_perm('can_module_control').get_json().get('allowed'):
        abort(403, "Você não tem permissão para gerenciar pendências.")

    token = request.args.get('token', '')
    
    modulos_pendentes_obj = Modulo.query.filter_by(status='pendente').all()
    
    lista_pendentes = []
    for modulo in modulos_pendentes_obj:
        lista_pendentes.append({
            "modulo": modulo,
            "editor": modulo.pending_edit_user or 'N/A'
        })

    return render_template('Editor/EDT_Pendings.html', pendentes=lista_pendentes, token=token)

@editor_bp.route('/aprovar/<mid>', methods=['POST'])
def aprovar(mid):
    if not has_perm('can_module_control').get_json().get('allowed'):
        abort(403, "Você não tem permissão para aprovar alterações.")

    token = request.args.get('token', '')
    modulo = Modulo.query.get_or_404(mid)
    
    try:
        agora = datetime.now()
        user_name_approver = session.get('user_name', 'Anônimo')
        user_name_editor = modulo.pending_edit_user or 'Desconhecido'

        major, minor = map(int, modulo.current_version.split('.'))
        nova_versao = f"{major}.{minor + 1}"

        path_mod = os.path.join(DATA_DIR, mid)
        history_dir = os.path.join(path_mod, "history")
        os.makedirs(history_dir, exist_ok=True)
        
        pending_path = os.path.join(path_mod, "pending_documentation.md")
        official_path = os.path.join(path_mod, "documentation.md")
        tech_pending_path = os.path.join(path_mod, "pending_technical_documentation.md")
        tech_official_path = os.path.join(path_mod, "technical_documentation.md")

        backup_name, backup_name_tech = None, None
        if os.path.exists(pending_path):
            if os.path.exists(official_path):
                backup_name = f"v{nova_versao}_{agora.strftime('%Y-%m-%dT%H-%M-%S')}_doc.md"
                shutil.copyfile(official_path, os.path.join(history_dir, backup_name))
            shutil.move(pending_path, official_path)

        if os.path.exists(tech_pending_path):
            if os.path.exists(tech_official_path):
                backup_name_tech = f"v{nova_versao}_{agora.strftime('%Y-%m-%dT%H-%M-%S')}_tech.md"
                shutil.copyfile(tech_official_path, os.path.join(history_dir, backup_name_tech))
            shutil.move(tech_pending_path, tech_official_path)

        modulo.status = 'aprovado'
        modulo.current_version = nova_versao
        modulo.last_approved_by = user_name_approver
        modulo.last_approved_on = agora.isoformat()
        modulo.pending_edit_user = None
        modulo.pending_edit_data = None

        hist_aprovacao = HistoricoEdicao(
            event='aprovado', version=nova_versao, editor=user_name_editor,
            approver=user_name_approver, timestamp=agora.isoformat(),
            backup_file_doc=backup_name, backup_file_tech=backup_name_tech
        )
        modulo.edit_history.append(hist_aprovacao)
        
        db.session.commit()
        flash(f"Alterações no módulo '{mid}' aprovadas com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao aprovar o módulo: {e}", "danger")

    return redirect(url_for('editor.pendentes', token=token))

@editor_bp.route('/rejeitar/<mid>', methods=['POST'])
def rejeitar(mid):
    if not has_perm('can_module_control').get_json().get('allowed'):
        abort(403, "Você não tem permissão para rejeitar alterações.")

    token = request.args.get('token', '')
    modulo = Modulo.query.get_or_404(mid)

    try:
        user_name_editor = modulo.pending_edit_user or 'Desconhecido'
        
        pending_path = os.path.join(DATA_DIR, mid, "pending_documentation.md")
        tech_pending_path = os.path.join(DATA_DIR, mid, "pending_technical_documentation.md")
        if os.path.exists(pending_path): os.remove(pending_path)
        if os.path.exists(tech_pending_path): os.remove(tech_pending_path)

        modulo.status = 'aprovado'
        modulo.pending_edit_user = None
        modulo.pending_edit_data = None
        
        hist_rejeicao = HistoricoEdicao(
            event='rejeitado', editor=user_name_editor,
            approver=session.get('user_name', 'Anônimo'), timestamp=datetime.now().isoformat()
        )
        modulo.edit_history.append(hist_rejeicao)

        db.session.commit()
        flash(f"Alteração pendente para o módulo '{mid}' foi rejeitada.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao rejeitar o módulo: {e}", "danger")

    return redirect(url_for('editor.pendentes', token=token))

@editor_bp.route('/historico/<mid>', methods=['GET', 'POST'])
def historico_modulo(mid):
    if not has_perm('can_versioning_modules').get_json().get('allowed'):
        abort(403, "Você não tem permissão para acessar o histórico de versões.")

    token = request.args.get('token', '')
    modulo_dict = get_modulo_by_id(mid)
    if not modulo_dict:
        abort(404)

    if request.method == 'POST':
        try:
            versao_filename = request.form.get('versao_filename')
            tipo = request.form.get('tipo')
            user_name = session.get('user_name', 'Anônimo')
            agora = datetime.now()

            path_mod = os.path.join(DATA_DIR, mid)
            history_dir = os.path.join(path_mod, "history")
            vigente_path = os.path.join(path_mod, "documentation.md" if tipo == 'doc' else "technical_documentation.md")
            versao_path = os.path.join(history_dir, versao_filename)

            if os.path.exists(versao_path):
                if os.path.exists(vigente_path):
                    backup_name = f"{agora.strftime('%Y-%m-%dT%H-%M-%S')}_backup_before_restore.md"
                    shutil.copyfile(vigente_path, os.path.join(history_dir, backup_name))
                
                shutil.copyfile(versao_path, vigente_path)
                versao_restaurada = versao_filename.split('_')[0].replace('v', '')

                modulo_obj = Modulo.query.get(mid)
                modulo_obj.current_version = versao_restaurada
                modulo_obj.last_approved_by = user_name
                modulo_obj.last_approved_on = agora.isoformat()

                hist_restauracao = HistoricoEdicao(
                    event='restaurado', version=versao_restaurada, editor=user_name,
                    timestamp=agora.isoformat(),
                    backup_file_doc=versao_filename if tipo == 'doc' else None,
                    backup_file_tech=versao_filename if tipo == 'tech' else None
                )
                modulo_obj.edit_history.append(hist_restauracao)
                
                db.session.commit()
                flash(f'Módulo revertido para a versão {versao_restaurada} com sucesso!', 'success')
            else:
                flash('Arquivo de versão não encontrado.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao restaurar a versão: {e}", "danger")
        
        return redirect(url_for('.historico_modulo', mid=mid, token=token))

    historico_eventos = sorted(modulo_dict.get('edit_history', []), key=lambda x: x['timestamp'], reverse=True)
    return render_template('Editor/HistoricalModule.html', modulo=modulo_dict, historico_eventos=historico_eventos, token=token)

@editor_bp.route('/options', methods=['GET'])
def editor_options():
    modules_db = Modulo.query.with_entities(Modulo.id, Modulo.nome).order_by(Modulo.nome).all()
    modules = [{'id': row.id, 'nome': row.nome} for row in modules_db]

    icons_file = ICONS_FILE
    try:
        with open(icons_file, 'r', encoding='utf-8') as f:
            icons = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        icons = ['bi-alarm', 'bi-bag', 'bi-gear', 'bi-activity']

    keywords = ['tutorial', 'referência', 'exemplo', 'guia', 'API', 'como usar']
    
    return jsonify({'modules': modules, 'icons': icons, 'keywords': keywords})

@editor_bp.route('/upload_image/<modulo_id>', methods=['POST'])
def upload_image(modulo_id):
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400

    file = request.files['file']
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
        return jsonify({'error': 'Formato não suportado'}), 400

    dest_dir = IMAGES_DIR / modulo_id
    os.makedirs(dest_dir, exist_ok=True)

    i = 1
    while True:
        filename = f"img{i}{ext}"
        safe_name = secure_filename(filename)
        file_path = os.path.join(dest_dir, safe_name)
        if not os.path.exists(file_path):
            break
        i += 1

    file.save(file_path)

    # >>> AQUI: gera a URL COM prefixo (/luft-docs/data/img/...)
    img_url = url_for(
        'index.serve_imagem_dinamica',
        nome_arquivo=f'{modulo_id}/{safe_name}',
        _external=False  # path relativo; use True se quiser URL absoluta
    )
    return jsonify({'url': img_url})

@editor_bp.route('/upload_video/<modulo_id>', methods=['POST'])
def upload_video(modulo_id):
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400

    file = request.files['file']
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.mp4', '.webm', '.ogg']:
        return jsonify({'error': 'Formato de vídeo não suportado'}), 400

    dest_dir = VIDEOS_DIR / modulo_id
    os.makedirs(dest_dir, exist_ok=True)

    filename = secure_filename(file.filename)
    file_path = os.path.join(dest_dir, filename)
    file.save(file_path)

    # --- CORRIGIDO: agora respeita a base /luft-docs ---
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

    dest_folder = DOCS_DOWNLOAD_DIR
    os.makedirs(dest_folder, exist_ok=True)

    file_path = os.path.join(dest_folder, filename)
    file.save(file_path)

    # --- CORRIGIDO: inclui /luft-docs na rota de download ---
    url = f'/download?token=__TOKEN_PLACEHOLDER__&download={filename}'
    return jsonify({'url': url})

@editor_bp.route('/submodulos')
def listar_submodulos():
    token = request.args.get('token', '')
    global_dir = Path(BASE_DIR) / 'data' / 'global'
    global_dir.mkdir(exist_ok=True)

    submodulos_info = []
    for p in global_dir.rglob('*.md'):
        mod_time_unix = os.path.getmtime(p)
        mod_time_str = datetime.fromtimestamp(mod_time_unix).strftime('%d/%m/%Y %H:%M:%S')
        submodulos_info.append({
            'path': p.relative_to(global_dir).as_posix(),
            'modified': mod_time_str
        })
    submodulos_info.sort(key=lambda x: x['path'])

    dir_tree = build_dir_tree(global_dir)
    return render_template(
        'Editor/EDT_SubModuleList.html',
        submodulos=submodulos_info,
        dir_tree_json=json.dumps(dir_tree),
        token=token
    )


@editor_bp.route('/deletar_submodulo', methods=['POST'])
def deletar_submodulo():
    token = request.form.get('token')
    if not token:
        return "Não autorizado", 403

    path_to_delete = request.form.get('path_to_delete')
    if not path_to_delete:
        flash('Caminho do arquivo não fornecido.', 'danger')
        return redirect(url_for('.listar_submodulos', token=token))

    global_dir = Path(BASE_DIR) / 'data' / 'global'
    full_path = global_dir.joinpath(path_to_delete).resolve()

    # Segurança: impede path traversal
    if global_dir.resolve() not in full_path.parents:
        flash('Tentativa de exclusão de arquivo inválida.', 'danger')
        return redirect(url_for('.listar_submodulos', token=token))

    try:
        if full_path.is_file():
            full_path.unlink()
            flash(f'Submódulo "{path_to_delete}" deletado com sucesso.', 'success')
            # Limpa pastas vazias acima
            parent = full_path.parent
            while parent != global_dir and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent
        else:
            flash('O caminho especificado não é um arquivo válido.', 'warning')
    except Exception as e:
        flash(f'Erro ao deletar o arquivo: {e}', 'danger')

    return redirect(url_for('.listar_submodulos', token=token))


@editor_bp.route('/criar_submodulo', methods=['POST'])
def criar_submodulo():
    token = request.form.get('token')
    if not token:
        return "Não autorizado", 403

    folder_path = request.form.get('folder_path', '').strip()
    file_name = request.form.get('file_name', '').strip()

    if not file_name:
        flash('O nome do arquivo é obrigatório.', 'danger')
        return redirect(url_for('.listar_submodulos', token=token))

    # Sanitiza nome e caminho
    file_name = file_name.replace('.md', '').replace('/', '').replace('\\', '')
    if '..' in folder_path or folder_path.startswith('/'):
        flash('Caminho de pasta inválido.', 'danger')
        return redirect(url_for('.listar_submodulos', token=token))

    global_dir = Path(BASE_DIR) / 'data' / 'global'
    target_dir = global_dir.joinpath(folder_path) if folder_path and folder_path != '.' else global_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    final_path = target_dir / f"{file_name}.md"
    if final_path.exists():
        flash(f'O arquivo "{file_name}.md" já existe. Abrindo para edição.', 'info')
    else:
        final_path.touch()
        flash(f'Submódulo "{file_name}.md" criado com sucesso!', 'success')

    # ATENÇÃO: padronizado para submodulo_path
    submodulo_path = final_path.relative_to(global_dir).as_posix()
    return redirect(url_for('.editar_submodulo', submodulo_path=submodulo_path, token=token))


@editor_bp.route('/submodulo/<path:submodulo_path>', methods=['GET', 'POST'])
def editar_submodulo(submodulo_path):
    token = request.args.get('token', '')
    global_dir = Path(BASE_DIR) / 'data' / 'global'
    file_path = global_dir / submodulo_path

    if request.method == 'POST':
        content = limpar_linhas_em_branco(request.form.get('content', ''))
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        flash('Submódulo salvo com sucesso!', 'success')
        return redirect(url_for('.listar_submodulos', token=token))

    content = file_path.read_text(encoding='utf-8') if file_path.exists() else ""
    return render_template(
        'Editor/EDT_SubModuleEdit.html',
        path=submodulo_path,
        content=content,
        token=token
    )


@editor_bp.route('/diff_pendente')
def diff_pendente():
    if not has_perm('can_module_control').get_json().get('allowed'):
        return jsonify({'error': 'Acesso negado.'}), 403

    mid = request.args.get('mid')
    path_mod = os.path.join(DATA_DIR, mid)

    def get_text(path):
        return open(path, encoding='utf-8').read() if os.path.exists(path) else ""

    doc = get_text(os.path.join(path_mod, "documentation.md"))
    pend_doc = get_text(os.path.join(path_mod, "pending_documentation.md"))
    tech = get_text(os.path.join(path_mod, "technical_documentation.md"))
    pend_tech = get_text(os.path.join(path_mod, "pending_technical_documentation.md"))

    return jsonify({
        "doc_html_left": render_diff_html(doc, pend_doc),
        "doc_html_right": render_diff_html(pend_doc, doc),
        "tech_html_left": render_diff_html(tech, pend_tech),
        "tech_html_right": render_diff_html(pend_tech, tech)
    })


@editor_bp.route('/diff_historico')
def diff_historico():
    if not has_perm('can_versioning_modules').get_json().get('allowed'):
        return jsonify({'error': 'Acesso negado.'}), 403

    mid = request.args.get('mid')
    file1 = request.args.get('file1')
    file2 = request.args.get('file2')
    if not all([mid, file1, file2]):
        return jsonify({'error': 'Parâmetros ausentes.'}), 400

    history_dir = os.path.join(DATA_DIR, mid, "history")
    path1 = os.path.join(history_dir, secure_filename(file1))
    path2 = os.path.join(history_dir, secure_filename(file2))
    if not os.path.exists(path1) or not os.path.exists(path2):
        return jsonify({'error': 'Arquivos não encontrados.'}), 404

    with open(path1, 'r', encoding='utf-8') as f1, open(path2, 'r', encoding='utf-8') as f2:
        content1, content2 = f1.read(), f2.read()

    dmp = dmp_module.diff_match_patch()
    diffs = dmp.diff_main(content1, content2)
    dmp.diff_cleanupSemantic(diffs)
    patch = dmp.patch_make(content1, diffs)
    return jsonify({'diff': dmp.patch_toText(patch)})


@editor_bp.route('/get_historical_content')
def get_historical_content():
    if not has_perm('can_versioning_modules').get_json().get('allowed'):
        return jsonify({'error': 'Acesso negado.'}), 403

    mid = request.args.get('mid')
    filename = request.args.get('filename')
    if not mid or not filename:
        return jsonify({'error': 'Parâmetros ausentes.'}), 400

    filepath = os.path.join(DATA_DIR, mid, "history", secure_filename(filename))
    if not os.path.exists(filepath):
        return jsonify({'error': 'Arquivo histórico não encontrado.'}), 404

    with open(filepath, 'r', encoding='utf-8') as f:
        html_content = markdown.markdown(f.read(), extensions=['fenced_code', 'tables'])
    return jsonify({'html': html_content})

def _handle_upload(folder_name: str):
    if 'file' not in request.files: return jsonify({'error': 'Nenhum arquivo encontrado'}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({'error': 'Nome de arquivo inválido'}), 400
    
    ext = Path(file.filename).suffix
    filename = f"{uuid.uuid4().hex}{ext}"
    upload_folder = os.path.join(BASE_DIR, 'data', folder_name, 'submodulo')
    os.makedirs(upload_folder, exist_ok=True)
    file.save(os.path.join(upload_folder, filename))
    
    file_url = url_for('static', filename=f'uploads/{folder_name}/{filename}', _external=False)
    return jsonify({'url': file_url, 'type': file.mimetype})

@editor_bp.route('/upload_submodule_anexo', methods=['POST'])
def upload_submodule_anexo():
    return _handle_upload('attachments')

@editor_bp.route('/upload_submodule_video', methods=['POST'])
def upload_submodule_video():
    return _handle_upload('videos')

@editor_bp.route('/upload_submodule_image', methods=['POST'])
def upload_submodule_image():
    return _handle_upload('images')
