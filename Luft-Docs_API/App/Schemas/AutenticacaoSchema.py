"""Schemas de entrada relacionados a autenticacao da API."""

from pydantic import BaseModel, Field


class RequisicaoRevogacaoToken(BaseModel):
    """Representa o corpo esperado no endpoint de revogacao de token."""

    token: str = Field(..., min_length=1, description="Token JWT que deve ser invalidado.")