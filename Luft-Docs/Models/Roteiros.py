from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, TIMESTAMP
from sqlalchemy.orm import relationship, synonym

from Models.Base import BasePostgres


class Roteiro(BasePostgres):
    __tablename__ = "Tb_Docs_Roteiros"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    Titulo = Column(String(255), nullable=False)
    Descricao = Column(Text, nullable=True)
    Tipo = Column(String(50), nullable=False, default="link")
    Conteudo = Column(Text, nullable=False)
    Icone = Column(String(50), nullable=True, default="bi-play-circle")
    Ordem = Column(Integer, default=0)
    CriadoEm = Column(DateTime(timezone=True))
    AtualizadoEm = Column(DateTime(timezone=True))

    Modulos = relationship(
        "Modulo",
        secondary="Tb_Docs_RelacaoRoteirosModulos",
        back_populates="Roteiros",
        lazy="subquery",
    )
    LogsAuditoria = relationship(
        "LogAuditoriaRoteiro",
        back_populates="Roteiro",
        cascade="all, delete-orphan",
    )

    id = synonym("Id")
    titulo = synonym("Titulo")
    descricao = synonym("Descricao")
    tipo = synonym("Tipo")
    conteudo = synonym("Conteudo")
    icone = synonym("Icone")
    ordem = synonym("Ordem")
    created_at = synonym("CriadoEm")
    updated_at = synonym("AtualizadoEm")
    modulos = synonym("Modulos")
    audit_logs = synonym("LogsAuditoria")

    def __repr__(self):
        return f"<Roteiro {self.Id}: {self.Titulo}>"

    @staticmethod
    def _iso(dt):
        if not dt:
            return None
        if isinstance(dt, str):
            return dt.replace(" ", "T") + "Z"
        iso = dt.isoformat()
        return iso.replace("+00:00", "Z")

    def to_dict(self):
        return {
            "id": self.Id,
            "titulo": self.Titulo,
            "descricao": self.Descricao,
            "tipo": self.Tipo,
            "conteudo": self.Conteudo,
            "icone": self.Icone,
            "ordem": self.Ordem,
            "created_at": self._iso(self.CriadoEm),
            "updated_at": self._iso(self.AtualizadoEm),
        }


class LogAuditoriaRoteiro(BasePostgres):
    __tablename__ = "Tb_Docs_LogAuditoriaRoteiros"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    RoteiroId = Column(Integer, ForeignKey("Tb_Docs_Roteiros.Id"), nullable=False)
    UsuarioId = Column(Integer, nullable=False)
    NomeUsuario = Column(String(100), nullable=False)
    Acao = Column(String(50), nullable=False)
    RegistradoEm = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)

    Roteiro = relationship("Roteiro", back_populates="LogsAuditoria")

    id = synonym("Id")
    roteiro_id = synonym("RoteiroId")
    user_id = synonym("UsuarioId")
    user_name = synonym("NomeUsuario")
    action = synonym("Acao")
    timestamp = synonym("RegistradoEm")
    roteiro = synonym("Roteiro")

    def __repr__(self):
        return f"<LogAuditoriaRoteiro {self.Id} - Acao: {self.Acao} por {self.NomeUsuario}>"