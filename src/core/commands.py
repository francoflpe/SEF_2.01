# ====================================================================
# COMMANDS - Sistema de Desfazer/Refazer (QUndoCommand)
# ====================================================================
"""
Este arquivo contém as classes de comando para o sistema de Desfazer/Refazer.
Cada comando encapsula uma ação modificadora e sua reversão.

NOTA: Os comandos AddNodeCommand e DeleteNodeCommand foram removidos.
Operações de criação e exclusão de nós agora são permanentes e salvam diretamente no arquivo.
Apenas a renomeação de nós usa o sistema de Desfazer/Refazer.
"""

from PyQt6.QtGui import QUndoCommand


class RenameNodeCommand(QUndoCommand):
    """
    Comando para renomear um nó.
    """
    
    def __init__(self, model, node_uuid: str, new_name: str, controller):
        """
        Construtor do comando de renomear nó.
        
        Args:
            model: Referência ao ProjectModel
            node_uuid: UUID do nó a ser renomeado
            new_name: Nome novo do nó
            controller: Referência ao Controller para atualizar a UI
        """
        super().__init__()
        self.model = model
        self.node_uuid = node_uuid
        self.new_name = new_name
        self.controller = controller
        
        # Obtém o nome antigo aqui para evitar problemas de referência
        node, _ = self.model._find_node_by_uuid(self.node_uuid)
        self.old_name = node.get('displayName', '') if node else ''
        
        self.setText(f"Renomear '{self.old_name}' para '{self.new_name}'")
    
    def redo(self):
        """Executa a ação de renomear o nó."""
        # Só executa se o nome realmente mudou
        if self.old_name == self.new_name:
            return

        success = self.model.update_node_name(self.node_uuid, self.new_name)
        if success:
            # Atualiza apenas o item específico na árvore
            item = self.controller._find_item_by_uuid(self.node_uuid)
            if item:
                self.controller._ignore_item_changed = True
                item.setText(self.new_name)
                self.controller._ignore_item_changed = False
            
            self.controller._update_window_title()
            self.controller.view.update_status_message(f"Item renomeado para: {self.new_name}")
    
    def undo(self):
        """Desfaz a ação restaurando o nome antigo."""
        if self.old_name == self.new_name:
            return

        success = self.model.update_node_name(self.node_uuid, self.old_name)
        if success:
            # Atualiza apenas o item específico na árvore
            item = self.controller._find_item_by_uuid(self.node_uuid)
            if item:
                self.controller._ignore_item_changed = True
                item.setText(self.old_name)
                self.controller._ignore_item_changed = False
            
            self.controller._update_window_title()
            self.controller.view.update_status_message(f"Item renomeado para: {self.old_name}")
