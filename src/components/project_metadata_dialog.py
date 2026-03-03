# ====================================================================
# DIALOGS - Diálogos Customizados da Aplicação
# ====================================================================
"""
Este arquivo contém diálogos customizados para a aplicação.
Implementa as janelas de diálogo que coletam informações do usuário.
"""

from PyQt6.QtWidgets import (
    QDialog, QLabel, QLineEdit, QDialogButtonBox, 
    QVBoxLayout, QHBoxLayout, QFormLayout
)
from PyQt6.QtCore import Qt
from typing import Optional


class ProjectMetadataDialog(QDialog):
    """
    Diálogo para coletar metadados do projeto.
    Solicita informações como CS (Centro de Serviço) e Cliente.
    """
    
    def __init__(self, parent=None):
        """
        Construtor do diálogo de metadados.
        
        Args:
            parent: Widget pai (geralmente a janela principal)
        """
        super().__init__(parent)
        
        # Configuração da janela do diálogo
        self.setWindowTitle("Dados do Projeto")
        self.setMinimumWidth(300)
        
        # Criação dos campos de entrada
        self._setup_ui()
    
    def _setup_ui(self):
        """
        Configura a interface do diálogo.
        """
        # Layout principal vertical
        layout = QVBoxLayout()
        
        # Layout de formulário para os campos
        form_layout = QFormLayout()
        
        # Campo CS (Centro de Serviço)
        self.cs_input = QLineEdit()
        self.cs_input.setPlaceholderText("Digite o código da CS")
        form_layout.addRow("CS:", self.cs_input)
        
        # Campo Cliente
        self.cliente_input = QLineEdit()
        self.cliente_input.setPlaceholderText("Digite o nome do cliente")
        form_layout.addRow("Cliente:", self.cliente_input)
        
        # Adiciona o formulário ao layout principal
        layout.addLayout(form_layout)
        
        # Adiciona espaçamento
        layout.addSpacing(20)
        
        # Botões OK e Cancelar
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        
        # Define o layout do diálogo
        self.setLayout(layout)
        
        # Foca no primeiro campo
        self.cs_input.setFocus()
    
    def get_data(self) -> Optional[dict]:
        """
        Retorna os dados inseridos pelo usuário.
        
        Returns:
            Dicionário com os dados se o usuário confirmou (OK),
            None se o usuário cancelou.
        """
        if self.result() == QDialog.DialogCode.Accepted:
            return {
                'cs': self.cs_input.text().strip(),
                'cliente': self.cliente_input.text().strip()
            }
        return None
