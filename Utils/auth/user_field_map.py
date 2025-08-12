# Mapeamento dos campos do JSON da API para nomes internos usados na sessão

USER_FIELD_MAP = {
    "Codigo_Usuario": "id",
    "Login_Usuario": "name",
    "Nome_Usuario": "full_name",
    "Email_Usuario": "email",
    "codigo_usuariogrupo": "role",  # ou "group_id" se preferir
    # Adicione outros campos conforme necessário
}