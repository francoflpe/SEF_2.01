# ====================================================================
# VIEW - Interface Gráfica da Aplicação (PyQt6)
# ====================================================================
"""
Este arquivo contém a classe MainView, responsável exclusivamente
pela interface gráfica da aplicação. Não contém lógica de negócio.
"""

from PyQt6.QtWidgets import QMainWindow, QStatusBar, QToolBar, QStyle, QDockWidget, QTreeView, QWidget, QVBoxLayout, QTableView, QAbstractItemView
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QCloseEvent, QKeyEvent
from PyQt6.QtCore import pyqtSignal, Qt


class MainView(QMainWindow):
    """
    View da aplicação no padrão MVC.
    Responsável apenas pela criação e exibição dos componentes visuais.
    Emite sinais quando o usuário interage com a interface.
    """
    
    # Sinais customizados para comunicar eventos ao Controller
    createProjectClicked = pyqtSignal()
    openProjectClicked = pyqtSignal()
    saveProjectClicked = pyqtSignal()
    saveAsProjectClicked = pyqtSignal()
    exitRequested = pyqtSignal()
    copyNodeClicked = pyqtSignal()
    pasteNodeClicked = pyqtSignal()
    closeRequested = pyqtSignal(QCloseEvent)
    explorerToggleRequested = pyqtSignal(bool)
    explorerVisibilityChanged = pyqtSignal(bool)
    deleteKeyPressed = pyqtSignal()
    
    def __init__(self):
        """
        Construtor da MainView.
        Configura todos os elementos visuais da interface.
        """
        super().__init__()
        
        # Configuração do título da janela
        self.setWindowTitle("SEF - Software de Estudos Focus")
        
        # Configuração do tamanho inicial da janela (largura x altura)
        self.resize(800, 600)
        
        # Configuração do ícone da janela com fundo branco
        self._configurar_icone()
        
        # Configuração da barra de menu
        self._criar_menu()
        
        # Configuração da barra de ferramentas
        self._criar_barra_ferramentas()
        
        # Criação do widget central (necessário para que o dock não ocupe toda a área)
        self._criar_widget_central()
        
        # Configuração do explorador de projeto (QDockWidget)
        self._criar_explorador()
        
        # Criação e configuração da barra de status
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Pronto")
        self.setStatusBar(self.status_bar)
        
        # --- NOVA ADIÇÃO ---
        # Cria a QTableView que será usada para exibir os dados
        self.table_view = QTableView()
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Apenas visualização por enquanto

        # Adiciona a tabela ao layout central
        self.central_layout.addWidget(self.table_view)
    
    def _configurar_icone(self):
        """
        Carrega o ícone transparente e adiciona um fundo branco.
        """
        # Carrega a imagem original (com transparência)
        icone_original = QPixmap("resources/icone_png.png")
        
        # Cria um novo pixmap com o mesmo tamanho, preenchido com branco
        icone_com_fundo = QPixmap(icone_original.size())
        icone_com_fundo.fill(QColor("white"))
        
        # Usa QPainter para desenhar o ícone original sobre o fundo branco
        painter = QPainter(icone_com_fundo)
        painter.drawPixmap(0, 0, icone_original)
        painter.end()
        
        # Define o ícone da janela
        self.setWindowIcon(QIcon(icone_com_fundo))
    
    def _criar_menu(self):
        """
        Cria a barra de menu e suas ações.
        Conecta as ações aos sinais customizados.
        """
        # Obtém a barra de menu da janela principal
        menu_bar = self.menuBar()
        
        # Cria o menu "Arquivo" (Alt+A como atalho)
        menu_arquivo = menu_bar.addMenu("&Arquivo")
        
        # Obtém os ícones padrão do sistema via QStyle
        icone_criar = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
        icone_abrir = self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon)
        icone_salvar = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton)
        
        # Ação "Criar Projeto" com ícone
        self.acao_criar = QAction(icone_criar, "Criar Projeto", self)
        self.acao_criar.triggered.connect(self.createProjectClicked.emit)
        menu_arquivo.addAction(self.acao_criar)
        
        # Ação "Abrir Projeto" com ícone
        self.acao_abrir = QAction(icone_abrir, "Abrir Projeto", self)
        self.acao_abrir.triggered.connect(self.openProjectClicked.emit)
        menu_arquivo.addAction(self.acao_abrir)
        
        # Adiciona um separador
        menu_arquivo.addSeparator()
        
        # Ação "Salvar" com ícone
        self.acao_salvar = QAction(icone_salvar, "Salvar", self)
        self.acao_salvar.setShortcut("Ctrl+S")
        self.acao_salvar.triggered.connect(self.saveProjectClicked.emit)
        menu_arquivo.addAction(self.acao_salvar)
        
        # Ação "Salvar como..." com ícone
        self.acao_salvar_como = QAction("Salvar como...", self)
        self.acao_salvar_como.setShortcut("Ctrl+Shift+S")
        self.acao_salvar_como.triggered.connect(self.saveAsProjectClicked.emit)
        menu_arquivo.addAction(self.acao_salvar_como)
        
        # Adiciona um separador
        menu_arquivo.addSeparator()
        
        # Ação "Sair"
        self.acao_sair = QAction("Sair", self)
        self.acao_sair.triggered.connect(self.exitRequested.emit)
        menu_arquivo.addAction(self.acao_sair)
        
        # Cria o menu "Editar" (Alt+E como atalho)
        menu_editar = menu_bar.addMenu("&Editar")
        
        # Obtém ícones para desfazer/refazer
        icone_desfazer = self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack)
        icone_refazer = self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward)
        
        # Ação "Desfazer" (será conectada ao QUndoStack no controller)
        self.acao_desfazer = QAction(icone_desfazer, "Desfazer", self)
        self.acao_desfazer.setShortcut("Ctrl+Z")
        self.acao_desfazer.setEnabled(False)
        menu_editar.addAction(self.acao_desfazer)
        
        # Ação "Refazer" (será conectada ao QUndoStack no controller)
        self.acao_refazer = QAction(icone_refazer, "Refazer", self)
        self.acao_refazer.setShortcut("Ctrl+Y")
        self.acao_refazer.setEnabled(False)
        menu_editar.addAction(self.acao_refazer)
        
        # Adiciona um separador
        menu_editar.addSeparator()
        
        # Ação "Copiar"
        self.acao_copiar = QAction("Copiar", self)
        self.acao_copiar.setShortcut("Ctrl+C")
        self.acao_copiar.triggered.connect(self.copyNodeClicked.emit)
        menu_editar.addAction(self.acao_copiar)
        
        # Ação "Colar"
        self.acao_colar = QAction("Colar", self)
        self.acao_colar.setShortcut("Ctrl+V")
        self.acao_colar.triggered.connect(self.pasteNodeClicked.emit)
        menu_editar.addAction(self.acao_colar)
        
        # Adiciona um separador
        menu_editar.addSeparator()
        
        # Cria o menu "Janela" (Alt+J como atalho)
        menu_janela = menu_bar.addMenu("&Janela")
        
        # Ação "Explorador" (verificável)
        self.acao_explorador = QAction("Explorador", self)
        self.acao_explorador.setCheckable(True)
        self.acao_explorador.setChecked(False)  # Inicialmente não verificado
        self.acao_explorador.triggered.connect(self.explorerToggleRequested.emit)
        menu_janela.addAction(self.acao_explorador)
    
    def _criar_barra_ferramentas(self):
        """
        Cria a barra de ferramentas com ações rápidas.
        """
        # Cria a barra de ferramentas
        barra_ferramentas = QToolBar("Barra de Ferramentas Principal")
        self.addToolBar(barra_ferramentas)
        
        # Adiciona as ações à barra de ferramentas
        barra_ferramentas.addAction(self.acao_criar)
        barra_ferramentas.addAction(self.acao_abrir)
        barra_ferramentas.addAction(self.acao_salvar)
        barra_ferramentas.addSeparator()
        barra_ferramentas.addAction(self.acao_desfazer)
        barra_ferramentas.addAction(self.acao_refazer)
    
    def _criar_widget_central(self):
        """
        Cria o widget central da janela principal.
        Necessário para que o QDockWidget não ocupe toda a área.
        """
        self.central_widget = QWidget()
        # adiciona layout para que possamos trocar o conteúdo dinamicamente
        self.central_layout = QVBoxLayout()
        self.central_layout.setContentsMargins(6, 6, 6, 6)
        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)

    def set_central_widget_content(self, widget: QWidget):
        """Substitui o conteúdo do widget central pelo widget fornecido."""
        # limpa layout
        try:
            while self.central_layout.count():
                item = self.central_layout.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.setParent(None)
        except Exception:
            pass
        # adiciona o novo widget
        if widget is not None:
            self.central_layout.addWidget(widget)
    
    def _criar_explorador(self):
        """
        Cria o explorador de projeto como um QDockWidget com QTreeView.
        """
        # Cria o QDockWidget
        self.dock = QDockWidget("Explorador", self)
        
        # Restringe as áreas de docagem (esquerda e direita)
        self.dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | 
            Qt.DockWidgetArea.RightDockWidgetArea
        )
        
        # Desabilita a capacidade de flutuar (destacar da janela)
        self.dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        
        # Define largura fixa
        self.dock.setFixedWidth(250)
        
        # Cria o QTreeView
        self.tree_view = QTreeView()
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.setHeaderHidden(True)  # Esconde o cabeçalho
        self.tree_view.setEditTriggers(
            QTreeView.EditTrigger.EditKeyPressed
        )  # Habilita edição apenas via tecla F2
        
        # Define o QTreeView como widget do dock
        self.dock.setWidget(self.tree_view)
        
        # Conecta o sinal de mudança de visibilidade do dock a um sinal customizado
        self.dock.visibilityChanged.connect(self.explorerVisibilityChanged.emit)
        
        # Adiciona o dock à janela principal (área esquerda)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock)
        
        # Inicialmente oculto
        self.dock.hide()
    
    def update_status_message(self, message: str):
        """
        Atualiza a mensagem da barra de status.
        Método chamado pelo Controller.
        
        Args:
            message: Mensagem a ser exibida na barra de status
        """
        self.status_bar.showMessage(message)
    
    def update_table_data(self, dataframe):
        """
        Atualiza a exibição de dados na interface.
        Método a ser implementado quando houver uma tabela de dados.
        
        Args:
            dataframe: DataFrame do Pandas com os dados a serem exibidos
        """
        # TODO: Implementar quando adicionar QTableView/QTableWidget
        pass
    
    def show_explorer(self):
        """
        Torna o explorador de projeto visível.
        Método chamado pelo Controller.
        """
        self.dock.show()
    
    def update_explorer_model(self, model):
        """
        Atualiza o modelo do QTreeView com um novo QStandardItemModel.
        Método chamado pelo Controller.
        
        Args:
            model: QStandardItemModel com a estrutura da árvore
        """
        self.tree_view.setModel(model)
        self.tree_view.expandAll()  # Expande todos os itens automaticamente
    
    def toggle_explorer_visibility(self, visible: bool):
        """
        Mostra ou oculta o explorador de projeto.
        Método chamado pelo Controller.
        
        Args:
            visible: True para mostrar, False para ocultar
        """
        self.dock.setVisible(visible)
    
    def set_explorer_menu_checked(self, checked: bool):
        """
        Atualiza o estado de check da ação do menu Janela > Explorador.
        Método chamado pelo Controller.
        
        Args:
            checked: True para marcar, False para desmarcar
        """
        # Bloqueia sinais temporariamente para evitar loop
        self.acao_explorador.blockSignals(True)
        self.acao_explorador.setChecked(checked)
        self.acao_explorador.blockSignals(False)
    
    def update_window_title(self, title: str):
        """
        Atualiza o título da janela.
        Método chamado pelo Controller.
        
        Args:
            title: Título a ser exibido
        """
        self.setWindowTitle(title)
    
    def closeEvent(self, event: QCloseEvent):
        """
        Override do evento de fechamento da janela.
        Em vez de fechar diretamente, emite o sinal closeRequested
        para que o Controller possa verificar alterações não salvas.
        
        Args:
            event: Evento de fechamento
        """
        # Emite o sinal para o Controller decidir se fecha ou não
        self.closeRequested.emit(event)

    #Sobrescrever o método keyPressEvent
    def keyPressEvent(self, event: QKeyEvent):
        """
        Sobrescreve o evento de pressionar tecla para capturar a tecla Delete.
        """
        # Verifica se a tecla pressionada é Delete E se a árvore tem o foco
        if event.key() == Qt.Key.Key_Delete and self.tree_view.hasFocus():
            self.deleteKeyPressed.emit()
        else:
            # Passa todos os outros eventos de tecla para a implementação padrão
            super().keyPressEvent(event)
