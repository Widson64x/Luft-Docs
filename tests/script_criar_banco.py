# script_criar_banco.py
import sqlite3

# --- 1. Definição Central dos Módulos do Sistema ---
#
# Com base na sua imagem. Sinta-se à vontade para ajustar nomes, descrições e ícones.
# O 'id' deve ser o mesmo nome da pasta para manter a consistência.
# O 'link' será gerado automaticamente a partir do 'id'.
#
ALL_MODULES_DATA = [
    {
        'id': 'agendamento',
        'name': 'Agendamento',
        'desc': 'Gestão de agendas, tarefas e compromissos da equipe.',
        'icon': 'bi bi-calendar-event'
    },
    {
        'id': 'coordenacao',
        'name': 'Coordenação',
        'desc': 'Ferramentas para coordenar e monitorar operações e projetos.',
        'icon': 'bi bi-diagram-3'
    },
    {
        'id': 'recebimento-intec',
        'name': 'Recebimento Intec',
        'desc': 'Processamento e gestão de documentos e recebimentos da Intec.',
        'icon': 'bi bi-box-arrow-in-down'
    },
    {
        'id': 'relacao-edi',
        'name': 'Relação EDI',
        'desc': 'Monitoramento e gestão de arquivos de Intercâmbio Eletrônico de Dados (EDI).',
        'icon': 'bi bi-file-earmark-code'
    },
    {
        'id': 'relacao-parceiros',
        'name': 'Relação de Parceiros',
        'desc': 'Cadastro, consulta e gerenciamento de parceiros comerciais.',
        'icon': 'bi bi-people-fill'
    },
    {
        'id': 'tarifas-complementares',
        'name': 'Tarifas Complementares',
        'desc': 'Cálculo e gestão de tarifas, taxas e valores adicionais.',
        'icon': 'bi bi-cash-coin'
    },
    {
        'id': 'telas-informa',
        'name': 'Telas Informativas',
        'desc': 'Visualização de dashboards, gráficos e telas de informação gerencial.',
        'icon': 'bi bi-tv'
    },
    # Módulo genérico para TI
    {
        'id': 'gerenciamento-usuarios',
        'name': 'Gerenciamento de Usuários',
        'desc': 'Crie, edite e gerencie os acessos dos usuários ao sistema.',
        'icon': 'bi bi-person-badge'
    }
]

# --- 2. Definição dos Planos de Estudo por Grupo ---
#
# Mapeia quais módulos cada grupo deve aprender.
# Use os 'nomes' dos módulos definidos na lista acima.
#
RECOMMENDATIONS_MAP = {
    'COMERCIAL BASICO': [
        'Agendamento',
        'Tarifas Complementares'
    ],
    'TORRE': [
        'Coordenação',
        'Agendamento',
        'Recebimento Intec',
        'Relação EDI',
        'Telas Informativas',
        'Tarifas Complementares'
    ],
    'GRUPO TI': [
        'Relação EDI',
        'Telas Informativas',
        'Coordenação'
    ]
}

# --- 3. Lógica do Banco de Dados (não precisa alterar) ---

def setup_database():
    """Conecta, limpa e popula o banco de dados com os novos planos."""
    conn = sqlite3.connect('recommendations.db')
    cursor = conn.cursor()

    print("Conectado ao banco de dados 'recommendations.db'.")

    # Limpa dados antigos para recomeçar do zero
    print("Limpando dados antigos...")
    cursor.execute("DELETE FROM recommendations")
    cursor.execute("DELETE FROM user_groups")
    cursor.execute("DELETE FROM learning_modules")
    print("Tabelas limpas com sucesso.")

    try:
        # Prepara os dados dos módulos, gerando o link automaticamente
        modules_to_add = [
            {
                'name': mod['name'],
                'desc': mod['desc'],
                'link': f"/modulo/{mod['id']}" # Gera o link padronizado
            }
            for mod in ALL_MODULES_DATA
        ]

        # Inserir todos os Módulos de Aprendizado
        print("\nInserindo novos módulos de aprendizado...")
        cursor.executemany(
            "INSERT INTO learning_modules (module_name, description, link_to_module) VALUES (:name, :desc, :link)",
            modules_to_add
        )
        print(f"{len(modules_to_add)} módulos inseridos.")

        # Inserir os Grupos de Usuário
        print("\nInserindo novos grupos de usuário...")
        groups_to_add = [{'group_name': name} for name in RECOMMENDATIONS_MAP.keys()]
        cursor.executemany(
            "INSERT INTO user_groups (group_name) VALUES (:group_name)",
            groups_to_add
        )
        print(f"{len(groups_to_add)} grupos inseridos.")

        # Criar as Recomendações
        print("\nCriando mapeamento de recomendações...")
        cursor.execute("SELECT id, module_name FROM learning_modules")
        module_ids = {name: id for id, name in cursor.fetchall()}

        cursor.execute("SELECT id, group_name FROM user_groups")
        group_ids = {name: id for id, name in cursor.fetchall()}

        recommendations_to_add = []
        for group_name, module_names in RECOMMENDATIONS_MAP.items():
            if group_name not in group_ids:
                print(f"AVISO: Grupo '{group_name}' não encontrado no banco. Pulando recomendações.")
                continue
            
            group_id = group_ids[group_name]
            for module_name in module_names:
                if module_name not in module_ids:
                    print(f"AVISO: Módulo '{module_name}' não encontrado no banco. Pulando recomendação.")
                    continue
                
                module_id = module_ids[module_name]
                recommendations_to_add.append({'group_id': group_id, 'module_id': module_id})
        
        cursor.executemany(
            "INSERT INTO recommendations (group_id, module_id) VALUES (:group_id, :module_id)",
            recommendations_to_add
        )
        print(f"{len(recommendations_to_add)} recomendações criadas.")

        conn.commit()
        print("\nBanco de dados atualizado com sucesso!")

    except sqlite3.Error as e:
        print(f"Ocorreu um erro: {e}")
        conn.rollback()

    finally:
        conn.close()
        print("Conexão fechada.")


# Executa a função principal
if __name__ == "__main__":
    setup_database()