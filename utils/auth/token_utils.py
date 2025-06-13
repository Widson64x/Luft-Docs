import secrets

def gerar_token_aleatorio(tamanho_bytes: int = 64) -> str:
    """
    Gera um token aleatório (string em base64 URL-safe).
    Por padrão, utiliza 32 bytes de entropia.
    """
    return secrets.token_urlsafe(tamanho_bytes)