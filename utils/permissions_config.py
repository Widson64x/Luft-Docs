# /utils/permissions_config.py
"""
Arquivo de configuração central para permissões.
Armazena listas e configurações que podem ser compartilhadas por diferentes rotas.
"""

# Defina aqui os IDs dos módulos que são considerados restritos.
# A permissão 'can_see_restricted_module' será necessária para visualizá-los.
MODULOS_RESTRITOS = [
    'template',
    'relacao-parceiros',
]

MODULOS_TECNICOS_VISIVEIS = [
    'tarifas-complementares',
]
