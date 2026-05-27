from __future__ import annotations

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship, synonym

from Models.Base import BasePostgres


roteirosModulos = Table(
    "Tb_Docs_RelacaoRoteirosModulos",
    BasePostgres.metadata,
    Column("RoteiroId", Integer, ForeignKey("Tb_Docs_Roteiros.Id"), primary_key=True),
    Column("ModuloId", String(100), ForeignKey("Tb_Docs_Modulos.Id"), primary_key=True),
)


class Modulo(BasePostgres):
    __tablename__ = "Tb_Docs_Modulos"

    Id = Column(String(100), primary_key=True)
    Nome = Column(String(255), nullable=False)
    Descricao = Column(Text, nullable=True)
    Icone = Column(String(50), nullable=True)
    Status = Column(String(50), nullable=True)
    UsuarioUltimaEdicao = Column(String(100), nullable=True)
    DataUltimaEdicao = Column(String(100), nullable=True)
    UsuarioEdicaoPendente = Column(String(100), nullable=True)
    DataEdicaoPendente = Column(String(100), nullable=True)
    VersaoAtual = Column(String(50), nullable=True)
    AprovadoPor = Column(String(100), nullable=True)
    AprovadoEm = Column(String(100), nullable=True)
    Is_Restrito = Column(Boolean, default=False)

    PalavrasChave = relationship(
        "PalavraChave",
        back_populates="Modulo",
        cascade="all, delete-orphan",
        lazy="joined",
    )
    HistoricoEdicoes = relationship(
        "HistoricoEdicao",
        back_populates="Modulo",
        cascade="all, delete-orphan",
        lazy="joined",
    )
    Roteiros = relationship(
        "Roteiro",
        secondary="Tb_Docs_RelacaoRoteirosModulos",
        back_populates="Modulos",
        lazy="joined",
    )
    Relacionados = relationship(
        "Modulo",
        secondary="Tb_Docs_ModulosRelacionados",
        primaryjoin=lambda: Modulo.Id == ModuloRelacionado.ModuloId,
        secondaryjoin=lambda: Modulo.Id == ModuloRelacionado.RelacionadoId,
        backref="RelacionadoPor",
        lazy="joined",
    )

    id = synonym("Id")
    nome = synonym("Nome")
    descricao = synonym("Descricao")
    icone = synonym("Icone")
    status = synonym("Status")
    ultima_edicao_user = synonym("UsuarioUltimaEdicao")
    ultima_edicao_data = synonym("DataUltimaEdicao")
    pending_edit_user = synonym("UsuarioEdicaoPendente")
    pending_edit_data = synonym("DataEdicaoPendente")
    current_version = synonym("VersaoAtual")
    last_approved_by = synonym("AprovadoPor")
    last_approved_on = synonym("AprovadoEm")
    is_restrito = synonym("Is_Restrito")
    palavras_chave = synonym("PalavrasChave")
    edit_history = synonym("HistoricoEdicoes")
    roteiros = synonym("Roteiros")
    relacionados = synonym("Relacionados")

    @property
    def InfoEdicaoPendente(self):
        return {"data": self.DataEdicaoPendente, "user": self.UsuarioEdicaoPendente}

    @property
    def pending_edit_info(self):
        return self.InfoEdicaoPendente


class PalavraChave(BasePostgres):
    __tablename__ = "Tb_Docs_PalavrasChave"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    ModuloId = Column(String(100), ForeignKey("Tb_Docs_Modulos.Id"), nullable=False)
    Palavra = Column(String(100), nullable=False)

    Modulo = relationship("Modulo", back_populates="PalavrasChave")

    id = synonym("Id")
    modulo_id = synonym("ModuloId")
    palavra = synonym("Palavra")
    modulo = synonym("Modulo")


class ModuloRelacionado(BasePostgres):
    __tablename__ = "Tb_Docs_ModulosRelacionados"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    ModuloId = Column(String(100), ForeignKey("Tb_Docs_Modulos.Id"), nullable=False)
    RelacionadoId = Column(String(100), ForeignKey("Tb_Docs_Modulos.Id"), nullable=False)

    id = synonym("Id")
    modulo_id = synonym("ModuloId")
    relacionado_id = synonym("RelacionadoId")


class HistoricoEdicao(BasePostgres):
    __tablename__ = "Tb_Docs_HistoricoEdicoes"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    ModuloId = Column(String(100), ForeignKey("Tb_Docs_Modulos.Id"), nullable=False)
    Evento = Column(String(100))
    Versao = Column(String(50))
    Editor = Column(String(100))
    Aprovador = Column(String(100))
    RegistradoEm = Column(String(100))
    ArquivoBackupDocumentacao = Column(String(255))
    ArquivoBackupDocumentacaoTecnica = Column(String(255))

    Modulo = relationship("Modulo", back_populates="HistoricoEdicoes")

    id = synonym("Id")
    modulo_id = synonym("ModuloId")
    event = synonym("Evento")
    version = synonym("Versao")
    editor = synonym("Editor")
    approver = synonym("Aprovador")
    timestamp = synonym("RegistradoEm")
    backup_file_doc = synonym("ArquivoBackupDocumentacao")
    backup_file_tech = synonym("ArquivoBackupDocumentacaoTecnica")
    modulo = synonym("Modulo")


class PalavraGlobal(BasePostgres):
    __tablename__ = "Tb_Docs_PalavrasGlobais"

    Palavra = Column(String(100), primary_key=True)
    Descricao = Column(Text)

    palavra = synonym("Palavra")
    descricao = synonym("Descricao")