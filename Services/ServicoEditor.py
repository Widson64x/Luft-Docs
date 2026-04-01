from __future__ import annotations

import json
import os
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import diff_match_patch as dmp_module
import markdown
from flask import flash, jsonify, request, session, url_for
from werkzeug.utils import secure_filename

from Config import DATA_DIR, DATA_ROOT, DOCS_DOWNLOAD_DIR, ICONS_FILE, IMAGES_DIR, VIDEOS_DIR
from Models import HistoricoEdicao, Modulo, PalavraChave, db
from Services.PermissaoService import ChavesPermissao, PermissaoService
from Utils.data.UtilitariosModulo import CarregarModulos, ObterModuloPorId


class ServicoEditor:
    """Centraliza a regra de negocio das rotas do editor."""

    def obterRespostaPainelEditor(self) -> dict[str, Any]:
        """Monta o contexto da pagina principal do editor."""
        if not self._usuarioPossuiPermissao(ChavesPermissao.VISUALIZAR_EDITOR):
            return self._respostaErro(403, "Acesso negado ao editor.")

        modulos, _ = CarregarModulos()
        return self._respostaRenderizacao(
            "Editor/EDT_ModuleList.html",
            modulos=modulos,
            token=self._obterToken(),
            num_pendencias=self._obterQuantidadePendencias(),
        )

    def obterRespostaCriacaoModulo(self) -> dict[str, Any]:
        """Processa a criacao de um novo modulo."""
        if not self._usuarioPossuiPermissao(ChavesPermissao.CRIAR_MODULOS):
            return self._respostaErro(
                403, "Voce nao tem permissao para criar novos modulos."
            )

        token = self._obterToken()
        if request.method == "POST":
            identificador = request.form["id"].strip().lower().replace(" ", "-")

            if Modulo.query.get(identificador):
                flash(
                    f"O ID de modulo '{identificador}' ja existe. Por favor, escolha outro.",
                    "danger",
                )
                return self._respostaRedirecionamento(
                    "Editor.criarModulo", token=token
                )

            try:
                agora = datetime.now().isoformat()
                nome_usuario = session.get("user_name", "Anonimo")

                novo_modulo = Modulo(
                    Id=identificador,
                    Nome=request.form["nome"],
                    Descricao=request.form["descricao"],
                    Icone=request.form["icone"],
                    Is_Restrito=self._obterFlagFormulario("is_restrito"),
                    Status="aprovado",
                    VersaoAtual="1.0",
                    AprovadoPor=nome_usuario,
                    AprovadoEm=agora,
                )

                palavras_chave = [
                    termo.strip()
                    for termo in request.form["palavras_chave"].split(",")
                    if termo.strip()
                ]
                for palavra in palavras_chave:
                    novo_modulo.PalavrasChave.append(PalavraChave(Palavra=palavra))

                relacionados_ids = [
                    termo.strip()
                    for termo in request.form["relacionados"].split(",")
                    if termo.strip()
                ]
                if relacionados_ids:
                    novo_modulo.Relacionados = Modulo.query.filter(
                        Modulo.Id.in_(relacionados_ids)
                    ).all()

                novo_modulo.HistoricoEdicoes.append(
                    HistoricoEdicao(
                        Evento="criado",
                        Versao="1.0",
                        Editor=nome_usuario,
                        RegistradoEm=agora,
                    )
                )

                db.session.add(novo_modulo)
                db.session.commit()

                caminho_modulo = os.path.join(DATA_DIR, identificador)
                os.makedirs(caminho_modulo, exist_ok=True)
                conteudo_documentacao = self._limparLinhasEmBranco(
                    request.form.get("doc_content")
                    or self._carregarTemplateDocumentacao()
                )
                conteudo_tecnico = self._limparLinhasEmBranco(
                    request.form.get("tech_content") or self._carregarTemplateTecnico()
                )
                self._escreverArquivo(
                    os.path.join(caminho_modulo, "documentation.md"),
                    conteudo_documentacao,
                )
                self._escreverArquivo(
                    os.path.join(caminho_modulo, "technical_documentation.md"),
                    conteudo_tecnico,
                )

                flash(f"Modulo '{identificador}' criado com sucesso!", "success")
                return self._respostaRedirecionamento(
                    "Editor.exibirPainelEditor", token=token
                )
            except Exception as erro:
                db.session.rollback()
                flash(f"Erro ao criar o modulo: {erro}", "danger")

        return self._respostaRenderizacao(
            "Editor/EDT_ModuleNew.html",
            token=token,
            doc_content=self._carregarTemplateDocumentacao(),
            tech_content=self._carregarTemplateTecnico(),
        )

    def obterRespostaEdicaoModulo(self, modulo_id: str) -> dict[str, Any]:
        """Processa a edicao de um modulo existente."""
        if not self._usuarioPossuiPermissao(ChavesPermissao.EDITAR_MODULOS):
            return self._respostaErro(
                403, "Voce nao tem permissao para editar modulos."
            )

        token = self._obterToken()
        modulo = Modulo.query.get_or_404(modulo_id)

        if request.method == "POST":
            try:
                modulo.Nome = request.form["nome"]
                modulo.Descricao = request.form["descricao"]
                modulo.Icone = request.form["icone"]
                modulo.Is_Restrito = self._obterFlagFormulario("is_restrito")
                modulo.Status = "pendente"
                modulo.UsuarioEdicaoPendente = session.get("user_name", "Anonimo")
                modulo.DataEdicaoPendente = datetime.now().isoformat()

                novas_palavras = {
                    termo.strip()
                    for termo in request.form["palavras_chave"].split(",")
                    if termo.strip()
                }
                modulo.PalavrasChave = [
                    PalavraChave(Palavra=palavra) for palavra in novas_palavras
                ]

                relacionados_ids = {
                    termo.strip()
                    for termo in request.form["relacionados"].split(",")
                    if termo.strip()
                }
                modulo.Relacionados = Modulo.query.filter(
                    Modulo.Id.in_(relacionados_ids)
                ).all()

                db.session.commit()

                caminho_modulo = os.path.join(DATA_DIR, modulo_id)
                os.makedirs(caminho_modulo, exist_ok=True)
                self._escreverArquivo(
                    os.path.join(caminho_modulo, "pending_documentation.md"),
                    self._limparLinhasEmBranco(request.form["doc_content"]),
                )
                self._escreverArquivo(
                    os.path.join(
                        caminho_modulo,
                        "pending_technical_documentation.md",
                    ),
                    self._limparLinhasEmBranco(request.form["tech_content"]),
                )

                flash("Alteracao enviada para aprovacao!", "success")
                return self._respostaRedirecionamento(
                    "Editor.exibirPainelEditor", token=token
                )
            except Exception as erro:
                db.session.rollback()
                flash(f"Erro ao salvar o modulo: {erro}", "danger")

        caminho_modulo = os.path.join(DATA_DIR, modulo_id)
        conteudo_documentacao = self._lerPrimeiroArquivoExistente(
            os.path.join(caminho_modulo, "pending_documentation.md"),
            os.path.join(caminho_modulo, "documentation.md"),
        )
        conteudo_tecnico = self._lerPrimeiroArquivoExistente(
            os.path.join(caminho_modulo, "pending_technical_documentation.md"),
            os.path.join(caminho_modulo, "technical_documentation.md"),
        )

        return self._respostaRenderizacao(
            "Editor/EDT_ModuleEdit.html",
            modulo=ObterModuloPorId(modulo_id),
            doc_content=conteudo_documentacao,
            tech_content=conteudo_tecnico,
            token=token,
        )

    def obterRespostaExclusaoModulo(self, modulo_id: str) -> dict[str, Any]:
        """Exclui um modulo e seus arquivos associados."""
        if not self._usuarioPossuiPermissao(ChavesPermissao.EXCLUIR_MODULOS):
            return self._respostaErro(
                403, "Voce nao tem permissao para deletar modulos."
            )

        token = self._obterToken()
        modulo = Modulo.query.get_or_404(modulo_id)

        try:
            db.session.delete(modulo)
            db.session.commit()

            caminho_modulo = os.path.join(DATA_DIR, modulo_id)
            if os.path.isdir(caminho_modulo):
                shutil.rmtree(caminho_modulo)
            caminho_imagens = IMAGES_DIR / modulo_id
            if os.path.isdir(caminho_imagens):
                shutil.rmtree(caminho_imagens)

            flash(f"Modulo {modulo_id} deletado com sucesso!", "success")
        except Exception as erro:
            db.session.rollback()
            flash(f"Erro ao deletar o modulo: {erro}", "danger")

        return self._respostaRedirecionamento("Editor.exibirPainelEditor", token=token)

    def obterRespostaPendencias(self) -> dict[str, Any]:
        """Lista os modulos com alteracoes pendentes de aprovacao."""
        if not self._usuarioPossuiPermissao(ChavesPermissao.APROVAR_MODULOS):
            return self._respostaErro(
                403, "Voce nao tem permissao para gerenciar pendencias."
            )

        pendencias = [
            {
                "modulo": modulo,
                "editor": modulo.UsuarioEdicaoPendente or "N/A",
            }
            for modulo in Modulo.query.filter_by(Status="pendente").all()
        ]
        return self._respostaRenderizacao(
            "Editor/EDT_Pendings.html",
            pendentes=pendencias,
            token=self._obterToken(),
        )

    def obterRespostaAprovacaoModulo(self, modulo_id: str) -> dict[str, Any]:
        """Aprova uma alteracao pendente de modulo."""
        if not self._usuarioPossuiPermissao(ChavesPermissao.APROVAR_MODULOS):
            return self._respostaErro(
                403, "Voce nao tem permissao para aprovar alteracoes."
            )

        token = self._obterToken()
        modulo = Modulo.query.get_or_404(modulo_id)

        try:
            agora = datetime.now()
            nome_aprovador = session.get("user_name", "Anonimo")
            nome_editor = modulo.UsuarioEdicaoPendente or "Desconhecido"

            major, minor = map(int, modulo.VersaoAtual.split("."))
            nova_versao = f"{major}.{minor + 1}"

            caminho_modulo = os.path.join(DATA_DIR, modulo_id)
            diretorio_historico = os.path.join(caminho_modulo, "history")
            os.makedirs(diretorio_historico, exist_ok=True)

            caminho_pendente = os.path.join(caminho_modulo, "pending_documentation.md")
            caminho_oficial = os.path.join(caminho_modulo, "documentation.md")
            caminho_tecnico_pendente = os.path.join(
                caminho_modulo, "pending_technical_documentation.md"
            )
            caminho_tecnico_oficial = os.path.join(
                caminho_modulo, "technical_documentation.md"
            )

            backup_documentacao = None
            backup_tecnico = None
            if os.path.exists(caminho_pendente):
                if os.path.exists(caminho_oficial):
                    backup_documentacao = (
                        f"v{nova_versao}_{agora.strftime('%Y-%m-%dT%H-%M-%S')}_doc.md"
                    )
                    shutil.copyfile(
                        caminho_oficial,
                        os.path.join(diretorio_historico, backup_documentacao),
                    )
                shutil.move(caminho_pendente, caminho_oficial)

            if os.path.exists(caminho_tecnico_pendente):
                if os.path.exists(caminho_tecnico_oficial):
                    backup_tecnico = (
                        f"v{nova_versao}_{agora.strftime('%Y-%m-%dT%H-%M-%S')}_tech.md"
                    )
                    shutil.copyfile(
                        caminho_tecnico_oficial,
                        os.path.join(diretorio_historico, backup_tecnico),
                    )
                shutil.move(caminho_tecnico_pendente, caminho_tecnico_oficial)

            modulo.Status = "aprovado"
            modulo.VersaoAtual = nova_versao
            modulo.AprovadoPor = nome_aprovador
            modulo.AprovadoEm = agora.isoformat()
            modulo.UsuarioEdicaoPendente = None
            modulo.DataEdicaoPendente = None

            modulo.HistoricoEdicoes.append(
                HistoricoEdicao(
                    Evento="aprovado",
                    Versao=nova_versao,
                    Editor=nome_editor,
                    Aprovador=nome_aprovador,
                    RegistradoEm=agora.isoformat(),
                    ArquivoBackupDocumentacao=backup_documentacao,
                    ArquivoBackupDocumentacaoTecnica=backup_tecnico,
                )
            )

            db.session.commit()
            flash(
                f"Alteracoes no modulo '{modulo_id}' aprovadas com sucesso!",
                "success",
            )
        except Exception as erro:
            db.session.rollback()
            flash(f"Erro ao aprovar o modulo: {erro}", "danger")

        return self._respostaRedirecionamento("Editor.exibirPendencias", token=token)

    def obterRespostaRejeicaoModulo(self, modulo_id: str) -> dict[str, Any]:
        """Rejeita uma alteracao pendente de modulo."""
        if not self._usuarioPossuiPermissao(ChavesPermissao.REJEITAR_MODULOS):
            return self._respostaErro(
                403, "Voce nao tem permissao para rejeitar alteracoes."
            )

        token = self._obterToken()
        modulo = Modulo.query.get_or_404(modulo_id)

        try:
            nome_editor = modulo.UsuarioEdicaoPendente or "Desconhecido"
            caminho_pendente = os.path.join(DATA_DIR, modulo_id, "pending_documentation.md")
            caminho_tecnico_pendente = os.path.join(
                DATA_DIR, modulo_id, "pending_technical_documentation.md"
            )
            if os.path.exists(caminho_pendente):
                os.remove(caminho_pendente)
            if os.path.exists(caminho_tecnico_pendente):
                os.remove(caminho_tecnico_pendente)

            modulo.Status = "aprovado"
            modulo.UsuarioEdicaoPendente = None
            modulo.DataEdicaoPendente = None
            modulo.HistoricoEdicoes.append(
                HistoricoEdicao(
                    Evento="rejeitado",
                    Editor=nome_editor,
                    Aprovador=session.get("user_name", "Anonimo"),
                    RegistradoEm=datetime.now().isoformat(),
                )
            )

            db.session.commit()
            flash(
                f"Alteracao pendente para o modulo '{modulo_id}' foi rejeitada.",
                "info",
            )
        except Exception as erro:
            db.session.rollback()
            flash(f"Erro ao rejeitar o modulo: {erro}", "danger")

        return self._respostaRedirecionamento("Editor.exibirPendencias", token=token)

    def obterRespostaHistoricoModulo(self, modulo_id: str) -> dict[str, Any]:
        """Exibe ou restaura o historico de versoes de um modulo."""
        if not self._usuarioPossuiPermissao(ChavesPermissao.VERSIONAR_MODULOS):
            return self._respostaErro(
                403, "Voce nao tem permissao para acessar o historico."
            )

        token = self._obterToken()
        modulo = Modulo.query.get_or_404(modulo_id)
        caminho_modulo = os.path.join(DATA_DIR, modulo_id)
        diretorio_historico = os.path.join(caminho_modulo, "history")
        os.makedirs(diretorio_historico, exist_ok=True)

        if request.method == "POST":
            try:
                nome_arquivo_alvo = request.form.get("versao_filename")
                tipo_arquivo = request.form.get("tipo")
                nome_usuario = session.get("user_name", "Anonimo")
                agora = datetime.now()

                nome_vigente = (
                    "documentation.md"
                    if tipo_arquivo == "doc"
                    else "technical_documentation.md"
                )
                caminho_vigente = os.path.join(caminho_modulo, nome_vigente)
                caminho_versao_antiga = os.path.join(
                    diretorio_historico,
                    secure_filename(nome_arquivo_alvo),
                )

                if not os.path.exists(caminho_versao_antiga):
                    flash("Arquivo da versao selecionada nao encontrado.", "danger")
                    return self._respostaRedirecionamento(
                        "Editor.exibirHistoricoModulo",
                        mid=modulo_id,
                        token=token,
                    )

                identificador_tipo = "doc" if tipo_arquivo == "doc" else "tech"
                nome_backup = (
                    f"v{modulo.VersaoAtual}_BKP-PRE-RESTORE_"
                    f"{agora.strftime('%Y-%m-%dT%H-%M-%S')}_{identificador_tipo}.md"
                )
                caminho_backup = os.path.join(diretorio_historico, nome_backup)

                if os.path.exists(caminho_vigente):
                    shutil.copyfile(caminho_vigente, caminho_backup)

                shutil.copyfile(caminho_versao_antiga, caminho_vigente)

                versao_restaurada = "Regressao"
                correspondencia = re.search(r"v(\d+\.\d+)", nome_arquivo_alvo or "")
                if correspondencia:
                    versao_restaurada = correspondencia.group(1)

                modulo.HistoricoEdicoes.append(
                    HistoricoEdicao(
                        Evento="restaurado",
                        Versao=f"{versao_restaurada} (Restaurado)",
                        Editor=nome_usuario,
                        RegistradoEm=agora.isoformat(),
                        ArquivoBackupDocumentacao=nome_backup if tipo_arquivo == "doc" else None,
                        ArquivoBackupDocumentacaoTecnica=nome_backup if tipo_arquivo == "tech" else None,
                    )
                )
                modulo.AprovadoPor = f"{nome_usuario} (Rollback)"
                modulo.AprovadoEm = agora.isoformat()

                db.session.commit()
                flash(
                    "Modulo restaurado para a versao selecionada. "
                    "A versao anterior foi salva como backup.",
                    "success",
                )
            except Exception as erro:
                db.session.rollback()
                flash(f"Erro ao restaurar versao: {erro}", "danger")

            return self._respostaRedirecionamento(
                "Editor.exibirHistoricoModulo", mid=modulo_id, token=token
            )

        historico_eventos = sorted(
            modulo.HistoricoEdicoes,
            key=lambda evento: evento.RegistradoEm,
            reverse=True,
        )
        return self._respostaRenderizacao(
            "Editor/HistoricalModule.html",
            modulo=modulo,
            historico_eventos=historico_eventos,
            token=token,
        )

    def obterRespostaOpcoesEditor(self) -> dict[str, Any]:
        """Retorna os dados auxiliares usados pelos formularios do editor."""
        modulos = [
            {"id": linha.Id, "nome": linha.Nome}
            for linha in Modulo.query.with_entities(Modulo.Id, Modulo.Nome)
            .order_by(Modulo.Nome)
            .all()
        ]

        try:
            with open(ICONS_FILE, "r", encoding="utf-8") as arquivo_icones:
                icones = json.load(arquivo_icones)
        except (FileNotFoundError, json.JSONDecodeError):
            icones = ["bi-alarm", "bi-bag", "bi-gear", "bi-activity"]

        return self._respostaJson(
            modules=modulos,
            icons=icones,
            keywords=[
                "tutorial",
                "referencia",
                "exemplo",
                "guia",
                "API",
                "como usar",
            ],
        )

    def obterRespostaUploadImagem(self, modulo_id: str) -> dict[str, Any]:
        """Processa o upload de imagem de modulo."""
        if "file" not in request.files:
            return self._respostaJsonErro("Nenhum arquivo enviado", 400)

        arquivo = request.files["file"]
        extensao = os.path.splitext(arquivo.filename)[1].lower()
        if extensao not in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"]:
            return self._respostaJsonErro("Formato nao suportado", 400)

        diretorio_destino = IMAGES_DIR / modulo_id
        os.makedirs(diretorio_destino, exist_ok=True)

        indice = 1
        while True:
            nome_arquivo = secure_filename(f"img{indice}{extensao}")
            caminho_arquivo = os.path.join(diretorio_destino, nome_arquivo)
            if not os.path.exists(caminho_arquivo):
                break
            indice += 1

        arquivo.save(caminho_arquivo)
        return self._respostaJson(
            url=url_for(
                "Inicio.servirImagemDinamica",
                nome_arquivo=f"{modulo_id}/{nome_arquivo}",
                _external=False,
            )
        )

    def obterRespostaUploadVideo(self, modulo_id: str) -> dict[str, Any]:
        """Processa o upload de video de modulo."""
        if "file" not in request.files:
            return self._respostaJsonErro("Nenhum arquivo enviado", 400)

        arquivo = request.files["file"]
        extensao = os.path.splitext(arquivo.filename)[1].lower()
        if extensao not in [".mp4", ".webm", ".ogg"]:
            return self._respostaJsonErro("Formato de video nao suportado", 400)

        diretorio_destino = VIDEOS_DIR / modulo_id
        os.makedirs(diretorio_destino, exist_ok=True)

        nome_arquivo = secure_filename(arquivo.filename)
        arquivo.save(os.path.join(diretorio_destino, nome_arquivo))
        return self._respostaJson(
            url=url_for(
                "Inicio.servirVideo",
                nome_arquivo=f"{modulo_id}/{nome_arquivo}",
                _external=False,
            ),
            type=f"video/{extensao[1:]}",
        )

    def obterRespostaUploadAnexo(self) -> dict[str, Any]:
        """Processa o upload de anexos para download."""
        if "file" not in request.files:
            return self._respostaJsonErro("Nenhum arquivo enviado", 400)

        arquivo = request.files["file"]
        nome_arquivo = secure_filename(arquivo.filename)

        os.makedirs(DOCS_DOWNLOAD_DIR, exist_ok=True)
        arquivo.save(os.path.join(DOCS_DOWNLOAD_DIR, nome_arquivo))
        return self._respostaJson(
            url=url_for(
                "Arquivos.baixarPelaRaiz",
                token="__TOKEN_PLACEHOLDER__",
                download=nome_arquivo,
            )
        )

    def obterRespostaListagemSubmodulos(self) -> dict[str, Any]:
        """Lista os submodulos globais disponiveis."""
        diretorio_global = Path(DATA_ROOT) / "global"
        diretorio_global.mkdir(exist_ok=True)

        submodulos = []
        for arquivo in diretorio_global.rglob("*.md"):
            data_modificacao = datetime.fromtimestamp(os.path.getmtime(arquivo)).strftime(
                "%d/%m/%Y %H:%M:%S"
            )
            submodulos.append(
                {
                    "path": arquivo.relative_to(diretorio_global).as_posix(),
                    "modified": data_modificacao,
                }
            )
        submodulos.sort(key=lambda item: item["path"])

        return self._respostaRenderizacao(
            "Editor/EDT_SubModuleList.html",
            submodulos=submodulos,
            dir_tree_json=json.dumps(self._montarArvoreDiretorios(diretorio_global)),
            token=self._obterToken(),
        )

    def obterRespostaExclusaoSubmodulo(self) -> dict[str, Any]:
        """Exclui um submodulo global e limpa pastas vazias."""
        token = request.form.get("token")
        if not token:
            return self._respostaErro(403, "Nao autorizado")

        caminho_relativo = request.form.get("path_to_delete")
        if not caminho_relativo:
            flash("Caminho do arquivo nao fornecido.", "danger")
            return self._respostaRedirecionamento("Editor.listarSubmodulos", token=token)

        diretorio_global = Path(DATA_ROOT) / "global"
        caminho_completo = diretorio_global.joinpath(caminho_relativo).resolve()
        if diretorio_global.resolve() not in caminho_completo.parents:
            flash("Tentativa de exclusao de arquivo invalida.", "danger")
            return self._respostaRedirecionamento("Editor.listarSubmodulos", token=token)

        try:
            if caminho_completo.is_file():
                caminho_completo.unlink()
                flash(
                    f'Submodulo "{caminho_relativo}" deletado com sucesso.',
                    "success",
                )
                pasta_pai = caminho_completo.parent
                while pasta_pai != diretorio_global and not any(pasta_pai.iterdir()):
                    pasta_pai.rmdir()
                    pasta_pai = pasta_pai.parent
            else:
                flash("O caminho especificado nao e um arquivo valido.", "warning")
        except Exception as erro:
            flash(f"Erro ao deletar o arquivo: {erro}", "danger")

        return self._respostaRedirecionamento("Editor.listarSubmodulos", token=token)

    def obterRespostaCriacaoSubmodulo(self) -> dict[str, Any]:
        """Cria um submodulo vazio ou redireciona para edicao se ele ja existir."""
        token = request.form.get("token")
        if not token:
            return self._respostaErro(403, "Nao autorizado")

        caminho_pasta = request.form.get("folder_path", "").strip()
        nome_arquivo = request.form.get("file_name", "").strip()
        if not nome_arquivo:
            flash("O nome do arquivo e obrigatorio.", "danger")
            return self._respostaRedirecionamento("Editor.listarSubmodulos", token=token)

        nome_arquivo = nome_arquivo.replace(".md", "").replace("/", "").replace("\\", "")
        if ".." in caminho_pasta or caminho_pasta.startswith("/"):
            flash("Caminho de pasta invalido.", "danger")
            return self._respostaRedirecionamento("Editor.listarSubmodulos", token=token)

        diretorio_global = Path(DATA_ROOT) / "global"
        diretorio_destino = (
            diretorio_global.joinpath(caminho_pasta)
            if caminho_pasta and caminho_pasta != "."
            else diretorio_global
        )
        diretorio_destino.mkdir(parents=True, exist_ok=True)

        caminho_final = diretorio_destino / f"{nome_arquivo}.md"
        if caminho_final.exists():
            flash(f'O arquivo "{nome_arquivo}.md" ja existe. Abrindo para edicao.', "info")
        else:
            caminho_final.touch()
            flash(f'Submodulo "{nome_arquivo}.md" criado com sucesso!', "success")

        submodulo_path = caminho_final.relative_to(diretorio_global).as_posix()
        return self._respostaRedirecionamento(
            "Editor.editarSubmodulo",
            submodulo_path=submodulo_path,
            token=token,
        )

    def obterRespostaEdicaoSubmodulo(self, submodulo_path: str) -> dict[str, Any]:
        """Exibe ou salva um submodulo global."""
        token = self._obterToken()
        diretorio_global = Path(DATA_ROOT) / "global"
        caminho_arquivo = diretorio_global / submodulo_path

        if request.method == "POST":
            conteudo = self._limparLinhasEmBranco(request.form.get("content", ""))
            caminho_arquivo.parent.mkdir(parents=True, exist_ok=True)
            caminho_arquivo.write_text(conteudo, encoding="utf-8")
            flash("Submodulo salvo com sucesso!", "success")
            return self._respostaRedirecionamento("Editor.listarSubmodulos", token=token)

        return self._respostaRenderizacao(
            "Editor/EDT_SubModuleEdit.html",
            path=submodulo_path,
            content=caminho_arquivo.read_text(encoding="utf-8")
            if caminho_arquivo.exists()
            else "",
            token=token,
        )

    def obterRespostaDiffPendente(self) -> dict[str, Any]:
        """Retorna o diff entre a documentacao vigente e a pendente."""
        if not self._usuarioPossuiPermissao(ChavesPermissao.APROVAR_MODULOS):
            return self._respostaJsonErro("Acesso negado.", 403)

        modulo_id = request.args.get("mid")
        if not modulo_id:
            return self._respostaJsonErro("Parametros invalidos.", 400)

        caminho_modulo = os.path.join(DATA_DIR, modulo_id)
        documentacao = self._lerArquivoOpcional(
            os.path.join(caminho_modulo, "documentation.md")
        )
        documentacao_pendente = self._lerArquivoOpcional(
            os.path.join(caminho_modulo, "pending_documentation.md")
        )
        tecnico = self._lerArquivoOpcional(
            os.path.join(caminho_modulo, "technical_documentation.md")
        )
        tecnico_pendente = self._lerArquivoOpcional(
            os.path.join(caminho_modulo, "pending_technical_documentation.md")
        )

        return self._respostaJson(
            doc_html_left=self._renderizarMarkdownLimpo(documentacao),
            doc_html_right=self._renderizarDiffHtml(documentacao, documentacao_pendente),
            tech_html_left=self._renderizarMarkdownLimpo(tecnico),
            tech_html_right=self._renderizarDiffHtml(tecnico, tecnico_pendente),
        )

    def obterRespostaDiffHistorico(self) -> dict[str, Any]:
        """Retorna o diff entre a versao atual e uma versao historica."""
        if not self._usuarioPossuiPermissao(ChavesPermissao.VERSIONAR_MODULOS):
            return self._respostaJsonErro("Acesso negado.", 403)

        modulo_id = request.args.get("mid")
        nome_arquivo_historico = request.args.get("file1")
        tipo = request.args.get("tipo", "doc")
        if not modulo_id or not nome_arquivo_historico:
            return self._respostaJsonErro("Parametros invalidos.", 400)

        caminho_modulo = os.path.join(DATA_DIR, modulo_id)
        diretorio_historico = os.path.join(caminho_modulo, "history")
        nome_vigente = (
            "documentation.md" if tipo == "doc" else "technical_documentation.md"
        )
        conteudo_atual = self._lerArquivoOpcional(os.path.join(caminho_modulo, nome_vigente))
        conteudo_historico = self._lerArquivoOpcional(
            os.path.join(diretorio_historico, secure_filename(nome_arquivo_historico))
        )

        return self._respostaJson(
            html_left=self._renderizarMarkdownLimpo(conteudo_atual),
            html_right=self._renderizarDiffHtml(conteudo_atual, conteudo_historico),
        )

    def obterRespostaConteudoHistorico(self) -> dict[str, Any]:
        """Retorna o HTML renderizado de um arquivo historico especifico."""
        if not self._usuarioPossuiPermissao(ChavesPermissao.VERSIONAR_MODULOS):
            return self._respostaJsonErro("Acesso negado.", 403)

        modulo_id = request.args.get("mid")
        nome_arquivo = request.args.get("filename")
        if not modulo_id or not nome_arquivo:
            return self._respostaJsonErro("Parametros ausentes.", 400)

        caminho_arquivo = os.path.join(
            DATA_DIR,
            modulo_id,
            "history",
            secure_filename(nome_arquivo),
        )
        if not os.path.exists(caminho_arquivo):
            return self._respostaJsonErro("Arquivo historico nao encontrado.", 404)

        return self._respostaJson(
            html=markdown.markdown(
                self._lerArquivoOpcional(caminho_arquivo),
                extensions=["fenced_code", "tables"],
            )
        )

    def obterRespostaUploadAnexoSubmodulo(self) -> dict[str, Any]:
        """Processa o upload de anexos para submodulos."""
        return self._tratarUploadSubmodulo("attachments")

    def obterRespostaUploadVideoSubmodulo(self) -> dict[str, Any]:
        """Processa o upload de videos para submodulos."""
        return self._tratarUploadSubmodulo("videos")

    def obterRespostaUploadImagemSubmodulo(self) -> dict[str, Any]:
        """Processa o upload de imagens para submodulos."""
        return self._tratarUploadSubmodulo("images")

    def _tratarUploadSubmodulo(self, nome_pasta: str) -> dict[str, Any]:
        if "file" not in request.files:
            return self._respostaJsonErro("Nenhum arquivo encontrado", 400)

        arquivo = request.files["file"]
        if arquivo.filename == "":
            return self._respostaJsonErro("Nome de arquivo invalido", 400)

        extensao = Path(arquivo.filename).suffix
        nome_arquivo = f"{uuid.uuid4().hex}{extensao}"
        pasta_upload = os.path.join(DATA_ROOT, nome_pasta, "submodulo")
        os.makedirs(pasta_upload, exist_ok=True)
        arquivo.save(os.path.join(pasta_upload, nome_arquivo))

        return self._respostaJson(
            url=url_for(
                "static",
                filename=f"uploads/{nome_pasta}/{nome_arquivo}",
                _external=False,
            ),
            type=arquivo.mimetype,
        )

    @staticmethod
    def _limparLinhasEmBranco(markdown_texto: str) -> str:
        if not markdown_texto:
            return ""
        texto = markdown_texto.replace("\r\n", "\n").rstrip()
        return re.sub(r"\n{3,}", "\n\n", texto)

    @staticmethod
    def _obterQuantidadePendencias() -> int:
        return Modulo.query.filter_by(Status="pendente").count()

    @staticmethod
    def _carregarTemplateDocumentacao() -> str:
        try:
            with open(
                os.path.join(DATA_DIR, "templates", "template_documentation.md"),
                "r",
                encoding="utf-8",
            ) as arquivo:
                return arquivo.read()
        except FileNotFoundError:
            return "# Documentacao do Modulo\n"

    @staticmethod
    def _carregarTemplateTecnico() -> str:
        try:
            with open(
                os.path.join(
                    DATA_DIR,
                    "templates",
                    "template_technical_documentation.md",
                ),
                "r",
                encoding="utf-8",
            ) as arquivo:
                return arquivo.read()
        except FileNotFoundError:
            return "# Documentacao Tecnica\n"

    @staticmethod
    def _renderizarMarkdownLimpo(texto: str) -> str:
        if not texto:
            return ""
        return markdown.markdown(
            texto,
            extensions=["fenced_code", "tables", "nl2br"],
        )

    @staticmethod
    def _renderizarDiffHtml(conteudo_antigo: str, conteudo_novo: str) -> str:
        diferenca = dmp_module.diff_match_patch()
        diffs = diferenca.diff_main(conteudo_antigo, conteudo_novo)
        diferenca.diff_cleanupSemantic(diffs)

        partes_html = []
        for operacao, dados in diffs:
            if not dados:
                continue

            conteudo_seguro = markdown.markdown(
                dados,
                extensions=["fenced_code", "tables", "nl2br"],
            )
            if conteudo_seguro.startswith("<p>") and conteudo_seguro.endswith("</p>"):
                conteudo_seguro = conteudo_seguro[3:-4]

            if operacao == diferenca.DIFF_INSERT:
                partes_html.append(
                    f'<span class="diff-chunk diff-add">{conteudo_seguro}</span>'
                )
            elif operacao == diferenca.DIFF_DELETE:
                partes_html.append(
                    f'<span class="diff-chunk diff-rem">{conteudo_seguro}</span>'
                )
            else:
                partes_html.append(f'<span class="diff-chunk">{conteudo_seguro}</span>')

        return "".join(partes_html)

    def _montarArvoreDiretorios(self, caminho: Path) -> dict[str, Any]:
        arvore = {}
        for item in os.scandir(caminho):
            if item.is_dir():
                arvore[item.name] = self._montarArvoreDiretorios(Path(item.path))
        return arvore

    @staticmethod
    def _lerPrimeiroArquivoExistente(*caminhos: str) -> str:
        for caminho in caminhos:
            if os.path.exists(caminho):
                with open(caminho, "r", encoding="utf-8") as arquivo:
                    return arquivo.read()
        return ""

    @staticmethod
    def _lerArquivoOpcional(caminho: str) -> str:
        if not os.path.exists(caminho):
            return ""
        with open(caminho, "r", encoding="utf-8") as arquivo:
            return arquivo.read()

    @staticmethod
    def _escreverArquivo(caminho: str, conteudo: str) -> None:
        with open(caminho, "w", encoding="utf-8") as arquivo:
            arquivo.write(conteudo)

    @staticmethod
    def _obterToken() -> str:
        return request.args.get("token", "") or request.form.get("token", "")

    @staticmethod
    def _obterFlagFormulario(nome_campo: str) -> bool:
        valor = str(request.form.get(nome_campo, "")).strip().lower()
        return valor in {"1", "true", "on", "yes", "sim"}

    @staticmethod
    def _usuarioPossuiPermissao(nome_permissao: str) -> bool:
        return PermissaoService.usuarioPossuiPermissao(nome_permissao)

    @staticmethod
    def _respostaRenderizacao(template: str, **contexto: Any) -> dict[str, Any]:
        return {"tipo": "renderizar", "template": template, "contexto": contexto}

    @staticmethod
    def _respostaRedirecionamento(endpoint: str, **parametros: Any) -> dict[str, Any]:
        return {"tipo": "redirecionar", "endpoint": endpoint, "parametros": parametros}

    @staticmethod
    def _respostaJson(**dados: Any) -> dict[str, Any]:
        return {"tipo": "json", "dados": dados, "codigo": 200}

    @staticmethod
    def _respostaJsonErro(mensagem: str, codigo: int) -> dict[str, Any]:
        return {"tipo": "json", "dados": {"error": mensagem}, "codigo": codigo}

    @staticmethod
    def _respostaErro(codigo: int, mensagem: str) -> dict[str, Any]:
        return {"tipo": "erro", "codigo": codigo, "mensagem": mensagem}