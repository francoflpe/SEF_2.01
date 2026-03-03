# ====================================================================
# CONTROLLER - Orquestrador da Aplicação (Padrão MVC)
# ====================================================================
"""
Este arquivo contém o Controller da aplicação e o ponto de entrada principal.
O Controller coordena a interação entre a View (interface) e o Model (dados).
"""

import sys, os
import json
import pandas as pd
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox, QDialog, QMenu
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QUndoStack
from PyQt6.QtCore import Qt, QObject, QTranslator, QLibraryInfo, QLocale, QStandardPaths

from core.main_view import MainView
from core.project_model import ProjectModel
from components.project_metadata_dialog import ProjectMetadataDialog
from components.data_entry_dialog import DataEntryDialog
from core.commands import RenameNodeCommand
from data.pandas_model import PandasModel


class MainController(QObject):
    """
    Controller da aplicação no padrão MVC.
    Orquestra a comunicação entre a View (MainView) e o Model (ProjectModel).
    """
    
    def __init__(self):
        super().__init__()
        """
        Construtor do MainController.
        Instancia a View e o Model, e conecta os sinais aos slots.
        """
        # Instancia a View (interface gráfica)
        self.view = MainView()
        
        # Instancia o Model (dados)
        self.model = ProjectModel()
        
        # Inicializa o modelo da árvore do explorador
        self.tree_model = QStandardItemModel()
        
        # Define o modelo na view antes de conectar sinais
        self.view.tree_view.setModel(self.tree_model)
        
        # Inicializa a pilha de desfazer/refazer
        self.undo_stack = QUndoStack(self)
        
        # Conecta os sinais da View aos métodos do Controller
        self._connect_signals()
        
        # Flag para ignorar temporariamente o sinal itemChanged
        self._ignore_item_changed = False
        
        # Atualiza o título inicial
        self._update_window_title()
    
    def _connect_signals(self):
        """
        Conecta os sinais emitidos pela View aos métodos manipuladores (slots) do Controller.
        """
        self.view.createProjectClicked.connect(self.handle_create_project)
        self.view.openProjectClicked.connect(self.handle_open_project)
        self.view.saveProjectClicked.connect(self.handle_save_project)
        self.view.saveAsProjectClicked.connect(self.handle_save_as_project)
        self.view.exitRequested.connect(self.handle_exit)
        self.view.closeRequested.connect(self.handle_close_request)
        
        # Conecta os sinais de copiar e colar
        self.view.copyNodeClicked.connect(self.handle_copy_node)
        self.view.pasteNodeClicked.connect(self.handle_paste_node)
        
        # Conecta o sinal de menu de contexto do QTreeView
        self.view.tree_view.customContextMenuRequested.connect(self.show_tree_context_menu)
        
        # Conecta o sinal de mudança de seleção na árvore
        self.view.tree_view.selectionModel().selectionChanged.connect(self.handle_tree_selection_changed)
        
        # Conecta o sinal de item alterado (para detectar edição de nomes)
        self.tree_model.itemChanged.connect(self.handle_item_changed)
        
        # Conecta os sinais de controle de visibilidade do explorador
        self.view.explorerToggleRequested.connect(self.handle_toggle_explorer)
        self.view.explorerVisibilityChanged.connect(self.handle_explorer_visibility_changed)
        
        # Conecta as ações de desfazer/refazer ao QUndoStack
        self.view.acao_desfazer.triggered.connect(self.undo_stack.undo)
        self.view.acao_refazer.triggered.connect(self.undo_stack.redo)
        
        # Conecta os sinais do QUndoStack para habilitar/desabilitar as ações
        self.undo_stack.canUndoChanged.connect(self.view.acao_desfazer.setEnabled)
        self.undo_stack.canRedoChanged.connect(self.view.acao_refazer.setEnabled)

        self.view.deleteKeyPressed.connect(self.handle_delete_key_press)
        self.tree_model.itemChanged.connect(self.handle_item_changed)
    
    def handle_create_project(self):
        """
        Manipulador para a ação de criar um novo projeto.
        Abre um diálogo para salvar um novo arquivo JSON, coleta metadados e cria o projeto.
        """
        # Obtém o diretório "Documentos" do usuário como diretório padrão
        default_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
        
        # Abre um diálogo para escolher onde salvar o novo projeto
        file_path, _ = QFileDialog.getSaveFileName(
            self.view,
            "Criar Novo Projeto",
            default_dir,
            "Projetos SEF (*.json);;Todos os Arquivos (*)"
        )
        
        # Se o usuário forneceu um caminho
        if file_path:
            # Adiciona a extensão .json se não foi fornecida
            if not file_path.endswith('.json'):
                file_path += '.json'
            
            # Abre o diálogo de metadados
            metadata_dialog = ProjectMetadataDialog(self.view)
            
            # Executa o diálogo de forma modal
            if metadata_dialog.exec() == QDialog.DialogCode.Accepted:
                # Obtém os metadados do diálogo
                metadata = metadata_dialog.get_data()
                
                # Cria e salva o novo projeto no Model com os metadados
                project_data = self.model.create_and_save_new_project(file_path, metadata)
                
                if project_data:
                    self.undo_stack.clear()

                    # Atualiza a barra de status na View
                    self.view.update_status_message(f"Projeto criado e salvo: {self.model.project_name}")
                    
                    # Atualiza o explorador de projeto
                    self._update_tree_from_project_data(project_data)
                    
                    # Torna o explorador visível
                    self.view.show_explorer()
                    
                    # Atualiza o estado do menu
                    self.view.set_explorer_menu_checked(True)
                    
                    # Atualiza o título da janela
                    self._update_window_title()
                else:
                    # Exibe mensagem de erro
                    QMessageBox.critical(
                        self.view,
                        "Erro",
                        "Não foi possível criar o projeto."
                    )
                    self.view.update_status_message("Erro ao criar projeto")
            else:
                # Usuário cancelou o diálogo de metadados
                self.view.update_status_message("Criação de projeto cancelada")
    
    def handle_open_project(self):
        """
        Manipulador para a ação de abrir um projeto existente.
        Exibe um diálogo de seleção de arquivo JSON, carrega os dados e atualiza a View.
        """
        # Abre um diálogo para selecionar o arquivo
        file_path, _ = QFileDialog.getOpenFileName(
            self.view,
            "Abrir Projeto",
            "",
            "Projetos SEF (*.json);;Todos os Arquivos (*)"
        )
        
        # Se o usuário selecionou um arquivo
        if file_path:
            # Carrega o projeto no Model
            project_data = self.model.load_project(file_path)
            
            if project_data:
                self.undo_stack.clear()

                # Reconstrói a árvore com os dados carregados
                self._update_tree_from_project_data(project_data)
                
                # Atualiza a barra de status
                self.view.update_status_message(f"Projeto aberto: {self.model.project_name}")
                
                # Torna o explorador visível
                self.view.show_explorer()
                
                # Atualiza o estado do menu
                self.view.set_explorer_menu_checked(True)
            else:
                # Exibe mensagem de erro
                QMessageBox.critical(
                    self.view,
                    "Erro",
                    "Não foi possível abrir o projeto.\nVerifique se o arquivo é um projeto válido."
                )
                self.view.update_status_message("Erro ao abrir projeto")            
            # Atualiza o título da janela
            self._update_window_title()
    
    def handle_save_project(self):
        """
        Salva o projeto atual. Se não há um caminho definido, chama "Salvar Como".
        """
        # Verifica se há um projeto aberto
        if not self.model.project_path:
            self.handle_save_as_project()
            return
        
        # Salva o projeto
        success = self.model.save_project(self.model.project_path)
        
        if success:
            self.view.update_status_message(f"Projeto salvo: {self.model.project_name}")
            self._update_window_title()
        else:
            QMessageBox.critical(
                self.view,
                "Erro",
                "Não foi possível salvar o projeto."
            )
            self.view.update_status_message("Erro ao salvar projeto")
    
    def handle_save_as_project(self):
        """
        Salva o projeto em um novo caminho.
        """
        # Verifica se há um projeto aberto
        if not self.model.project_data:
            QMessageBox.warning(
                self.view,
                "Aviso",
                "Não há um projeto aberto para salvar."
            )
            return
        
        # Abre um diálogo para escolher onde salvar
        file_path, _ = QFileDialog.getSaveFileName(
            self.view,
            "Salvar Projeto Como",
            "",
            "Projetos SEF (*.json);;Todos os Arquivos (*)"
        )
        
        # Se o usuário forneceu um caminho
        if file_path:
            # Adiciona a extensão .json se não foi fornecida
            if not file_path.endswith('.json'):
                file_path += '.json'
            
            # Salva o projeto no novo caminho
            success = self.model.save_project(file_path)
            
            if success:
                self.view.update_status_message(f"Projeto salvo como: {self.model.project_name}")
                self._update_window_title()
            else:
                QMessageBox.critical(
                    self.view,
                    "Erro",
                    "Não foi possível salvar o projeto."
                )
                self.view.update_status_message("Erro ao salvar projeto")
    
    def handle_close_request(self, event):
        """
        Manipulador para a solicitação de fechamento da janela.
        Verifica se há alterações não salvas e pergunta ao usuário o que fazer.
        
        Args:
            event: QCloseEvent - evento de fechamento da janela
        """
        # Verifica se há alterações não salvas
        if not self.model.is_dirty:
            # Não há alterações, pode fechar normalmente
            event.accept()
            return
        
        # Há alterações não salvas, exibe o diálogo de confirmação
        reply = QMessageBox.question(
            self.view,
            "Salvar Alterações?",
            "Seu projeto tem alterações não salvas. Deseja salvá-las antes de sair?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save
        )
        
        if reply == QMessageBox.StandardButton.Save:
            # Usuário escolheu salvar
            # Verifica se há um caminho de projeto definido
            if not self.model.project_path:
                # Não há caminho, precisa usar "Salvar Como"
                file_path, _ = QFileDialog.getSaveFileName(
                    self.view,
                    "Salvar Projeto Como",
                    "",
                    "Projetos SEF (*.json);;Todos os Arquivos (*)"
                )
                
                # Se o usuário cancelou o diálogo de salvar
                if not file_path:
                    # Cancela o fechamento
                    event.ignore()
                    return
                
                # Adiciona a extensão .json se não foi fornecida
                if not file_path.endswith('.json'):
                    file_path += '.json'
                
                # Salva o projeto no novo caminho
                success = self.model.save_project(file_path)
            else:
                # Já há um caminho, salva diretamente
                success = self.model.save_project(self.model.project_path)
            
            # Verifica se o salvamento foi bem-sucedido
            if success:
                # Salvo com sucesso, pode fechar
                event.accept()
            else:
                # Erro ao salvar, cancela o fechamento
                QMessageBox.critical(
                    self.view,
                    "Erro",
                    "Não foi possível salvar o projeto. O fechamento foi cancelado."
                )
                event.ignore()
        
        elif reply == QMessageBox.StandardButton.Discard:
            # Usuário escolheu não salvar, fecha descartando as alterações
            event.accept()
        
        else:
            # Usuário cancelou, não fecha
            event.ignore()
    
    def handle_copy_node(self):
        """
        Copia o nó selecionado para a área de transferência.
        """
        # Obtém o índice atual selecionado
        current_index = self.view.tree_view.currentIndex()
        
        if not current_index.isValid():
            QMessageBox.information(
                self.view,
                "Copiar",
                "Selecione um item para copiar."
            )
            return
        
        # Obtém o item
        item = self.tree_model.itemFromIndex(current_index)
        if not item:
            return
        
        # Obtém o UUID do item
        item_uuid = item.data(Qt.ItemDataRole.UserRole)
        
        if item_uuid is None:
            return
        
        # Obtém o snapshot do nó
        node_snapshot = self.model.get_node_snapshot(item_uuid)
        
        if node_snapshot:
            # Converte para JSON e coloca na área de transferência
            clipboard = QApplication.clipboard()
            clipboard.setText(json.dumps(node_snapshot, ensure_ascii=False, indent=2))
            self.view.update_status_message(f"Item '{item.text()}' copiado")
        else:
            QMessageBox.warning(
                self.view,
                "Erro",
                "Não foi possível copiar o item."
            )
    
    def handle_paste_node(self):
        """
        Cola um nó da área de transferência como subitem do item selecionado.
        """
        # Obtém o índice atual selecionado
        current_index = self.view.tree_view.currentIndex()
        
        if not current_index.isValid():
            QMessageBox.information(
                self.view,
                "Colar",
                "Selecione um item pai onde colar."
            )
            return
        
        # Obtém o item pai
        parent_item = self.tree_model.itemFromIndex(current_index)
        if not parent_item:
            return
        
        # Obtém o UUID e logicalId do pai
        parent_uuid = parent_item.data(Qt.ItemDataRole.UserRole)
        parent_logical_id = parent_item.data(Qt.ItemDataRole.UserRole + 1)
        
        if parent_uuid is None:
            return
        
        # NOVA REGRA: Verifica se o pai é um nó folha (node-X.Y)
        # Nós folha NÃO podem ter filhos
        if '.' in parent_logical_id and parent_logical_id != 'root':
            QMessageBox.warning(
                self.view,
                "Operação Não Permitida",
                "Nós do tipo 'node-X.Y' são nós terminais (folhas) e não podem ter filhos.\n"
                "Apenas 'root' e nós do tipo 'node-X' podem ter subitens."
            )
            return
        
        # Lê o conteúdo da área de transferência
        clipboard = QApplication.clipboard()
        clipboard_text = clipboard.text()
        
        if not clipboard_text:
            QMessageBox.information(
                self.view,
                "Colar",
                "A área de transferência está vazia."
            )
            return
        
        try:
            # Tenta parsear como JSON
            node_data = json.loads(clipboard_text)
            
            # Pega o nome do nó copiado
            node_name = node_data.get('displayName', 'Novo Nó')
            
            # Gera um nome único
            unique_name = self._generate_unique_name(parent_item, node_name)
            
            # Adiciona o nó diretamente (sem comando, operação permanente)
            project_data = self.model.add_node_to_json(parent_uuid, unique_name)
            
            if project_data:
                # Salva imediatamente no arquivo
                if self.model.save_project():
                    # Atualiza a UI
                    self._update_tree_from_project_data(project_data)
                    self._update_window_title()
                    
                    self.view.update_status_message(f"Item '{unique_name}' colado")
                else:
                    QMessageBox.critical(
                        self.view,
                        "Erro",
                        "Não foi possível salvar o projeto."
                    )
            else:
                QMessageBox.warning(
                    self.view,
                    "Erro",
                    "Não foi possível colar o item."
                )
            
        except json.JSONDecodeError:
            QMessageBox.warning(
                self.view,
                "Erro",
                "O conteúdo da área de transferência não é um nó válido."
            )
    
    def _update_window_title(self):
        """
        Atualiza o título da janela com o nome do projeto e indicador de modificação.
        """
        if self.model.project_name:
            # CORREÇÃO: Adicionado o placeholder '[*]' ao título
            title = f"{self.model.project_name}[*] - SEF-2.01"
        else:
            # CORREÇÃO: Adicionado o placeholder '[*]' ao título padrão
            title = "SEF-2.01[*]"
        
        # Atualiza o título na view
        self.view.update_window_title(title)
        
        # Define o estado modificado (para exibir [*] se houver mudanças não salvas)
        self.view.setWindowModified(self.model.is_dirty)   

    def handle_exit(self):
        """
        Manipulador para a ação de sair da aplicação.
        Fecha a janela principal, encerrando a aplicação.
        """
        self.view.close()
    
    def _update_tree_from_project_data(self, project_data: dict):
        """
        Atualiza o modelo da árvore com base nos dados do projeto.
        
        Args:
            project_data: Dicionário com os dados do projeto
        """
        # Limpa o modelo atual
        self._ignore_item_changed = True
        self.tree_model.clear()
        
        # Obtém a árvore do projeto
        project_tree = project_data.get('projectTree', {})
        
        # Itera sobre os nós raiz (normalmente haverá apenas um)
        for root_uuid, root_data in project_tree.items():
            root_display_name = root_data.get('displayName', root_uuid)
            root_logical_id = root_data.get('logicalId', 'root')
            
            # Cria o item raiz
            root_item = QStandardItem(root_display_name)
            root_item.setEditable(False)  # Item raiz não é editável
            root_item.setData(root_uuid, role=Qt.ItemDataRole.UserRole)  # UUID
            root_item.setData(root_logical_id, role=Qt.ItemDataRole.UserRole + 1)  # logicalId
            
            # Adiciona filhos recursivamente
            nodes = root_data.get('nodes', {})
            if nodes:
                self._build_tree_recursive(root_item, nodes)
            
            # Adiciona o item raiz ao modelo
            self.tree_model.appendRow(root_item)
        
        # Atualiza a view
        self.view.update_explorer_model(self.tree_model)
        self._ignore_item_changed = False
    
    def _build_tree_recursive(self, parent_item: QStandardItem, nodes_dict: dict):
        """
        Constrói a árvore recursivamente a partir de um dicionário de nós.
        
        Args:
            parent_item: Item pai no QStandardItemModel
            nodes_dict: Dicionário com os nós filhos (chave = UUID, valor = dados do nó)
        """
        for node_uuid, node_data in nodes_dict.items():
            # Obtém o nome de exibição e logicalId do nó
            display_name = node_data.get('displayName', node_uuid)
            logical_id = node_data.get('logicalId', '')
            
            # Cria o item
            child_item = QStandardItem(display_name)
            child_item.setEditable(True)  # Permite edição
            child_item.setData(node_uuid, role=Qt.ItemDataRole.UserRole)  # Armazena o UUID
            child_item.setData(logical_id, role=Qt.ItemDataRole.UserRole + 1)  # Armazena o logicalId
            
            parent_item.appendRow(child_item)
            
            # Se tem filhos, processa recursivamente
            sub_nodes = node_data.get('nodes', {})
            if sub_nodes:
                self._build_tree_recursive(child_item, sub_nodes)
    
    def show_tree_context_menu(self, position):
        """
        Exibe o menu de contexto ao clicar com botão direito na árvore.
        
        Args:
            position: Posição do clique
        """
        # Obtém o índice do item clicado
        index = self.view.tree_view.indexAt(position)
        
        # Se um item válido foi clicado
        if index.isValid():
            # Obtém o item e seu logicalId
            item = self.tree_model.itemFromIndex(index)
            logical_id = item.data(Qt.ItemDataRole.UserRole + 1) if item else ''
            item_uuid = item.data(Qt.ItemDataRole.UserRole) if item else None
            
            # Cria o menu de contexto
            context_menu = QMenu()
            
            # Se for um nó de dados do tipo node-X (não root, não node-X.Y), adiciona opção de editar dados
            edit_data_action = None
            if item_uuid and logical_id.startswith('node-') and self.model.is_data_node(item_uuid):
                edit_data_action = context_menu.addAction("Editar/Visualizar Dados...")
                context_menu.addSeparator()
            
            # Adiciona a ação "Adicionar Subitem"
            add_action = context_menu.addAction("Adicionar Subitem")
            
            # NOVA REGRA: Desabilita "Adicionar Subitem" para nós folha (node-X.Y)
            # Nós folha são identificados por ter um ponto no logicalId (exceto 'root')
            if '.' in logical_id and logical_id != 'root':
                add_action.setEnabled(False)
            
            # Adiciona separador
            context_menu.addSeparator()
            
            # Adiciona a ação "Renomear" (com atalho F2)
            rename_action = context_menu.addAction("Renomear")
            rename_action.setShortcut("F2")
            
            # Adiciona a ação "Excluir"
            delete_action = context_menu.addAction("Excluir")
            delete_action.setShortcut("Delete")  # Atalho pela tecla Delete
            
            # Desabilita "Excluir" para o nó raiz
            if logical_id == 'root':
                rename_action.setText("Editar Dados do Projeto")
                delete_action.setEnabled(False)
            
            # Executa o menu e verifica qual ação foi selecionada
            action = context_menu.exec(self.view.tree_view.viewport().mapToGlobal(position))
            
            if edit_data_action is not None and action == edit_data_action:
                self.handle_edit_node_data(index)
            elif action == add_action:
                self.handle_add_subitem(index)
            elif action == rename_action:
                if logical_id == 'root':
                    self.handle_edit_project_metadata()
                else:
                    self.handle_rename_item(index)
            elif action == delete_action:
                self.handle_delete_item(index)
    
    def handle_edit_node_data(self, index):
        """
        Abre o diálogo de edição de dados para o nó selecionado.
        
        Args:
            index: QModelIndex do item selecionado
        """
        # Obtém o item do modelo
        item = self.tree_model.itemFromIndex(index)
        
        if not item:
            return
        
        # Obtém o UUID do item
        item_uuid = item.data(Qt.ItemDataRole.UserRole)
        
        if item_uuid is None:
            return
        
        # Abre o diálogo de edição de dados
        dialog = DataEntryDialog(self.view, node_uuid=item_uuid, controller=self)

        result = dialog.exec()

        # Após o diálogo fechar, recarrega o projeto a partir do arquivo
        # usado pelo diálogo para manter o ProjectModel em memória sincronizado
        try:
            proj_file = getattr(dialog, 'project_file', None)
            if proj_file and os.path.exists(proj_file):
                loaded = self.model.load_project(proj_file)
                if loaded:
                    # Atualiza a árvore e a UI para refletir mudanças externas
                    self._update_tree_from_project_data(self.model.project_data)
                    self.view.update_status_message(f"Projeto recarregado após edição de dados: {self.model.project_name}")
        except Exception:
            # Não interromper a aplicação se o reload falhar
            pass
    
    def handle_tree_selection_changed(self, selected, deselected):
        """
        Chamado quando a seleção no QTreeView muda.
        Verifica se o nó selecionado é um nó de dados e exibe seus dados na QTableView.
        """
        indexes = selected.indexes()
        if not indexes:
            # Se nada estiver selecionado, limpa a tabela
            self.view.table_view.setModel(None)
            return

        # Pega o primeiro item selecionado
        index = indexes[0]
        item = self.tree_model.itemFromIndex(index)
        
        if not item:
            return

        # Recupera o UUID e busca o nó
        node_uuid = item.data(Qt.ItemDataRole.UserRole)
        node, _ = self.model._find_node_by_uuid(node_uuid)

        if node and 'dataType' in node:
            # É um nó de dados (como "Barras", "Cabos BT")
            data_dict = node.get('data', {})
            
            # Converte o dicionário para um DataFrame do Pandas
            # Usamos orient='index' para ter os campos como linhas
            df = pd.DataFrame.from_dict(data_dict, orient='index', columns=['Valor'])
            df.index.name = "Campo"
            
            # Cria o PandasModel e o define na QTableView
            pandas_model = PandasModel(df)
            self.view.table_view.setModel(pandas_model)
            self.view.table_view.resizeColumnsToContents()  # Ajusta largura das colunas
        else:
            # Não é um nó de dados, limpa a tabela
            self.view.table_view.setModel(None)
    
    def handle_add_subitem(self, parent_index):
        """
        Adiciona um subitem ao item selecionado na árvore.
        Nova regra: root e node-X podem ter múltiplos filhos, mas node-X.Y não pode ter filhos.
        IMPORTANTE: Operação permanente que salva diretamente no arquivo.
        
        Args:
            parent_index: QModelIndex do item pai
        """
        # Obtém o item pai do modelo
        parent_item = self.tree_model.itemFromIndex(parent_index)
        
        if not parent_item:
            return
        
        # Obtém o UUID e logicalId do pai
        parent_uuid = parent_item.data(Qt.ItemDataRole.UserRole)
        parent_logical_id = parent_item.data(Qt.ItemDataRole.UserRole + 1)
        
        if parent_uuid is None:
            return
        
        # NOVA REGRA: Verifica se o pai é um nó folha (node-X.Y)
        # Nós folha NÃO podem ter filhos
        if '.' in parent_logical_id and parent_logical_id != 'root':
            QMessageBox.warning(
                self.view,
                "Operação Não Permitida",
                "Nós do tipo 'node-X.Y' são nós terminais (folhas) e não podem ter filhos.\n"
                "Apenas 'root' e nós do tipo 'node-X' podem ter subitens."
            )
            return
        
        # NOVA VERIFICAÇÃO: Se o pai tem dados, avisar que eles serão perdidos
        if self.model.get_node_data(parent_uuid):
            reply = QMessageBox.question(
                self.view,
                "Aviso de Exclusão de Dados",
                "Este item contém dados. Adicionar um subitem irá converter este item em um nó estrutural "
                "e seus dados associados serão permanentemente excluídos. Deseja continuar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                self.view.update_status_message("Operação cancelada")
                return
            
            # Limpa os dados do nó pai
            if not self.model.clear_node_data(parent_uuid):
                QMessageBox.critical(
                    self.view,
                    "Erro",
                    "Não foi possível limpar os dados do nó."
                )
                return
        
        # Gera o nome padrão único
        new_name = self._generate_unique_name(parent_item, "Novo Subitem")
        
        # Adiciona o nó diretamente (sem comando, operação permanente)
        project_data = self.model.add_node_to_json(parent_uuid, new_name)
        
        if project_data:
            # Salva imediatamente no arquivo
            if self.model.save_project():
                # Atualiza a UI
                self._update_tree_from_project_data(project_data)
                self._update_window_title()
                
                # Expande o item pai para mostrar o novo filho
                self.view.tree_view.expandAll()
                
                self.view.update_status_message("Subitem adicionado com sucesso")
            else:
                QMessageBox.critical(
                    self.view,
                    "Erro",
                    "Não foi possível salvar o projeto."
                )
        else:
            QMessageBox.warning(
                self.view,
                "Erro",
                "Não foi possível adicionar o subitem."
            )

    def handle_edit_project_metadata(self):
        """
        Abre o diálogo de metadados para edição.
        """
        if not self.model.project_data:
            QMessageBox.warning(self.view, "Aviso", "Nenhum projeto aberto para editar.")
            return

        # Cria o diálogo
        metadata_dialog = ProjectMetadataDialog(self.view)
        
        # Pré-preenche o diálogo com os dados atuais
        current_metadata = self.model.project_data.get("projectMetadata", {})
        metadata_dialog.cs_input.setText(current_metadata.get("CS", ""))
        metadata_dialog.cliente_input.setText(current_metadata.get("cliente", ""))
        
        # Executa o diálogo
        if metadata_dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = metadata_dialog.get_data()
            if new_data:
                # Atualiza os dados no modelo
                success = self.model.update_project_metadata(new_data)
                
                if success:
                    # Salva as alterações
                    self.model.save_project()
                    # Atualiza a UI (título da janela e árvore)
                    self._update_tree_from_project_data(self.model.project_data)
                    self._update_window_title()
                    self.view.update_status_message("Dados do projeto atualizados.")
                else:
                    QMessageBox.critical(self.view, "Erro", "Não foi possível atualizar os metadados.")
    
    def add_data_node(self, parent_uuid: str, display_name: str, data_type: str) -> bool:
        """
        Adiciona um nó de dados filho. Operação permanente que salva no arquivo.
        
        VALIDAÇÃO: Verifica se já existe um nó do mesmo tipo antes de adicionar.
        
        Args:
            parent_uuid: UUID do nó pai
            display_name: Nome de exibição do novo nó
            data_type: Tipo de dado (ex: "barras", "cabos_bt")
            
        Returns:
            True se o nó foi criado com sucesso, False caso contrário
        """
        # Verifica se já existe um nó do mesmo tipo
        existing_nodes = self.model.get_child_nodes_by_type(parent_uuid)
        for node_info in existing_nodes.values():
            if node_info['dataType'] == data_type:
                # Já existe um nó desse tipo, não adiciona duplicado
                # Retorna True silenciosamente (não é um erro, apenas não faz nada)
                return True
        
        # Gera um nome único para o novo nó de dados
        parent_item = self._find_item_by_uuid(parent_uuid)
        if not parent_item:
            return False
        unique_name = self._generate_unique_name(parent_item, display_name)

        # Chama o método do modelo (que também valida unicidade internamente)
        project_data = self.model.add_data_node(parent_uuid, unique_name, data_type)
        
        if project_data:
            # Salva imediatamente no arquivo
            if self.model.save_project():
                self._update_tree_from_project_data(project_data)
                self._update_window_title()
                self.view.tree_view.expandAll()
                return True
            else:
                QMessageBox.critical(self.view, "Erro", "Não foi possível salvar o projeto.")
                return False
        else:
            # Falha silenciosa - o model já imprimiu o erro
            return False
    
    def remove_data_node(self, parent_uuid: str, data_type: str) -> bool:
        """
        Remove um nó de dados filho de um tipo específico.
        Operação permanente que salva no arquivo.
        
        Args:
            parent_uuid: UUID do nó pai
            data_type: Tipo de dado a ser removido (ex: "barras", "cabos_bt")
            
        Returns:
            True se o nó foi removido com sucesso, False caso contrário
        """
        # Chama o método do modelo
        project_data = self.model.remove_data_node(parent_uuid, data_type)
        
        if project_data:
            # Salva imediatamente no arquivo
            if self.model.save_project():
                self._update_tree_from_project_data(project_data)
                self._update_window_title()
                return True
            else:
                QMessageBox.critical(self.view, "Erro", "Não foi possível salvar o projeto.")
                return False
        else:
            # Falha silenciosa - o nó pode não existir
            return False
    
    def get_child_data_nodes(self, parent_uuid: str) -> dict:
        """
        Retorna um dicionário de nós de dados filhos de um nó pai.
        Formato: { 'child_uuid': {'displayName': '..', 'dataType': '...'} }
        
        Delega para o método do Model.
        """
        return self.model.get_child_nodes_by_type(parent_uuid)

    def handle_delete_item_by_uuid(self, node_uuid: str, confirm: bool = False):
        """
        Exclui um nó pelo seu UUID. Se `confirm` for True, pede confirmação.
        Esta função centraliza a lógica de exclusão permanente.
        """
        if not node_uuid:
            return

        node_to_delete, _ = self.model._find_node_by_uuid(node_uuid)
        if not node_to_delete:
            QMessageBox.warning(self.view, "Erro", "Item a ser excluído não encontrado.")
            return

        item_name = node_to_delete.get('displayName', 'Item sem nome')
        
        if confirm:
            reply = QMessageBox.question(
                self.view,
                "Confirmar Exclusão",
                f"Deseja realmente excluir o item '{item_name}' e todos os seus subitens?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # Exclui o nó do modelo de dados
        project_data = self.model.delete_node(node_uuid)
        
        if project_data:
            # Salva a alteração imediatamente no arquivo JSON
            if self.model.save_project():
                self._update_tree_from_project_data(project_data)
                self._update_window_title()
                self.view.update_status_message(f"Item '{item_name}' excluído com sucesso.")
            else:
                QMessageBox.critical(self.view, "Erro de Salvamento", "Não foi possível salvar a exclusão no arquivo.")
                # Opcional: Recarregar o projeto para reverter a alteração em memória
                self.model.load_project(self.model.project_path)
                self._update_tree_from_project_data(self.model.project_data)
        else:
            QMessageBox.warning(self.view, "Erro", "Não foi possível excluir o item do modelo de dados.")
    
    def _generate_unique_name(self, parent_item: QStandardItem, base_name: str) -> str:
        """
        Gera um nome único para um novo subitem.
        
        Args:
            parent_item: Item pai
            base_name: Nome base (ex: "Novo Subitem")
            
        Returns:
            Nome único
        """
        # Coleta todos os nomes dos irmãos
        existing_names = []
        for i in range(parent_item.rowCount()):
            child = parent_item.child(i)
            existing_names.append(child.text())
        
        # Se o nome base não existe, usa ele
        if base_name not in existing_names:
            return base_name
        
        # Senão, adiciona sufixo numérico
        counter = 1
        while f"{base_name}_{counter}" in existing_names:
            counter += 1
        
        return f"{base_name}_{counter}"
    
    def _find_item_by_uuid(self, uuid_to_find: str) -> QStandardItem:
        """
        Encontra um item na árvore pelo seu UUID.
        
        Args:
            uuid_to_find: UUID do item a ser encontrado
            
        Returns:
            O QStandardItem correspondente ou None se não encontrado
        """
        def search_recursive(item: QStandardItem) -> QStandardItem:
            """Busca recursiva por UUID."""
            # Verifica se este item tem o UUID procurado
            if item.data(Qt.ItemDataRole.UserRole) == uuid_to_find:
                return item
            
            # Busca nos filhos
            for i in range(item.rowCount()):
                child = item.child(i)
                result = search_recursive(child)
                if result:
                    return result
            
            return None
        
        # Busca a partir da raiz
        for i in range(self.tree_model.rowCount()):
            root_item = self.tree_model.item(i)
            result = search_recursive(root_item)
            if result:
                return result
        
        return None
    
    def handle_rename_item(self, index):
        """
        Inicia a edição do item selecionado.
        
        Args:
            index: QModelIndex do item a renomear
        """
        # Inicia a edição do item
        self.view.tree_view.edit(index)
    
    def handle_item_changed(self, item: QStandardItem):
        """
        Manipula a mudança de um item (após edição do nome).
        
        Args:
            item: Item que foi modificado
        """
        if self._ignore_item_changed or not item:
            return
        
        # O item pode ter sido invalidado se a árvore foi reconstruída.
        # Precisamos de seu UUID e do novo nome.
        try:
            item_uuid = item.data(Qt.ItemDataRole.UserRole)
            new_name = item.text()
        except RuntimeError:
            # Acontece se o wrapper C++ do item foi deletado.
            # Isso é esperado se a árvore foi recriada. A operação já foi tratada.
            return
        
        if item_uuid is None:
            return
            
        # O comando vai buscar o nome antigo e verificar se houve mudança.
        command = RenameNodeCommand(self.model, item_uuid, new_name, self)
        self.undo_stack.push(command)
        
        self.view.update_status_message(f"Item renomeado para: {new_name}")

    def handle_delete_key_press(self):
        """
        Chamado quando a tecla Delete é pressionada.
        Delega a lógica para a função centralizada handle_delete_item.
        """
        current_index = self.view.tree_view.currentIndex()
        if current_index.isValid():
            # Reutiliza a mesma lógica do menu de contexto
            self.handle_delete_item(current_index)
    
    def handle_delete_item(self, index):
        """
        Manipula a exclusão de um item a partir de um QModelIndex (vinda do menu de contexto).
        Delega a lógica para a função centralizada handle_delete_item_by_uuid.
        """
        if not index.isValid():
            return
            
        item = self.tree_model.itemFromIndex(index)
        if not item:
            return
            
        item_uuid = item.data(Qt.ItemDataRole.UserRole)
        item_logical_id = item.data(Qt.ItemDataRole.UserRole + 1)

        if not item_uuid or item_logical_id == 'root':
            QMessageBox.warning(self.view, "Operação Não Permitida", "Não é possível excluir o nó raiz.")
            return

        # Chama a nova função central, pedindo confirmação (confirm=True)
        self.handle_delete_item_by_uuid(item_uuid, confirm=True)
    
    def handle_toggle_explorer(self, checked: bool):
        """
        Manipulador para alternar a visibilidade do explorador via menu Janela.
        
        Args:
            checked: True se a ação foi marcada, False se desmarcada
        """
        self.view.toggle_explorer_visibility(checked)
    
    def handle_explorer_visibility_changed(self, visible: bool):
        """
        Manipulador para quando a visibilidade do explorador muda.
        Atualiza o estado do menu para refletir o estado atual.
        
        Args:
            visible: True se o explorador está visível, False caso contrário
        """
        self.view.set_explorer_menu_checked(visible)
    
    def show(self):
        """
        Exibe a janela principal da aplicação.
        """
        self.view.show()
