# /utils/permissions_config.py
"""
Arquivo de configuração central para permissões.
Armazena listas e configurações que podem ser compartilhadas por diferentes rotas.
"""

# Defina aqui os IDs dos módulos que são considerados restritos.
# A permissão 'can_see_restricted_module' será necessária para visualizá-los.

# Só os ++ que vão poder ver esses módulos, só a nata. 
MODULOS_RESTRITOS = [
    'template',
    'relacao-parceiros',
    'testando'
]

MODULOS_TECNICOS_VISIVEIS = [
    'tarifas-complementares',
]
