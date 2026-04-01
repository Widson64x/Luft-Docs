from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, String, Text, TIMESTAMP, func
from sqlalchemy.orm import synonym

from Models.Base import BasePostgres


class ReporteBug(BasePostgres):
    __tablename__ = "Tb_Docs_ReportesBug"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    UsuarioId = Column(Integer, nullable=False)
    TipoReporte = Column(String(50), nullable=False)
    EntidadeAlvo = Column(String(100), nullable=True)
    CategoriaErro = Column(String(100), nullable=True)
    Descricao = Column(Text, nullable=False)
    Status = Column(String(50), nullable=False, default="aberto")
    CriadoEm = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    id = synonym("Id")
    user_id = synonym("UsuarioId")
    report_type = synonym("TipoReporte")
    target_entity = synonym("EntidadeAlvo")
    error_category = synonym("CategoriaErro")
    description = synonym("Descricao")
    status = synonym("Status")
    created_at = synonym("CriadoEm")

    def __repr__(self):
        return f"<ReporteBug {self.Id} por {self.UsuarioId}>"


class FeedbackIA(BasePostgres):
    __tablename__ = "Tb_Docs_FeedbackIA"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    RespostaId = Column(String, nullable=False)
    UsuarioId = Column(String, nullable=False)
    PerguntaUsuario = Column(Text, nullable=True)
    ModeloUtilizado = Column(String(100), nullable=True)
    FontesContexto = Column(Text, nullable=True)
    Avaliacao = Column(Integer, nullable=True)
    Comentario = Column(Text, nullable=True)
    RegistradoEm = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)

    feedback_id = synonym("Id")
    response_id = synonym("RespostaId")
    user_id = synonym("UsuarioId")
    user_question = synonym("PerguntaUsuario")
    model_used = synonym("ModeloUtilizado")
    context_sources = synonym("FontesContexto")
    rating = synonym("Avaliacao")
    comment = synonym("Comentario")
    timestamp = synonym("RegistradoEm")

    def __repr__(self):
        return f"<FeedbackIA {self.Id} for response {self.RespostaId}>"


class AcessoDocumento(BasePostgres):
    __tablename__ = "Tb_Docs_LogAcessosDocumentos"

    DocumentoId = Column(String(255), primary_key=True)
    QuantidadeAcessos = Column(Integer, nullable=False, default=1)
    UltimoAcessoEm = Column(
        TIMESTAMP,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    document_id = synonym("DocumentoId")
    access_count = synonym("QuantidadeAcessos")
    last_access = synonym("UltimoAcessoEm")


class LogBusca(BasePostgres):
    __tablename__ = "Tb_Docs_LogBuscas"

    TermoBusca = Column(String(255), primary_key=True)
    QuantidadeBuscas = Column(Integer, nullable=False, default=1)
    UltimaBuscaEm = Column(
        TIMESTAMP,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    query_term = synonym("TermoBusca")
    search_count = synonym("QuantidadeBuscas")
    last_searched = synonym("UltimaBuscaEm")


class AvaliacaoDocumento(BasePostgres):
    __tablename__ = "Tb_Docs_AvaliacoesDocumentos"

    Id = Column(Integer, primary_key=True)
    DocumentoId = Column(String(100), ForeignKey("Tb_Docs_Modulos.Id"))
    Avaliacao = Column(Integer)
    Comentario = Column(Text)
    Sugestoes = Column(Text)
    Trechos = Column(Text)
    MudancasSolicitadas = Column(Text)

    id = synonym("Id")
    document_id = synonym("DocumentoId")
    rating = synonym("Avaliacao")
    feedback = synonym("Comentario")
    suggestions = synonym("Sugestoes")
    techos = synonym("Trechos")
    changes = synonym("MudancasSolicitadas")