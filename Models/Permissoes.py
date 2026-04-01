from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from Models.Base import BaseSqlServer


class UsuarioBanco(BaseSqlServer):
    __tablename__ = "usuario"

    Codigo_Usuario = Column(Integer, primary_key=True, autoincrement=True)
    Login_Usuario = Column(String(100))
    Nome_Usuario = Column(String(255))
    Email_Usuario = Column(String(255))
    codigo_usuariogrupo = Column(Integer, ForeignKey("usuariogrupo.codigo_usuariogrupo"))

    GrupoRel = relationship("UsuarioGrupoBanco", foreign_keys=[codigo_usuariogrupo], lazy="joined")

    def __repr__(self):
        return f"<UsuarioBanco {self.Login_Usuario}>"


class UsuarioGrupoBanco(BaseSqlServer):
    __tablename__ = "usuariogrupo"

    codigo_usuariogrupo = Column(Integer, primary_key=True, autoincrement=True)
    Sigla_UsuarioGrupo = Column(String(50))
    Descricao_UsuarioGrupo = Column(String(255))

    def __repr__(self):
        return f"<UsuarioGrupoBanco {self.Sigla_UsuarioGrupo}>"


class Tb_Permissao(BaseSqlServer):
    __tablename__ = "Tb_Permissao"
    __table_args__ = (
        UniqueConstraint("Id_Sistema", "Chave_Permissao", name="uq_sistema_chave_permissao"),
    )

    Id_Permissao = Column(Integer, primary_key=True, autoincrement=True)
    Id_Sistema = Column(Integer, nullable=False)
    Chave_Permissao = Column(String(100), nullable=False)
    Descricao_Permissao = Column(String(255))
    Categoria_Permissao = Column(String(50))

    def __repr__(self):
        return f"<Tb_Permissao {self.Chave_Permissao}>"


class Tb_PermissaoGrupo(BaseSqlServer):
    __tablename__ = "Tb_PermissaoGrupo"

    Id_Vinculo = Column(Integer, primary_key=True, autoincrement=True)
    Codigo_UsuarioGrupo = Column(Integer, nullable=False)
    Id_Permissao = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Tb_PermissaoGrupo grupo={self.Codigo_UsuarioGrupo} perm={self.Id_Permissao}>"


class Tb_PermissaoUsuario(BaseSqlServer):
    __tablename__ = "Tb_PermissaoUsuario"

    Id_Vinculo = Column(Integer, primary_key=True, autoincrement=True)
    Codigo_Usuario = Column(Integer, nullable=False)
    Id_Permissao = Column(Integer, nullable=False)
    Conceder = Column(Boolean, default=True)

    def __repr__(self):
        return (
            f"<Tb_PermissaoUsuario user={self.Codigo_Usuario} "
            f"perm={self.Id_Permissao} conceder={self.Conceder}>"
        )


class Tb_LogAcesso(BaseSqlServer):
    __tablename__ = "Tb_LogAcesso"

    Id_Log = Column(Integer, primary_key=True, autoincrement=True)
    Id_Sistema = Column(Integer, nullable=True)
    Id_Usuario = Column(Integer, nullable=True)
    Nome_Usuario = Column(String(150))
    Rota_Acessada = Column(String(200))
    Metodo_Http = Column(String(10))
    Ip_Origem = Column(String(50))
    Permissao_Exigida = Column(String(100))
    Acesso_Permitido = Column(Boolean)
    Data_Hora = Column(DateTime, default=datetime.utcnow)
    Parametros_Requisicao = Column(Text, nullable=True)
    Resposta_Acao = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Tb_LogAcesso {self.Id_Log} user={self.Nome_Usuario} permitido={self.Acesso_Permitido}>"