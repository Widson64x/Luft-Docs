from __future__ import annotations

import secrets


def GerarTokenAleatorio(tamanhoBytes: int = 64) -> str:
    """Gera um token aleatorio utilizando base64 URL-safe."""
    return secrets.token_urlsafe(tamanhoBytes)