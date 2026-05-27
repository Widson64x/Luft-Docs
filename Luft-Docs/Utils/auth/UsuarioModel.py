"""
Modelo flask_login do usuário autenticado no LuftDocs.

Funciona com AMBOS os fluxos de autenticação:
  1. Login via tela (form POST) → AuthService + login_user()
  2. Login via token na URL   → PopularSessaoUsuario() + login_user()
  3. API Bearer token          → RequerPermissao() resolve sem flask_login

O 'user_loader' do flask_login reconstrói o objeto a partir da sessão Flask
(sem query extra ao banco, pois os dados já foram salvos no login).
"""
from __future__ import annotations

from flask_login import UserMixin


class UsuarioSistema(UserMixin):
    """Representa o usuário autenticado na sessão."""

    def __init__(
        self,
        id_banco: int,
        login: str,
        nome: str,
        email: str = "",
        grupo: str = "Usuario",
        id_grupo_banco: int | None = None,
    ) -> None:
        # flask_login usa get_id() para gravar no cookie de sessão
        self._id          = str(id_banco)
        self.id_banco     = id_banco
        self.login        = login
        self.nome         = nome
        self.email        = email
        self.grupo        = grupo
        self.id_grupo     = id_grupo_banco

    # -- flask_login interface ------------------------------------------
    def get_id(self) -> str:
        return self._id

    # -- helpers de template -------------------------------------------
    @property
    def iniciais(self) -> str:
        partes = (self.nome or self.login).split()
        return "".join(p[0] for p in partes[:2]).upper() or "US"

    # -- reconstrução a partir da sessão Flask -------------------------
    @classmethod
    def da_sessao(cls, sessao: dict) -> "UsuarioSistema | None":
        """
        Reconstrói o objeto a partir do dict de sessão do Flask.
        Retorna None se os dados essenciais estiverem ausentes.
        """
        uid  = sessao.get("user_id")
        nome = sessao.get("user_name")
        if not uid or not nome:
            return None

        grupo_info = sessao.get("user_group", {})
        return cls(
            id_banco      = int(uid),
            login         = sessao.get("full_name") or nome,
            nome          = nome,
            email         = sessao.get("email", ""),
            grupo         = grupo_info.get("acronym", "Usuario"),
            id_grupo_banco= grupo_info.get("group_code"),
        )

    def __repr__(self) -> str:
        return f"<UsuarioSistema {self.login} [{self.grupo}]>"
