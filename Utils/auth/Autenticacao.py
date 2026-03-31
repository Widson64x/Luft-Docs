from __future__ import annotations

from functools import wraps
from typing import Any, Callable

import requests
from flask import current_app, redirect, render_template, request, session, url_for

from Config import USER_API_URL
from Utils.auth.MapeamentoCamposUsuario import MAPA_CAMPOS_USUARIO
from Utils.auth.ProvedorUsuario import ObterUsuarioPorCredenciais, ObterUsuarioPorToken


def MapearCamposUsuario(usuarioApi: dict[str, Any]) -> dict[str, Any]:
    """Converte os campos recebidos da API para os nomes internos da aplicacao."""
    return {MAPA_CAMPOS_USUARIO.get(chave, chave): valor for chave, valor in usuarioApi.items()}


def PopularSessaoUsuario(dadosUsuarioApi: dict[str, Any] | None) -> bool:
    """Valida os dados recebidos da API e popula a sessao atual do usuario."""
    if not dadosUsuarioApi or "usuario" not in dadosUsuarioApi:
        return False

    usuario_api = dadosUsuarioApi["usuario"]
    usuario = MapearCamposUsuario(usuario_api)
    session["user_name"] = usuario.get("name")
    session["user_id"] = usuario.get("id")
    session["email"] = usuario.get("email")
    session["full_name"] = usuario.get("full_name")

    grupo_api = dadosUsuarioApi.get("grupo", {})
    session["user_group"] = {
        "group_code": grupo_api.get("codigo_usuariogrupo"),
        "acronym": grupo_api.get("Sigla_UsuarioGrupo"),
        "description": grupo_api.get("Descricao_UsuarioGrupo"),
    }

    from Services.ServicoPermissao import ServicoPermissao

    definicoes_permissoes = ServicoPermissao().carregarPermissoes()
    sigla_grupo = session["user_group"].get("acronym")
    nome_usuario = session.get("user_name")
    session["permissions"] = {}
    for nome_permissao, informacoes in definicoes_permissoes.items():
        session["permissions"][nome_permissao] = (
            sigla_grupo in informacoes.get("groups", [])
            or nome_usuario in informacoes.get("users", [])
        )

    session["token"] = dadosUsuarioApi.get("token")
    session["token_expiry"] = dadosUsuarioApi.get("token_expira_em")
    session.permanent = False
    return True


def ValidarUsuarioPorCredenciais() -> bool:
    """Valida o usuario a partir do login_hash presente na URL."""
    hash_login = request.args.get("login_hash", "").strip()
    if not hash_login:
        return False
    return PopularSessaoUsuario(ObterUsuarioPorCredenciais(hash_login))


def ValidarUsuarioPorToken() -> bool:
    """Valida o usuario a partir do token presente na URL."""
    token_bruto = request.args.get("token", "").strip()
    if not token_bruto:
        return False
    return PopularSessaoUsuario(ObterUsuarioPorToken(token_bruto))


def AutenticarRequisicaoInicial() -> Any:
    """Executa o fluxo inicial de autenticacao da requisicao de entrada."""
    if ValidarUsuarioPorToken():
        return True
    if ValidarUsuarioPorCredenciais():
        token = session.get("token")
        if token:
            return redirect(url_for("index.exibirInicio", token=token))
        return True
    return render_template("Auth/InfoLogin.html"), 403


def LoginObrigatorio(funcao: Callable[..., Any]) -> Callable[..., Any]:
    """Garante que a rota decorada so seja acessada por usuarios autenticados."""

    @wraps(funcao)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if "user_name" not in session or "user_id" not in session:
            return redirect(url_for("index.exibirInicio"))
        return funcao(*args, **kwargs)

    return wrapper


def EncerrarSessaoUsuario() -> bool:
    """Revoga o token remoto, quando possivel, e limpa a sessao local."""
    token = session.get("token")
    if token:
        try:
            resposta = requests.post(
                f"{USER_API_URL}/logout_token",
                json={"token": token},
                timeout=3,
            )
            resposta.raise_for_status()
        except requests.RequestException as erro:
            current_app.logger.error("Falha ao revogar token na API: %s", erro)
    session.clear()
    return True