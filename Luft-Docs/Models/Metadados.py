from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship, synonym

from Models.Base import BasePostgres


class CategoriaTagMeta(BasePostgres):
    __tablename__ = "Tb_Docs_CategoriasTagsMeta"

    Id = Column(Integer, primary_key=True)
    Nome = Column(String(100), unique=True, nullable=False)
    Descricao = Column(Text, nullable=True)

    Tags = relationship(
        "TagMeta",
        back_populates="Categoria",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    id = synonym("Id")
    nome = synonym("Nome")
    descricao = synonym("Descricao")
    tags = synonym("Tags")

    def __repr__(self):
        return f"<CategoriaTagMeta {self.Nome}>"


class TagMeta(BasePostgres):
    __tablename__ = "Tb_Docs_TagsMeta"

    Id = Column(Integer, primary_key=True)
    Tag = Column(String(50), unique=True, nullable=False)
    Descricao = Column(Text, nullable=False)
    CategoriaId = Column(Integer, ForeignKey("Tb_Docs_CategoriasTagsMeta.Id"), nullable=False)

    Categoria = relationship("CategoriaTagMeta", back_populates="Tags")
    ObjetosAssociados = relationship(
        "RelacaoObjetoTagMeta",
        back_populates="TagRelacionada",
        cascade="all, delete-orphan",
    )

    id = synonym("Id")
    tag = synonym("Tag")
    descricao = synonym("Descricao")
    categoria_id = synonym("CategoriaId")
    categoria = synonym("Categoria")
    objetos_associados = synonym("ObjetosAssociados")

    def __repr__(self):
        return f"<TagMeta {self.Tag}>"


class RelacaoObjetoTagMeta(BasePostgres):
    __tablename__ = "Tb_Docs_RelacaoObjetosTagsMeta"

    Id = Column(Integer, primary_key=True)
    NomeObjeto = Column(String(255), nullable=False)
    TipoObjeto = Column(String(50), nullable=False, default="TABLE")
    TagId = Column(Integer, ForeignKey("Tb_Docs_TagsMeta.Id"), nullable=False)

    TagRelacionada = relationship("TagMeta", back_populates="ObjetosAssociados")

    id = synonym("Id")
    nome_objeto = synonym("NomeObjeto")
    tipo_objeto = synonym("TipoObjeto")
    tag_id = synonym("TagId")
    tag = synonym("TagRelacionada")

    def __repr__(self):
        tag_repr = self.TagRelacionada.Tag if self.TagRelacionada else "N/A"
        return f"<RelacaoObjetoTagMeta Objeto:{self.NomeObjeto} -> Tag:{tag_repr}>"