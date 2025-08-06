import json
import sqlite3

def migrar_dados():
    """Lê o config.json e popula o banco de dados luftdocs.db."""
    try:
        # Carregar dados do arquivo JSON
        with open(r'data/config.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Conectar ao banco de dados
        conn = sqlite3.connect('luftdocs.db')
        cursor = conn.cursor()

        # 1. Migrar Módulos
        for modulo in data['modulos']:
            # Inserir dados na tabela 'modulos'
            cursor.execute('''
                INSERT OR REPLACE INTO modulos (
                    id, nome, descricao, icone, status,
                    ultima_edicao_user, ultima_edicao_data,
                    pending_edit_user, pending_edit_data,
                    current_version, last_approved_by, last_approved_on
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                modulo['id'],
                modulo['nome'],
                modulo['descricao'],
                modulo.get('icone'),
                modulo.get('status'),
                modulo.get('ultima_edicao', {}).get('user'),
                modulo.get('ultima_edicao', {}).get('data'),
                modulo.get('pending_edit_info', {}).get('user'),
                modulo.get('pending_edit_info', {}).get('data'),
                modulo.get('version_info', {}).get('current_version'),
                modulo.get('version_info', {}).get('last_approved_by'),
                modulo.get('version_info', {}).get('last_approved_on')
            ))

            # Limpar dados antigos para evitar duplicatas
            cursor.execute("DELETE FROM palavras_chave WHERE modulo_id = ?", (modulo['id'],))
            cursor.execute("DELETE FROM modulos_relacionados WHERE modulo_id = ?", (modulo['id'],))
            cursor.execute("DELETE FROM historico_edicao WHERE modulo_id = ?", (modulo['id'],))


            # 2. Migrar Palavras-Chave
            for palavra in modulo.get('palavras_chave', []):
                cursor.execute('''
                    INSERT INTO palavras_chave (modulo_id, palavra) VALUES (?, ?)
                ''', (modulo['id'], palavra))

            # 3. Migrar Módulos Relacionados
            for relacionado in modulo.get('relacionados', []):
                cursor.execute('''
                    INSERT INTO modulos_relacionados (modulo_id, relacionado_id) VALUES (?, ?)
                ''', (modulo['id'], relacionado))

            # 4. Migrar Histórico de Edição
            for historico in modulo.get('edit_history', []):
                cursor.execute('''
                    INSERT INTO historico_edicao (
                        modulo_id, event, version, editor, approver, timestamp,
                        backup_file_doc, backup_file_tech
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    modulo['id'],
                    historico.get('event'),
                    historico.get('version'),
                    historico.get('editor') or historico.get('user'), # Para o evento 'criado'
                    historico.get('approver'),
                    historico.get('timestamp'),
                    historico.get('backup_file_doc'),
                    historico.get('backup_file_tech')
                ))

        # 5. Migrar Palavras Globais
        cursor.execute("DELETE FROM palavras_globais") # Limpa a tabela para evitar duplicatas
        for palavra, descricao in data.get('palavras_globais', {}).items():
            cursor.execute('''
                INSERT OR REPLACE INTO palavras_globais (palavra, descricao) VALUES (?, ?)
            ''', (palavra, descricao))


        # Salvar as alterações e fechar a conexão
        conn.commit()
        conn.close()

        print("Migração de dados do 'config.json' para 'luftdocs.db' concluída com sucesso!")

    except FileNotFoundError:
        print("Erro: O ficheiro 'config.json' não foi encontrado. Verifique o caminho.")
    except Exception as e:
        print(f"Ocorreu um erro durante a migração: {e}")

# Executar a função de migração
if __name__ == '__main__':
    migrar_dados()