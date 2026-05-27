"""Modelos ORM relacionados ao dominio de usuarios."""

from typing import Any, Dict

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base


BaseModelo = declarative_base()


class UsuarioModel(BaseModelo):
    """Representa o registro de usuario persistido no banco de dados."""

    __tablename__ = "usuario"

    codigoUsuario = Column("Codigo_Usuario", Integer, primary_key=True, autoincrement=True)
    loginUsuario = Column("Login_Usuario", String)
    nomeUsuario = Column("Nome_Usuario", String)
    emailUsuario = Column("Email_Usuario", String)
    codigoUsuarioGrupo = Column(
        "codigo_usuariogrupo",
        Integer,
        ForeignKey("usuariogrupo.codigo_usuariogrupo"),
    )

    def paraRespostaExterna(self) -> Dict[str, Any]:
        """Converte a entidade ORM para o contrato JSON legado da API."""
        return {
            "Codigo_Usuario": self.codigoUsuario,
            "Login_Usuario": self.loginUsuario,
            "Nome_Usuario": self.nomeUsuario,
            "Email_Usuario": self.emailUsuario,
            "codigo_usuariogrupo": self.codigoUsuarioGrupo,
        }


class UsuarioGrupoModel(BaseModelo):
    """Representa o grupo de permissao associado a um usuario."""

    __tablename__ = "usuariogrupo"

    codigoUsuarioGrupo = Column("codigo_usuariogrupo", Integer, primary_key=True, autoincrement=True)
    siglaUsuarioGrupo = Column("Sigla_UsuarioGrupo", String)
    descricaoUsuarioGrupo = Column("Descricao_UsuarioGrupo", String)
    permiteCadastrar = Column("Permite_Cadastrar", Integer)
    permiteAlterar = Column("Permite_Alterar", Integer)
    permiteExcluir = Column("Permite_Excluir", Integer)

    def paraRespostaExterna(self) -> Dict[str, Any]:
        """Converte a entidade ORM para o contrato JSON legado da API."""
        return {
            "codigo_usuariogrupo": self.codigoUsuarioGrupo,
            "Sigla_UsuarioGrupo": self.siglaUsuarioGrupo,
            "Descricao_UsuarioGrupo": self.descricaoUsuarioGrupo,
            "Permite_Cadastrar": bool(self.permiteCadastrar),
            "Permite_Alterar": bool(self.permiteAlterar),
            "Permite_Excluir": bool(self.permiteExcluir),
        }


class MenuAcessoModel(BaseModelo):
    """Representa a relacao de acesso entre grupo de usuario e menu."""

    __tablename__ = "MenuAcesso"

    codigoMenuAcesso = Column("Codigo_MenuAcesso", Integer, primary_key=True, autoincrement=True)
    codigoUsuarioGrupo = Column("Codigo_UsuarioGrupo", Integer, ForeignKey("usuariogrupo.codigo_usuariogrupo"))
    codigoMenu = Column("Codigo_Menu", Integer, ForeignKey("Menu.Codigo_Menu"))