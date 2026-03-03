# ====================================================================
# DATA DIALOG - Diálogo de Edição de Dados do Nó
# ====================================================================
"""
Este arquivo contém o diálogo para inserção, importação e visualização
de dados associados a um nó do projeto, com uma interface aprimorada
usando ícones e QSS (Qt Style Sheets).
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QGroupBox,
    QGridLayout, QHBoxLayout, QLineEdit, QPushButton, QCheckBox,
    QTableView, QAbstractItemView, QToolBox, QWidget, QSizePolicy, QStyle
)
# --- NOVA IMPORTAÇÃO ---
from PyQt6.QtGui import QIcon, QPalette
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QTextEdit

import json
import csv
import os
from data import data_map
from utils import migration as migrate_data
from utils import project_config
from datetime import datetime
import shutil
import html

# opcional: usar pandas para Excel quando disponível
try:
    import pandas as pd
    HAS_PANDAS = True
except Exception:
    HAS_PANDAS = False

class DataEntryDialog(QDialog):
    """
    Diálogo para editar, importar e visualizar dados de um nó específico.
    Utiliza um QToolBox estilizado para alternar entre inserção e importação.
    """
    # signal emitted after a successful write: (node_uuid: str, node_data: dict)
    data_changed = pyqtSignal(str, dict)
    
    def __init__(self, parent=None, node_uuid: str = None, project_file: str = None, controller=None):
        super().__init__(parent)

        self.controller = controller  # <-- Adicionar referência ao controller
        self.node_uuid = node_uuid
        # project file selection: explicit param -> stored config -> prompt
        if project_file:
            self.project_file = project_file
            project_config.set_project_file(project_file)
        else:
            self.project_file = project_config.get_project_file(prompt_if_missing=True) or os.path.join(os.path.dirname(__file__), 'teste.json')
        
        self.setWindowTitle("Editor de Dados")
        self.setWindowIcon(QIcon("resources/icone_png.png"))
        self.setFixedSize(500, 400)
        
        # area de resumo (verde) para mostrar o que será adicionado/ignorado/removido
        self.summary_view = QTextEdit()
        self.summary_view.setReadOnly(True)

        app = QApplication.instance()
        if app:
            pal = app.palette()
            self.summary_view.setAutoFillBackground(True)
            self.summary_view.setPalette(pal)
            # manter borda verde mas usar cores do Fusion para fundo/texto
            bg = pal.color(QPalette.ColorRole.Base).name()
            text = pal.color(QPalette.ColorRole.Text).name()
            self.summary_view.setStyleSheet(f"background:{bg}; color:{text}; border: 1px solid #ffffff; padding:6px;")
        else:
            # fallback (mantém comportamento atual se não houver QApplication)
            self.summary_view.setStyleSheet("background:#071b07; color:#9ef29e; border: 1px solid #2ea02e; padding:6px;")
        # permitir que a caixa verde cresça até o final do diálogo
        self.summary_view.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.summary_view.setMinimumHeight(280)

        self._setup_ui()
        self._connect_signals()

        # Estado inicial da UI
        self.group_resumo.hide()

        # Pré-preenche campos a partir do conteúdo atual do nó em project_file
        try:
            self._prefill_node_data()
        except Exception:
            # não atrapalhar a abertura do diálogo se houver problema de leitura
            pass
        
    def _setup_ui(self):
        """Configura a interface do diálogo, incluindo o QToolBox estilizado."""
        main_layout = QVBoxLayout(self)

        # --- QToolBox para alternar entre Inserir e Importar ---
        self.tool_box = QToolBox()
        self.tool_box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        page_inserir = QWidget()
        page_inserir.setLayout(self._create_inserir_layout())

        page_importar = QWidget()
        page_importar.setLayout(self._create_importar_layout())

        # --- Adicionando ícones às páginas ---
        style = self.style()
        icon_inserir = style.standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder)
        icon_importar = style.standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon)
        self.tool_box.addItem(page_inserir, icon_inserir, "Inserir Dados")
        self.tool_box.addItem(page_importar, icon_importar, "Importar de Arquivo")

        # --- Estilizando com QSS ---
        self.tool_box.setObjectName("DataToolBox")
        qss = """
            QToolBox::tab {
                background-color: #e8e8e8;
                border: 1px solid #c5c5c5;
                border-bottom: 1px solid #c5c5c5;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                padding-top: 0px;
                padding-bottom: 0px;
                padding-left: 10px;
                padding-right: 20px;
                font-weight: bold;
                color: #333;
                text-align: left;
            }
            QToolBox::tab:hover {
                background-color: #d1d1f5;
            }
            QToolBox::tab:selected {
                background-color: #ffffff;
                border-bottom: 1px solid #ffffff;
            }
        """
        self.tool_box.setStyleSheet(qss)

        # --- Seção de Resumo dos Dados ---
        self.group_resumo = QGroupBox("Resumo de Dados")
        layout_resumo = QVBoxLayout(self.group_resumo)
        self.table_resumo = QTableView()
        self.table_resumo.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_resumo.setAlternatingRowColors(True)
        layout_resumo.addWidget(self.table_resumo)
        # Mantém o resumo com altura controlada para não "empurrar" os controles
        self.group_resumo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.group_resumo.setMaximumHeight(220)

        # --- Layout: ToolBox + Resumo à esquerda (alinhados ao topo) e botões à direita ---
        content_layout = QHBoxLayout()

        left_vbox = QVBoxLayout()
        left_vbox.setAlignment(Qt.AlignmentFlag.AlignTop)
        left_vbox.addWidget(self.tool_box)
        left_vbox.addWidget(self.group_resumo)
        # summary_view will be placed to the right, below the action buttons
        # evita que os widgets cresçam e empurrem os botões para cima
        left_vbox.addStretch(1)

        # left_vbox ocupa a coluna da esquerda
        content_layout.addLayout(left_vbox, 1)

        # Botões empilhados verticalmente à direita (OK, Cancel, Reset)
        buttons_vbox = QVBoxLayout()
        buttons_vbox.setSpacing(8)
        buttons_vbox.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.btn_ok = QPushButton("OK")
        self.btn_ok.setDefault(True)

        self.btn_cancel = QPushButton("Cancel")

        self.btn_reset = QPushButton("Reset")

        buttons_vbox.addWidget(self.btn_ok)
        buttons_vbox.addWidget(self.btn_cancel)
        buttons_vbox.addWidget(self.btn_reset)

        # --- Ajusta largura dos botões e alinha a caixa de resumo ---
        btns = (self.btn_ok, self.btn_cancel, self.btn_reset)
        # calcula largura base a partir do sizeHint dos botões e adiciona padding
        max_btn_w = max(b.sizeHint().width() for b in btns) + 40
        for b in btns:
            b.setFixedWidth(max_btn_w)

        # coloca a summary_view logo abaixo dos botões com a mesma largura
        # usa setFixedWidth para garantir alinhamento; trocar para setMaximumWidth
        # se preferir comportamento responsivo
        self.summary_view.setFixedWidth(max_btn_w)
        buttons_vbox.addWidget(self.summary_view)
        buttons_vbox.addStretch(1)

        content_layout.addLayout(buttons_vbox)

        # Adiciona o layout de conteúdo ao layout principal
        main_layout.addLayout(content_layout)
        
    def _create_inserir_layout(self) -> QGridLayout:
        layout = QGridLayout()
        self.checkboxes = {
            "barras": QCheckBox("Barras"), "disj_bt": QCheckBox("Disjuntores BT"),
            "disj_mt": QCheckBox("Disjuntores MT"), "fusiveis": QCheckBox("Fusíveis"),
            "chaves_sec": QCheckBox("Chaves Seccionadoras"), "cabos_bt": QCheckBox("Cabos BT"),
            "cabos_mt": QCheckBox("Cabos MT"), "saturacao_tc": QCheckBox("Saturação TC"),
        }
        layout.addWidget(self.checkboxes["barras"], 0, 0); layout.addWidget(self.checkboxes["disj_bt"], 1, 0); layout.addWidget(self.checkboxes["disj_mt"], 2, 0); layout.addWidget(self.checkboxes["fusiveis"], 3, 0)
        layout.addWidget(self.checkboxes["chaves_sec"], 0, 1); layout.addWidget(self.checkboxes["cabos_bt"], 1, 1); layout.addWidget(self.checkboxes["cabos_mt"], 2, 1); layout.addWidget(self.checkboxes["saturacao_tc"], 3, 1)
        self.btn_selecionar_tudo = QPushButton("Selecionar Tudo"); layout.addWidget(self.btn_selecionar_tudo, 4, 0, 1, 2)

        # Área dinâmica para campos por tipo (ex: campos de 'barras')
        self.dynamic_widget = QWidget()
        self.dynamic_layout = QVBoxLayout(self.dynamic_widget)
        self.dynamic_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.dynamic_widget, 5, 0, 1, 2)
        layout.setRowStretch(6, 1)

        # Estruturas para gerenciar campos dinâmicos
        self.dynamic_fields = {}  # tipo -> {campo: QLineEdit}
        self.dynamic_groups = {}  # tipo -> QGroupBox
        return layout

    def _create_importar_layout(self) -> QVBoxLayout:
        """Cria e retorna o layout para a página de importação."""
        layout = QVBoxLayout()

        # reduz margens e espaçamento para aproximar do "Resumo de Dados"
        layout.setContentsMargins(5, 5, 5, 5)  # margem inferior menor
        layout.setSpacing(4)

        # Container para o campo de arquivo e botão
        import_widget = QWidget()
        import_layout = QHBoxLayout(import_widget)
        import_layout.setContentsMargins(0, 0, 0, 0)
        # evitar que o widget de import expanda verticalmente
        import_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.txt_caminho_arquivo = QLineEdit()
        self.txt_caminho_arquivo.setPlaceholderText("Selecione um arquivo Excel...")
        self.txt_caminho_arquivo.setReadOnly(True)

        self.btn_procurar = QPushButton("Procurar...")

        import_layout.addWidget(self.txt_caminho_arquivo)
        import_layout.addWidget(self.btn_procurar)

        layout.addWidget(import_widget)
        # removido o addStretch que criava espaço vazio abaixo do import_widget
        # layout.addStretch(1)

        return layout

    def _connect_signals(self):
        # Conecta os botões verticais às ações do diálogo
        self.btn_ok.clicked.connect(self.handle_ok)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_reset.clicked.connect(self.handle_reset)

        self.btn_selecionar_tudo.clicked.connect(self.selecionar_todos_checkboxes)
        # conecta cada checkbox para controlar campos dinâmicos
        for tipo, cb in self.checkboxes.items():
            cb.stateChanged.connect(lambda state, t=tipo: self._on_tipo_checkbox_changed(t, state))
            # atualizar resumo sempre que o checkbox mudar
            cb.stateChanged.connect(lambda state, t=tipo: self.update_summary())
        self.btn_procurar.clicked.connect(self.handle_procurar_arquivo)
        self.tool_box.currentChanged.connect(self._on_page_changed)

    def handle_reset(self):
        """
        Limpa todos os campos do formulário para seus estados padrão.
        """
        # Limpa todos os checkboxes
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)
        
        # Limpa o campo de texto do caminho do arquivo
        self.txt_caminho_arquivo.clear()
        
        # Opcional: Reseta o QToolBox para a primeira página
        self.tool_box.setCurrentIndex(0)
        
        print("Formulário resetado.")

    def _on_page_changed(self, index: int):
        """
        Alterna a visibilidade do resumo de dados e ajusta o tamanho do diálogo.
        """
        if index == 1:  # Página "Importar"
            self.group_resumo.show()
        else:  # Página "Inserir"
            self.group_resumo.hide()
        # Força o diálogo a se recalcular para o menor tamanho possível
        self.adjustSize()
            
    def selecionar_todos_checkboxes(self):
        todos_marcados = all(cb.isChecked() for cb in self.checkboxes.values())
        novo_estado = not todos_marcados
        for tipo, checkbox in self.checkboxes.items():
            checkbox.setChecked(novo_estado)
            # atualização dos campos dinâmicos é feita pelo slot conectado

    def handle_procurar_arquivo(self):
        # Abre o dialog para escolher arquivo e preenche o campo de caminho
        filtro = "Arquivos (*.xlsx *.xls *.csv *.json);;Todos os arquivos (*)"
        caminho, _ = QFileDialog.getOpenFileName(self, "Selecionar arquivo para importar", os.getcwd(), filtro)
        if not caminho:
            return
        self.txt_caminho_arquivo.setText(caminho)

        # Tenta pré-visualizar/validar o arquivo (não entra em parsing pesado aqui)
        ext = os.path.splitext(caminho)[1].lower()
        if ext in (".xlsx", ".xls") and not HAS_PANDAS:
            QMessageBox.warning(self, "Dependência ausente", "Para importar arquivos Excel é necessário instalar pandas (pip install pandas openpyxl).")
            return
        # Exibe resumo mínimo
        self.group_resumo.show()
        print(f"Arquivo selecionado para importação: {caminho}")

    def _on_tipo_checkbox_changed(self, tipo: str, state: int):
        """Chamado quando um checkbox de tipo é marcado/desmarcado."""
        checked = state == Qt.CheckState.Checked
        self.update_dynamic_fields(tipo, checked)
        # atualizar resumo depois de criar/remover campos
        self.update_summary()

    def update_dynamic_fields(self, tipo: str, adicionar: bool):
        """Adiciona ou remove o grupo de campos dinâmicos para `tipo`."""
        # se adicionar, cria groupbox com campos do schema; se remover, retira do layout
        if adicionar:
            if tipo in self.dynamic_groups:
                return
            schema = data_map.get_schema(tipo)
            if not schema:
                # nada a renderizar
                return
            group = QGroupBox(tipo.capitalize())
            grid = QGridLayout()
            fields_map = {}
            row = 0
            for key, spec in schema.items():
                lbl = QLineEdit()  # usar QLineEdit como rótulo improvisado por simplicidade
                lbl.setReadOnly(True)
                lbl.setText(key)
                edt = QLineEdit()
                # suporte ao novo formato: spec é dict com 'nomeExcel'
                if isinstance(spec, dict):
                    excel_name = spec.get('nomeExcel', '')
                    edt.setPlaceholderText("")
                    edt.setToolTip(excel_name)
                    lbl.setToolTip(excel_name)
                else:
                    edt.setPlaceholderText(str(spec))
                grid.addWidget(lbl, row, 0)
                grid.addWidget(edt, row, 1)
                fields_map[key] = edt
                row += 1
            group.setLayout(grid)
            self.dynamic_layout.addWidget(group)
            self.dynamic_groups[tipo] = group
            self.dynamic_fields[tipo] = fields_map
        else:
            if tipo not in self.dynamic_groups:
                return
            group = self.dynamic_groups.pop(tipo)
            # remove widget do layout
            self.dynamic_layout.removeWidget(group)
            group.deleteLater()
            if tipo in self.dynamic_fields:
                del self.dynamic_fields[tipo]

    def handle_ok(self):
        """Dispatcher para OK: faz importação ou inserção conforme a página atual."""
        idx = self.tool_box.currentIndex()
        if idx == 1:
            # Página Importar
            self.do_import()
        else:
            # Página Inserir (implementação parcial/adiada)
            self.do_insert()
        # Fecha diálogo após operação
        super().accept()

    def do_import(self):
        """Importa o arquivo selecionado e grava seu conteúdo em teste.json -> nó -> data."""
        caminho = self.txt_caminho_arquivo.text().strip()
        if not caminho:
            QMessageBox.warning(self, "Arquivo não selecionado", "Selecione um arquivo para importar antes de continuar.")
            return

        ext = os.path.splitext(caminho)[1].lower()
        try:
            if ext == ".json":
                with open(caminho, "r", encoding="utf-8") as f:
                    dados = json.load(f)
            elif ext == ".csv":
                with open(caminho, newline='', encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    dados = [row for row in reader]
            elif ext in (".xls", ".xlsx"):
                if not HAS_PANDAS:
                    QMessageBox.warning(self, "Dependência ausente", "Instale pandas para importar Excel.")
                    return
                df = pd.read_excel(caminho)
                dados = df.fillna("").to_dict(orient="records")
            else:
                QMessageBox.warning(self, "Formato não suportado", f"Formato de arquivo não suportado: {ext}")
                return
        except Exception as e:
            QMessageBox.critical(self, "Erro ao ler arquivo", f"Falha ao ler o arquivo: {e}")
            return

        # Grava os dados lidos em projeto na chave data do nó (se existir)
        try:
            bak = self.write_to_teste_json(dados)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao gravar JSON", f"Falha ao gravar em teste.json: {e}")
            return

        # After successful write, reload the node data from disk and emit signal
        try:
            arquivo = self.project_file or os.path.join(os.path.dirname(__file__), "teste.json")
            with open(arquivo, 'r', encoding='utf-8') as f:
                projeto = json.load(f)
            node = self.find_node_in_tree(projeto.get('projectTree', {}), self.node_uuid)
            if node is None and self.node_uuid in projeto.get('projectTree', {}):
                node = projeto['projectTree'][self.node_uuid]
            written_data = node.get('data', {}) if node is not None else {}
            try:
                self.data_changed.emit(self.node_uuid, written_data)
            except Exception:
                pass
        except Exception:
            pass

        QMessageBox.information(self, "Importação concluída", "Dados importados e gravados em projeto com sucesso.")

    def find_node_in_tree(self, node_dict, target_uuid):
        """Procura recursivamente pelo nó com a chave target_uuid dentro de node_dict."""
        if target_uuid in node_dict:
            return node_dict[target_uuid]
        for key, val in node_dict.items():
            # cada val pode ter 'nodes'
            if isinstance(val, dict) and 'nodes' in val and isinstance(val['nodes'], dict):
                found = self.find_node_in_tree(val['nodes'], target_uuid)
                if found is not None:
                    return found
        return None

    def label_for(self, tipo: str) -> str:
        """Retorna o texto visível do QCheckBox correspondente à chave interna `tipo`.

        Se não existir um checkbox para a chave, retorna a própria chave.
        """
        cb = getattr(self, 'checkboxes', {}).get(tipo)
        return cb.text() if cb is not None else tipo

    def write_to_teste_json(self, dados):
        """Grava dados no arquivo de projeto (`self.project_file`), fazendo merge-on-write.

        Cria backup com sufixo .bak_YYYYmmdd_HHMMSS se houver alterações e retorna o backup path,
        ou None se nada mudou.
        """
        arquivo = self.project_file or os.path.join(os.path.dirname(__file__), "teste.json")
        if not os.path.exists(arquivo):
            raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")

        with open(arquivo, "r", encoding="utf-8") as f:
            projeto = json.load(f)

        # Espera-se que a árvore esteja em projeto['projectTree']
        if 'projectTree' not in projeto:
            raise KeyError("Estrutura inválida: chave 'projectTree' não encontrada.")

        node = self.find_node_in_tree(projeto['projectTree'], self.node_uuid)
        if node is None:
            # tenta procurar pelo próprio nivel raiz (às vezes node_uuid é a chave direta)
            if self.node_uuid in projeto['projectTree']:
                node = projeto['projectTree'][self.node_uuid]
        if node is None:
            raise KeyError(f"Nó com UUID {self.node_uuid} não encontrado em teste.json")

        # Merge-on-write with change detection
        existing = node.get('data', {}) if isinstance(node.get('data', {}), dict) else {}
        changed = False

        if isinstance(dados, dict):
            for tipo, novo in dados.items():
                antigo = existing.get(tipo)
                if isinstance(novo, dict):
                    if isinstance(antigo, dict):
                        for k, v in novo.items():
                            if v is not None and v != "" and antigo.get(k) != v:
                                antigo[k] = v
                                changed = True
                        merged = antigo
                    else:
                        merged = novo
                        changed = True
                else:
                    if antigo != novo:
                        merged = novo
                        changed = True
                    else:
                        merged = antigo
                existing[tipo] = merged
        else:
            if existing != dados:
                existing = dados
                changed = True

        if changed:
            # create single backup file in project dir (overwrite existing)
            proj_dir = os.path.dirname(arquivo)
            proj_base = os.path.splitext(os.path.basename(arquivo))[0]
            bak = os.path.join(proj_dir, proj_base + '.bak')
            try:
                shutil.copy2(arquivo, bak)
            except Exception:
                bak = None
            node['data'] = existing
            with open(arquivo, "w", encoding="utf-8") as f:
                json.dump(projeto, f, indent=4, ensure_ascii=False)
            # emit signal so controller/model can be updated in-memory
            try:
                self.data_changed.emit(self.node_uuid, existing)
            except Exception:
                pass
            return bak
        return None

    def _prefill_node_data(self):
        """
        Verifica os nós-filho do tipo 'dataType' existentes e marca os checkboxes
        correspondentes no diálogo.
        """
        if not hasattr(self, 'controller') or not self.controller:
            return

        # Usa o controller para buscar os nós de dados filhos existentes
        existing_nodes = self.controller.get_child_data_nodes(self.node_uuid)
        existing_types = {node['dataType'] for node in existing_nodes.values()}

        # Marca os checkboxes para cada tipo encontrado
        for tipo in existing_types:
            if tipo in self.checkboxes:
                self.checkboxes[tipo].setChecked(True)
                
        # Atualiza o resumo visual (adicionar/ignorar/remover)
        self.update_summary()

    def update_summary(self):
        """Atualiza a `summary_view` com o que será adicionado, ignorado e removido."""
        arquivo = self.project_file or os.path.join(os.path.dirname(__file__), 'teste.json')
        existing = {}
        if os.path.exists(arquivo):
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    projeto = json.load(f)
                node = self.find_node_in_tree(projeto.get('projectTree', {}), self.node_uuid)
                if node is None and self.node_uuid in projeto.get('projectTree', {}):
                    node = projeto['projectTree'][self.node_uuid]
                if node is not None:
                    existing = node.get('data', {}) if isinstance(node.get('data', {}), dict) else {}
            except Exception:
                existing = {}

        existing_types = set(existing.keys())
        selected = {t for t, cb in self.checkboxes.items() if cb.isChecked()}

        to_add = sorted(selected - existing_types)
        to_ignore = sorted(selected & existing_types)
        to_remove = sorted(existing_types - selected & set(self.checkboxes.keys()))

        parts = []
        parts.append(f"Adicionar ({len(to_add)}):\n{'\n'.join(self.label_for(t) for t in to_add) if to_add else ''}")
        parts.append(f"Ignorar ({len(to_ignore)}):\n{'\n'.join(self.label_for(t) for t in to_ignore) if to_ignore else ''}")
        parts.append(f"Remover ({len(to_remove)}):\n{'\n'.join(self.label_for(t) for t in to_remove) if to_remove else ''}")

        self.summary_view.setPlainText('\n\n'.join(parts))

    def do_insert(self):
        """
        Compara o estado atual do projeto com os checkboxes selecionados para
        determinar quais nós de dados devem ser adicionados ou removidos.
        Cada operação é confirmada e persistida pelo controller.
        """
        if not hasattr(self, 'controller') or not self.controller:
            QMessageBox.critical(self, "Erro", "Referência ao Controller não encontrada.")
            return

        # 1. Obter estado atual e estado desejado
        selected_types = {tipo for tipo, cb in self.checkboxes.items() if cb.isChecked()}
        
        # Busca os tipos de dados que já existem como filhos do nó atual
        existing_nodes = self.controller.get_child_data_nodes(self.node_uuid)
        existing_types = {node['dataType'] for node in existing_nodes.values()}

        # 2. Calcular o que adicionar e o que remover
        to_add = selected_types - existing_types
        to_remove = existing_types - selected_types

        if not to_add and not to_remove:
            QMessageBox.information(self, "Nenhuma Alteração", "O projeto já está no estado desejado.")
            self.accept()
            return

        # 3. Processar remoções com confirmação
        if to_remove:
            # Pega os nomes de exibição (ex: "Disjuntores BT") para a mensagem
            # Usa um dicionário de tipo -> nome para encontrar o nome correto do nó a ser removido
            type_to_display_name = {node['dataType']: node['displayName'] for node in existing_nodes.values()}
            names_to_remove = "\n".join([type_to_display_name.get(t, t) for t in to_remove])
            
            reply = QMessageBox.question(self, "Confirmar Remoção",
                "Os seguintes tipos de dados serão REMOVIDOS:\n\n" + names_to_remove + "\n\nDeseja continuar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                for tipo in to_remove:
                    # Remove o nó pelo tipo (mais direto que buscar UUID)
                    self.controller.remove_data_node(self.node_uuid, tipo)
        
        # 4. Processar adições
        if to_add:
            for tipo in to_add:
                display_name = self.label_for(tipo) # "Disjuntores BT"
                self.controller.add_data_node(self.node_uuid, display_name, tipo)

        # 5. Fechar o diálogo
        self.accept()