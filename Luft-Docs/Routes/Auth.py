"""
Rotas de autenticação do LuftDocs.

Suporta dois modos:
  1. Tela de login (form POST)   — usa AuthService + login_user()
  2. Token na URL / Bearer header — tratado por Autenticacao.py (sem alterar aqui)

Blueprint: Auth_BP  (url_prefix='/auth')
"""
from __future__ import annotations

from flask import (
    Blueprint,
    redirect,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from luftcore.extensions.flask_extension import (
    mensagem_erro,
    mensagem_sucesso,
    renderizar_login,
)

from Utils.auth.UsuarioModel import UsuarioSistema
from Utils.auth.Autenticacao import PopularSessaoUsuario

Auth_BP = Blueprint("Auth", __name__, url_prefix="/auth")


@Auth_BP.route("/", methods=["GET"])
def redirecionarRaizAuth():
    return redirect(url_for("Auth.login"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _proximo_destino() -> str:
    """Retorna para onde redirecionar após login bem-sucedido."""
    destino = request.args.get("next") or url_for("Inicio.exibirInicio")
    # Segurança: garante que 'next' seja uma rota relativa (sem host externo)
    if destino.startswith("http"):
        destino = url_for("Inicio.exibirInicio")
    return destino


def _criar_usuario_sessao(dados: dict) -> UsuarioSistema:
    """Cria o objeto flask_login a partir do dict retornado pelo AuthService."""
    grupo_info = dados.get("user_group", {})
    return UsuarioSistema(
        id_banco       = int(dados["id"]),
        login          = dados["login"],
        nome           = dados["nome"],
        email          = dados.get("email", ""),
        grupo          = dados.get("grupo") or grupo_info.get("acronym", "Usuario"),
        id_grupo_banco = dados.get("id_grupo") or grupo_info.get("group_code"),
    )


# ---------------------------------------------------------------------------
# Tela de login
# ---------------------------------------------------------------------------

@Auth_BP.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("Inicio.exibirInicio"))

    if request.method == "POST":
        identificador = (
            request.form.get("usuario")
            or request.form.get("username")
            or ""
        ).strip()
        senha = (
            request.form.get("senha")
            or request.form.get("password")
            or ""
        ).strip()
        ip_cliente    = request.remote_addr

        if not identificador or not senha:
            mensagem_erro(
                "Preencha usuário e senha.",
                status_http=400,
                tipo="warning",
                titulo="Dados obrigatórios",
            )
            return renderizar_login(nome_app="LuftDocs", action_url=url_for("Auth.login"))

        # --- Autenticação via AuthService (AD + SQL Server) ---
        try:
            from Services.AuthService import AuthService  # lazy import
            dados = AuthService.ValidarAcessoCompleto(identificador, senha)
        except Exception as exc:
            # Loga mas não expõe detalhes internos ao usuário
            import logging
            logging.getLogger(__name__).error("Erro no AuthService: %s", exc)
            dados = None

        if dados:
            usuario = _criar_usuario_sessao(dados)

            # Popula session["permissions"], session["user_id"], etc.
            # (reutiliza a mesma lógica do fluxo de token para consistência)
            dados_api_formato = {
                "usuario": {
                    "id":        dados["id"],
                    "name":      dados["login"],
                    "email":     dados.get("email", ""),
                    "full_name": dados["nome"],
                },
                "grupo": {
                    "codigo_usuariogrupo": dados.get("id_grupo"),
                    "Sigla_UsuarioGrupo":  dados.get("grupo", ""),
                    "Descricao_UsuarioGrupo": "",
                },
                "token": None,
                "token_expira_em": None,
            }
            PopularSessaoUsuario(dados_api_formato)

            # Registra com flask_login (grava _user_id no cookie de sessão)
            login_user(usuario, remember=False)

            mensagem_sucesso(
                f"Bem-vindo(a), {dados['nome']}!",
                titulo="Login realizado",
            )
            return redirect(_proximo_destino())

        mensagem_erro(
            "Credenciais inválidas. Verifique usuário e senha.",
            status_http=401,
            tipo="warning",
            titulo="Falha na autenticação",
        )

    return renderizar_login(nome_app="LuftDocs", action_url=url_for("Auth.login"))


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

@Auth_BP.route("/logout")
@login_required
def logout():
    from Utils.auth.Autenticacao import EncerrarSessaoUsuario
    EncerrarSessaoUsuario()   # revoga token remoto + limpa session
    logout_user()             # limpa cookie flask_login
    mensagem_sucesso("Você saiu do sistema.", titulo="Sessão encerrada")
    return redirect(url_for("Auth.login"))
