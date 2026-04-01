# Routes/Permissoes.py
"""
Blueprint de administração de permissões do LuftDocs.

Rotas:
  GET  /permissoes/                       → tela principal (tabs Grupos/Usuários)
  POST /permissoes/criar                  → cria nova permissão
  GET  /permissoes/api/acessos-grupo      → IDs ativos de um grupo (AJAX)
  GET  /permissoes/api/acessos-usuario    → IDs ativos de um usuário (AJAX)
  POST /permissoes/api/salvar-vinculo     → toggle on/off (AJAX)
  GET  /permissoes/verificar/<chave>      → verificação pontual (retrocompatível)
  GET  /permissoes/meu-grupo              → grupo/permissões do usuário logado
"""

from collections import defaultdict
import logging

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required
from luftcore.extensions.flask_extension import api_error, require_ajax, render_500, render_no_permission, render_404

from Services.PermissaoService import ChavesPermissao, PermissaoService, RequerPermissao

Permissoes_BP = Blueprint("Permissoes", __name__)
_logger = logging.getLogger(__name__)


def _renderizar_erro_http(codigo: int, mensagem: str):
    if codigo == 403:
        return render_no_permission(mensagem)
    if codigo == 404:
        return render_404(mensagem)
    return render_500(mensagem)


# ---------------------------------------------------------------------------
# Página principal
# ---------------------------------------------------------------------------

@Permissoes_BP.route("/")
@RequerPermissao(ChavesPermissao.VISUALIZAR_SEGURANCA)
@login_required
def gerenciarPermissoes():
    try:
        todas_permissoes = PermissaoService.listarTodasPermissoes()
        permissoes_por_categoria = defaultdict(list)
        for perm in todas_permissoes:
            permissoes_por_categoria[perm.Categoria_Permissao or "GERAL"].append(perm)

        lista_grupos = PermissaoService.listarGruposDiretorio()
        lista_usuarios = PermissaoService.listarUsuariosDiretorio()

        pode_editar = PermissaoService.usuarioPossuiPermissao(
            ChavesPermissao.EDITAR_SEGURANCA
        )
        pode_criar = PermissaoService.usuarioPossuiPermissao(
            ChavesPermissao.CRIAR_SEGURANCA
        )

        return render_template(
            "Pages/Permissoes.html",
            PermissoesPorCategoria=dict(permissoes_por_categoria),
            Grupos=lista_grupos,
            Usuarios=lista_usuarios,
            PodeEditar=pode_editar,
            PodeCriar=pode_criar,
        )
    except Exception as exc:
        _logger.exception("[Permissoes] Erro ao montar tela de permissões: %s", exc)
        return _renderizar_erro_http(500, "Não foi possível carregar a central de permissões.")


# ---------------------------------------------------------------------------
# Criar permissão
# ---------------------------------------------------------------------------

@Permissoes_BP.route("/criar", methods=["POST"])
@RequerPermissao(ChavesPermissao.CRIAR_SEGURANCA)
@login_required
def criarNovaPermissao():
    modulo = request.form.get("modulo", "").upper().strip().replace(" ", "_")
    acao = request.form.get("acao", "").upper().strip()
    excecao = request.form.get("excecao", "").upper().strip().replace(" ", "_")
    descricao = request.form.get("descricao", "").strip()

    if not modulo or not acao or not descricao:
        flash("Preencha todos os campos obrigatórios.", "danger")
        return redirect(url_for("Permissoes.gerenciarPermissoes"))

    chave = f"{modulo}.{excecao}.{acao}" if excecao else f"{modulo}.{acao}"

    try:
        PermissaoService.criarPermissao(chave, descricao, modulo)
        flash("Permissão criada com sucesso!", "success")
    except ValueError as exc:
        flash(str(exc), "warning")
    except Exception as exc:
        flash(f"Erro ao criar permissão: {exc}", "danger")

    return redirect(url_for("Permissoes.gerenciarPermissoes"))


# ---------------------------------------------------------------------------
# APIs AJAX
# ---------------------------------------------------------------------------

@Permissoes_BP.route("/api/acessos-grupo", methods=["GET"])
@RequerPermissao(ChavesPermissao.VISUALIZAR_SEGURANCA)
@login_required
@require_ajax
def buscarAcessosGrupo():
    id_grupo = request.args.get("idGrupo", type=int)
    if not id_grupo:
        return api_error("Parâmetro idGrupo é obrigatório.", status=400)
    ids_ativos = PermissaoService.idsPermitidosPorGrupo(id_grupo)
    return jsonify({"ids_ativos": ids_ativos})


@Permissoes_BP.route("/api/acessos-usuario", methods=["GET"])
@RequerPermissao(ChavesPermissao.VISUALIZAR_SEGURANCA)
@login_required
@require_ajax
def buscarAcessosUsuario():
    id_usuario = request.args.get("idUsuario", type=int)
    if not id_usuario:
        return api_error("Parâmetro idUsuario é obrigatório.", status=400)
    dados = PermissaoService.acessosUsuario(id_usuario)
    return jsonify(dados)


@Permissoes_BP.route("/api/salvar-vinculo", methods=["POST"])
@RequerPermissao(ChavesPermissao.EDITAR_SEGURANCA)
@login_required
@require_ajax
def salvarVinculo():
    dados = request.get_json(silent=True) or {}
    tipo = dados.get("Tipo")           # "grupo" ou "usuario"
    id_alvo = dados.get("IdAlvo")
    id_permissao = dados.get("IdPermissao")
    conceder = dados.get("Conceder")   # True / False / None

    if not tipo or id_alvo is None or id_permissao is None:
        return api_error("Parâmetros insuficientes.", status=400)

    try:
        if tipo == "grupo":
            PermissaoService.salvarVinculoGrupo(int(id_alvo), int(id_permissao), bool(conceder))
        elif tipo == "usuario":
            # None = remover override
            valor = None if conceder is None else bool(conceder)
            PermissaoService.salvarVinculoUsuario(int(id_alvo), int(id_permissao), valor)
        else:
            return api_error("Tipo inválido.", status=400)

        return jsonify({"ok": True})
    except Exception as exc:
        _logger.exception("[Permissoes] Erro ao salvar vínculo: %s", exc)
        return api_error("Falha ao salvar o vínculo de permissão.", status=500)


# ---------------------------------------------------------------------------
# Retrocompatibilidade
# ---------------------------------------------------------------------------

@Permissoes_BP.route("/verificar/<permission_name>", methods=["GET"])
@RequerPermissao(ChavesPermissao.VISUALIZAR_SEGURANCA)
@login_required
@require_ajax
def verificarPermissao(permission_name: str):
    """Endpoint legado — verifica se o usuário logado tem a permissão."""
    resultado = PermissaoService.verificarPermissao(permission_name)
    return jsonify({"allowed": resultado})


@Permissoes_BP.route("/meu-grupo", methods=["GET"])
@RequerPermissao(ChavesPermissao.VISUALIZAR_SEGURANCA)
@login_required
@require_ajax
def obterMeuGrupo():
    """Retorna grupo e permissões do usuário logado."""
    from flask import session
    grupo = session.get("user_group", {}).get("acronym", "")
    nome = session.get("user_name", "")
    permissoes = {
        chave: PermissaoService.verificarPermissao(chave)
        for chave in ChavesPermissao.CACHE_SESSAO
    }
    return jsonify({"user": nome, "group": grupo, "permissions": permissoes})

