import sys
import sqlite3
import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QLabel, QLineEdit, QPushButton, QHBoxLayout, 
                             QFrame, QGroupBox, QMenu, QAction)
from PyQt5.QtGui import QFont, QIcon, QColor
from PyQt5.QtCore import Qt, QSize

# --- CONFIGURAÇÃO ---
DATABASE_FILE = 'DATA/luftdocs.db'
# --------------------

class DeveloperDashboardV2(QMainWindow):
    def __init__(self):
        super().__init__()
        # Conexão com o banco em modo 'autocommit' para edições in-line
        self.db_conn = sqlite3.connect(DATABASE_FILE, isolation_level=None)
        self.init_ui()
        self.apply_styles()
        self.show_all_tables()

    def init_ui(self):
        self.setWindowTitle("WIKIDOCS - Developer Dashboard V2.0")
        self.setGeometry(100, 100, 1600, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel)

        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 1)

        self.show()

    def create_left_panel(self):
        """Cria o painel de navegação esquerdo com os botões de query."""
        left_frame = QFrame()
        left_frame.setObjectName("leftPanel")
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(10)

        title_label = QLabel("Dashboard V2")
        title_label.setObjectName("titleLabel")
        left_layout.addWidget(title_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar em tudo...")
        self.search_input.returnPressed.connect(self.run_search)
        left_layout.addWidget(self.search_input)

        # Botões de Ação Principais
        btn_fav = QPushButton("⭐ Favoritos")
        btn_fav.clicked.connect(self.show_favorites)
        left_layout.addWidget(btn_fav)

        btn_all = QPushButton("🗂️ Todas as Tabelas")
        btn_all.clicked.connect(self.show_all_tables)
        left_layout.addWidget(btn_all)
        
        btn_undocumented = QPushButton("✏️ Não Documentadas")
        btn_undocumented.clicked.connect(self.show_undocumented_tables)
        left_layout.addWidget(btn_undocumented)
        
        btn_health = QPushButton("🩺 Saúde do Schema")
        btn_health.clicked.connect(self.show_health_check)
        left_layout.addWidget(btn_health)

        module_groupbox = QGroupBox("Filtrar por Módulo")
        module_layout = QVBoxLayout()
        
        query = "SELECT DISTINCT nome_tag FROM Lft_Sys_TagsComponente WHERE categoria = 'Operacao' ORDER BY nome_tag;"
        modules = self.execute_query(query)
        for module in modules:
            module_name = module[0]
            btn = QPushButton(f"⚙️ {module_name}")
            btn.clicked.connect(lambda checked, m=module_name: self.filter_by_module(m))
            module_layout.addWidget(btn)
        
        module_groupbox.setLayout(module_layout)
        left_layout.addWidget(module_groupbox)

        left_layout.addStretch()
        return left_frame

    def create_right_panel(self):
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(10, 25, 10, 10)

        self.results_table = QTableWidget()
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setObjectName("resultsTable")
        
        # Sinais para novas funcionalidades
        self.results_table.itemChanged.connect(self.handle_item_changed)
        self.results_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_table.customContextMenuRequested.connect(self.show_context_menu)
        self.results_table.cellClicked.connect(self.handle_cell_click)

        right_layout.addWidget(self.results_table)
        return right_frame

    # --- Métodos de Ação dos Botões (Queries) ---
    def get_base_query(self):
        """Retorna a query base com todos os joins, para ser reutilizada."""
        return """
            SELECT r.nome_tabela, r.is_favorited, b.nome_tag, t.nome_tag, o.nome_tag, r.nome_entidade, r.descricao
            FROM Lft_Sys_Relacionamentos r
            LEFT JOIN Lft_Sys_TagsBase b ON r.id_tag_base = b.id
            LEFT JOIN Lft_Sys_TagsComponente t ON r.id_tag_tipo = t.id
            LEFT JOIN Lft_Sys_TagsComponente o ON r.id_tag_operacao = o.id
        """

    def show_all_tables(self):
        self.prepare_standard_table_headers()
        query = self.get_base_query() + " ORDER BY r.nome_tabela;"
        self.run_and_populate_table(query)

    def show_favorites(self):
        self.prepare_standard_table_headers()
        query = self.get_base_query() + " WHERE r.is_favorited = 1 ORDER BY r.nome_tabela;"
        self.run_and_populate_table(query)

    def show_undocumented_tables(self):
        self.prepare_standard_table_headers()
        query = self.get_base_query() + " WHERE r.descricao IS NULL OR r.descricao = '' ORDER BY r.nome_tabela;"
        self.run_and_populate_table(query)

    def filter_by_module(self, module_name):
        self.prepare_standard_table_headers()
        query = self.get_base_query() + " WHERE o.nome_tag = ? ORDER BY r.nome_tabela;"
        self.run_and_populate_table(query, [module_name])
    
    def run_search(self):
        self.prepare_standard_table_headers()
        like_term = f"%{self.search_input.text()}%"
        query = self.get_base_query() + " WHERE r.nome_tabela LIKE ? OR r.nome_entidade LIKE ? OR r.descricao LIKE ? OR o.nome_tag LIKE ?"
        self.run_and_populate_table(query, [like_term, like_term, like_term, like_term])

    def show_health_check(self):
        # Implementação da verificação de saúde... (igual à anterior)
        pass # Mantido para brevidade, mas a lógica é a mesma

    # --- Lógica das Novas Funcionalidades ---

    def handle_cell_click(self, row, column):
        """Lida com cliques nas células, especialmente na coluna 'Favorito'."""
        # Coluna do favorito é a 1
        if column == 1:
            table_name = self.results_table.item(row, 0).text()
            current_status = self.results_table.item(row, 1).text()
            
            new_status = 1 if current_status == '☆' else 0
            new_icon = '⭐' if new_status == 1 else '☆'

            query = "UPDATE Lft_Sys_Relacionamentos SET is_favorited = ? WHERE nome_tabela = ?"
            self.execute_query(query, [new_status, table_name])
            
            # Atualiza o ícone sem recarregar a tabela inteira
            self.results_table.blockSignals(True)
            self.results_table.item(row, 1).setText(new_icon)
            self.results_table.blockSignals(False)

    def handle_item_changed(self, item):
        """Lida com a edição in-line da descrição."""
        # Coluna da descrição é a 6
        if item.column() == 6:
            row = item.row()
            table_name = self.results_table.item(row, 0).text()
            new_description = item.text()
            
            query = "UPDATE Lft_Sys_Relacionamentos SET descricao = ? WHERE nome_tabela = ?"
            self.execute_query(query, [new_description, table_name])
            print(f"Descrição da tabela '{table_name}' atualizada.")

    def show_context_menu(self, pos):
        """Mostra o menu de contexto ao clicar com o botão direito."""
        selected_item = self.results_table.itemAt(pos)
        if not selected_item:
            return

        row = selected_item.row()
        table_name = self.results_table.item(row, 0).text()

        menu = QMenu()
        menu.setObjectName("contextMenu")
        
        generate_sql_menu = menu.addMenu("🤖 Gerar SQL")
        generate_python_menu = menu.addMenu("🐍 Gerar Modelo Python")

        sql_actions = ['SELECT', 'INSERT', 'UPDATE', 'DELETE']
        for action_name in sql_actions:
            action = QAction(action_name, self)
            action.triggered.connect(lambda checked, t=table_name, a=action_name: self.generate_sql(t, a))
            generate_sql_menu.addAction(action)

        py_model_action = QAction("Gerar Classe", self)
        py_model_action.triggered.connect(lambda checked, t=table_name: self.generate_python_model(t))
        generate_python_menu.addAction(py_model_action)

        menu.exec_(self.results_table.viewport().mapToGlobal(pos))
    
    def generate_sql(self, table_name, action_type):
        """Gera código SQL para a tabela selecionada."""
        cursor = self.db_conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        
        sql = ""
        if action_type == 'SELECT':
            sql = f"SELECT {', '.join(columns)} FROM {table_name} WHERE ...;"
        elif action_type == 'INSERT':
            placeholders = ', '.join(['?' for _ in columns])
            sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders});"
        elif action_type == 'UPDATE':
            setters = ' = ?, '.join(columns[1:]) + ' = ?'
            sql = f"UPDATE {table_name} SET {setters} WHERE {columns[0]} = ?;"
        elif action_type == 'DELETE':
            sql = f"DELETE FROM {table_name} WHERE {columns[0]} = ?;"
            
        QApplication.clipboard().setText(sql)
        print(f"Código SQL '{action_type}' para '{table_name}' copiado para a área de transferência.")

    def generate_python_model(self, table_name):
        """Gera uma classe Python simples para a tabela."""
        cursor = self.db_conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Converte o nome da tabela (ex: Lft_Tb_Perm_Usuarios) para um nome de classe (PermUsuarios)
        class_name = "".join([part.capitalize() for part in table_name.split('_')[2:]])

        # Cria os argumentos do __init__
        init_args = ", ".join([f"{col}=None" for col in columns])
        # Cria as atribuições self.x = x
        assignments = "\n        ".join([f"self.{col} = {col}" for col in columns])
        
        py_code = f"""
class {class_name}:
    def __init__(self, {init_args}):
        {assignments}

    def __repr__(self):
        return f"<{class_name}({columns[0]}={{self.{columns[0]}}})>"
"""
        QApplication.clipboard().setText(py_code.strip())
        print(f"Classe Python '{class_name}' copiada para a área de transferência.")

    # --- Métodos Utilitários ---
    def prepare_standard_table_headers(self):
        self.results_table.blockSignals(True)
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels(["Nome da Tabela", "Fav", "Base", "Tipo", "Módulo", "Entidade", "Descrição"])
        self.results_table.setColumnWidth(1, 40) # Coluna de Favoritos
        self.results_table.blockSignals(False)
        
    def run_and_populate_table(self, query, params=[]):
        data = self.execute_query(query, params)
        self.results_table.blockSignals(True) # Bloqueia sinais para evitar disparos durante o preenchimento
        self.results_table.setRowCount(0)
        if not data:
            self.results_table.blockSignals(False)
            return
        
        self.results_table.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):
            for col_idx, col_data in enumerate(row_data):
                # Coluna do favorito
                if col_idx == 1:
                    is_fav = col_data == 1
                    icon = '⭐' if is_fav else '☆'
                    item = QTableWidgetItem(icon)
                    item.setTextAlignment(Qt.AlignCenter)
                else:
                    item = QTableWidgetItem(str(col_data) if col_data is not None else "")
                
                # Permite edição apenas na coluna de descrição (6)
                if col_idx != 6:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)

                self.results_table.setItem(row_idx, col_idx, item)
        
        self.results_table.resizeColumnsToContents()
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.blockSignals(False)

    def execute_query(self, query, params=[]):
        try:
            cursor = self.db_conn.cursor()
            cursor.execute(query, params)
            # Para SELECTs, retorna dados. Para outros, apenas executa.
            if query.strip().upper().startswith("SELECT"):
                 return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Erro de banco de dados: {e}")
            return []
    
    def apply_styles(self):
        self.setStyleSheet("""
            /* ... (O mesmo QSS da versão anterior, com adição para o Menu) ... */
            QMenu {
                background-color: #2c313a;
                color: #abb2bf;
                border: 1px solid #61afef;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px 8px 20px;
            }
            QMenu::item:selected {
                background-color: #61afef;
                color: #21252b;
            }
            QMenu::separator {
                height: 1px;
                background: #3b4048;
                margin: 5px 0px;
            }
            /* Restante do CSS anterior... */
            QMainWindow, #leftPanel, #titleLabel, QTableWidget, QHeaderView::section,
            QTableWidget::item, QLineEdit, QPushButton, QGroupBox, QScrollBar {
                 /* Cole aqui o QSS da resposta anterior para manter o estilo */
            }
            QMainWindow {
                background-color: #282c34;
            }
            #leftPanel {
                background-color: #21252b;
                border-right: 1px solid #1c1f24;
            }
            #titleLabel {
                font-size: 22pt;
                font-weight: bold;
                color: #ffffff;
                padding-bottom: 10px;
            }
            #resultsTable { /* Target specific table */
                background-color: #282c34;
                color: #abb2bf;
                gridline-color: #3b4048;
                font-size: 10pt;
                border: none;
            }
            QHeaderView::section {
                background-color: #21252b;
                color: #ffffff;
                padding: 10px;
                font-size: 11pt;
                font-weight: bold;
                border: 1px solid #3b4048;
            }
            #resultsTable::item {
                padding: 6px;
                border-bottom: 1px solid #3b4048;
            }
            #resultsTable::item:selected {
                background-color: #61afef;
                color: #21252b;
            }
            #resultsTable::item:alternate {
                 background-color: #2c313a;
            }
            QLineEdit {
                background-color: #21252b;
                color: #abb2bf;
                border: 1px solid #3b4048;
                padding: 8px;
                font-size: 11pt;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #2c313a;
                color: #abb2bf;
                font-weight: bold;
                border: 1px solid #3b4048;
                padding: 10px;
                font-size: 11pt;
                border-radius: 4px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #3e4451;
                border: 1px solid #61afef;
            }
            QGroupBox {
                color: #61afef;
                font-size: 11pt;
                font-weight: bold;
                border: 1px solid #3b4048;
                border-radius: 4px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                left: 10px;
            }
            QScrollBar:vertical {
                border: none;
                background: #282c34;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: #3e4451;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

    def closeEvent(self, event):
        self.db_conn.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    dashboard = DeveloperDashboardV2()
    sys.exit(app.exec_())