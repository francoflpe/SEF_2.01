# ====================================================================
# MODEL - Lógica de Dados da Aplicação
# ====================================================================
"""
Este arquivo contém a classe ProjectModel, responsável exclusivamente
pelo gerenciamento dos dados da aplicação usando Pandas.
Não possui conhecimento sobre a interface gráfica (PyQt).
"""

import json
import pandas as pd
from typing import Optional, Tuple
import os
from datetime import datetime
import uuid
from data import data_map

# Versão da aplicação
APP_VERSION = "2.0.0"


class ProjectModel:
    """
    Model da aplicação no padrão MVC.
    Responsável por gerenciar, processar e armazenar os dados do projeto.
    Utiliza Pandas DataFrames para manipulação de dados.
    """
    
    def __init__(self):
        """
        Construtor do ProjectModel.
        Inicializa as estruturas de dados.
        """
        self.dataframe: Optional[pd.DataFrame] = None
        self.project_path: Optional[str] = None
        self.project_name: str = "Sem título"
        self.project_data: dict = {}
        self.is_dirty: bool = False  # Indica se há mudanças não salvas
    
    def create_and_save_new_project(self, path: str, metadata: dict) -> dict:
        """
        Cria e salva um novo projeto JSON com metadados.
        
        Args:
            path: Caminho onde o arquivo JSON será salvo
            metadata: Dicionário com metadados do projeto (cs, cliente)
            
        Returns:
            Dicionário com os metadados do projeto criado
        """
        try:
            # Extrai o nome do projeto a partir do caminho do arquivo
            project_name = os.path.splitext(os.path.basename(path))[0]
            
            # Obtém a data e hora atuais formatadas
            data_criacao = datetime.now().strftime("%d/%m/%Y %H:%M")
            
            # Cria o nome do item pai
            cs = metadata.get('cs', '')
            cliente = metadata.get('cliente', '')
            root_display_name = f"CS-{cs} - {cliente}"
            
            # Gera UUID para o nó raiz
            root_uuid = str(uuid.uuid4())
            
            # Cria a estrutura de dados completa para o projeto
            self.project_data = {
                "projectMetadata": {
                    "programa": "SEF - Software de Estudos Focus",
                    "versao": APP_VERSION,
                    "dataDeCriacao": data_criacao,
                    "CS": cs,
                    "cliente": cliente
                },
                "projectTree": {
                    root_uuid: {
                        "logicalId": "root",
                        "displayName": root_display_name,
                        "isDataNode": True,
                        "nodes": {}
                    }
                }
            }
            
            # Atualiza as propriedades do modelo
            self.project_path = path
            self.project_name = project_name
            self.dataframe = None  # Limpa o DataFrame
            
            # Salva o arquivo JSON usando o método centralizado
            if not self.save_project():
                print("Erro ao salvar projeto após criação")
                return {}
            
            return self.project_data
        except Exception as e:
            print(f"Erro ao criar e salvar projeto: {e}")
            return {}
    
    def save_project(self, path: Optional[str] = None) -> bool:
        """
        Salva o projeto atual em um arquivo JSON.
        
        Args:
            path: Caminho onde salvar. Se None, usa o path atual.
            
        Returns:
            True se salvo com sucesso, False caso contrário
        """
        save_path = path if path else self.project_path
        
        if save_path is None:
            return False
        
        try:
            # Salva o arquivo JSON
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.project_data, f, indent=4, ensure_ascii=False)
            
            self.project_path = save_path
            self.is_dirty = False  # Limpa o estado "sujo" após salvar
            return True
        except Exception as e:
            print(f"Erro ao salvar projeto: {e}")
            return False
    
    def get_project_metadata(self) -> dict:
        """
        Retorna os metadados do projeto atual.
        
        Returns:
            Dicionário com os metadados do projeto
        """
        if self.project_path and os.path.exists(self.project_path):
            try:
                with open(self.project_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erro ao ler metadados do projeto: {e}")
                return {}
        return self.project_data
    
    def load_project(self, path: str) -> dict | None:
        """
        Carrega um projeto existente a partir de um arquivo JSON.
        
        Args:
            path: Caminho do arquivo JSON do projeto
            
        Returns:
            Dicionário com os dados do projeto carregados ou None se falhar
        """
        try:
            # Verifica se o arquivo existe
            if not os.path.exists(path):
                print(f"Erro: Arquivo não encontrado: {path}")
                return None
            
            # Lê o conteúdo do arquivo JSON
            with open(path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # Valida a estrutura básica do JSON
            if 'projectMetadata' not in project_data:
                print("Erro: Estrutura JSON inválida - falta 'projectMetadata'")
                return None
            
            if 'projectTree' not in project_data:
                print("Erro: Estrutura JSON inválida - falta 'projectTree'")
                return None
            
            # Armazena os dados carregados
            self.project_data = project_data
            self.project_path = path
            self.project_name = os.path.splitext(os.path.basename(path))[0]
            self.dataframe = None  # Limpa o DataFrame
            
            # Migração automática: adiciona chave "data" se não existir
            self._migrate_add_data_key()
            
            self.is_dirty = False  # Limpa o estado "sujo" após carregar
            
            return project_data
            
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar JSON: {e}")
            return None
        except Exception as e:
            print(f"Erro ao carregar projeto: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _find_node_by_uuid(self, target_uuid: str, search_in: Optional[dict] = None) -> Tuple[Optional[dict], Optional[dict]]:
        """
        Busca recursivamente um nó pelo UUID.
        
        Args:
            target_uuid: UUID do nó a ser encontrado
            search_in: Dicionário onde buscar (opcional, usa self.project_data se None)
            
        Returns:
            Tupla (nó_encontrado, nó_pai) ou (None, None) se não encontrado
        """
        if search_in is None:
            search_in = self.project_data

        def _search_recursive(nodes_dict: dict, parent: Optional[dict] = None) -> Tuple[Optional[dict], Optional[dict]]:
            for node_uuid, node_data in nodes_dict.items():
                if node_uuid == target_uuid:
                    return node_data, parent
                
                # Busca nos filhos
                if 'nodes' in node_data and node_data['nodes']:
                    result = _search_recursive(node_data['nodes'], node_data)
                    if result[0] is not None:
                        return result
            
            return None, None
        
        # A busca começa a partir da chave 'projectTree' se ela existir
        root_tree = search_in.get('projectTree', {})
        return _search_recursive(root_tree)
    
    def add_node_to_json(self, parent_uuid: str, child_name: str) -> dict:
        """
        Adiciona um novo nó filho ao nó identificado pelo UUID do pai.
        Usa UUID como chave de armazenamento e calcula logicalId correto.
        Regra: apenas o nó raiz (logicalId="root") pode ter múltiplos filhos.
        
        Args:
            parent_uuid: UUID do nó pai
            child_name: Nome de exibição do novo nó filho
            
        Returns:
            Dicionário completo com os dados do projeto atualizados (ou {} em caso de erro)
        """
        try:
            if not self.project_data:
                return {}
            
            # Encontra o nó pai pelo UUID
            parent_node, _ = self._find_node_by_uuid(parent_uuid)
            
            if parent_node is None:
                print(f"Erro: Nó pai com UUID '{parent_uuid}' não encontrado")
                return {}
            
            # Obtém o logicalId do pai
            parent_logical_id = parent_node.get('logicalId', '')
            
            # Garantir que o nó pai tem a estrutura 'nodes'
            if 'nodes' not in parent_node:
                parent_node['nodes'] = {}
            
            # NOVA REGRA: Verifica se o pai é um nó folha (node-X.Y)
            # Nós folha NÃO podem ter filhos
            if '.' in parent_logical_id and parent_logical_id != 'root':
                print(f"Erro: Nó folha ('{parent_logical_id}') não pode ter filhos.")
                return {}
            
            # Calcula o logicalId do novo nó
            if parent_logical_id == 'root':
                # Filhos diretos do root: node-1, node-2, node-3...
                # Encontra o próximo número sequencial disponível
                existing_numbers = []
                for child_data in parent_node['nodes'].values():
                    child_logical_id = child_data.get('logicalId', '')
                    if child_logical_id.startswith('node-'):
                        try:
                            # Extrai o número (ex: 'node-5' -> 5)
                            num = int(child_logical_id.split('-')[1].split('.')[0])
                            existing_numbers.append(num)
                        except (ValueError, IndexError):
                            pass
                
                # Gera o próximo número
                next_number = max(existing_numbers) + 1 if existing_numbers else 1
                new_logical_id = f"node-{next_number}"
            
            else:
                # Filhos de node-X: node-X.1, node-X.2, node-X.3...
                # Encontra o próximo sub-número sequencial disponível
                existing_sub_numbers = []
                for child_data in parent_node['nodes'].values():
                    child_logical_id = child_data.get('logicalId', '')
                    # Verifica se é filho deste nó (ex: node-2.1, node-2.2 são filhos de node-2)
                    if child_logical_id.startswith(f"{parent_logical_id}."):
                        try:
                            # Extrai o sub-número (ex: 'node-2.5' -> 5)
                            sub_num = int(child_logical_id.split('.')[-1])
                            existing_sub_numbers.append(sub_num)
                        except (ValueError, IndexError):
                            pass
                
                # Gera o próximo sub-número
                next_sub_number = max(existing_sub_numbers) + 1 if existing_sub_numbers else 1
                new_logical_id = f"{parent_logical_id}.{next_sub_number}"
            
            # Gera UUID para o novo nó
            new_uuid = str(uuid.uuid4())
            
            # Cria o novo nó
            new_node = {
                "logicalId": new_logical_id,
                "displayName": child_name,
                "isDataNode": True,  # O novo filho sempre é dataNode
                "data": {},  # Nova chave para armazenar dados associados ao nó
                "nodes": {}
            }
            
            # Simplificação: quando um nó ganha filho, ele não é mais dataNode
            parent_node['isDataNode'] = False
            
            # Adiciona o novo nó usando UUID como chave
            parent_node['nodes'][new_uuid] = new_node
            
            # Marca como modificado (dirty)
            self.is_dirty = True
            
            return self.project_data
            
        except Exception as e:
            import traceback
            print(f"Erro ao adicionar nó: {e}")
            traceback.print_exc()
            return {}
    
    def add_data_node(self, parent_uuid: str, child_name: str, data_type: str) -> dict:
        """
        Adiciona um novo nó filho que representa um tipo de dado.
        
        VALIDAÇÃO: Verifica se já existe um nó do mesmo tipo antes de adicionar.
        
        Args:
            parent_uuid: UUID do nó pai
            child_name: Nome de exibição do novo nó
            data_type: Tipo de dado (ex: "barras", "cabos_bt")
            
        Returns:
            Dicionário completo com os dados do projeto atualizados (ou {} em caso de erro)
        """
        try:
            if not self.project_data:
                return {}
            
            parent_node, _ = self._find_node_by_uuid(parent_uuid)
            if parent_node is None:
                return {}

            # Garante que 'nodes' existe e que o pai não é um nó folha
            parent_logical_id = parent_node.get('logicalId', '')
            if 'nodes' not in parent_node or ('.' in parent_logical_id and parent_logical_id != 'root'):
                return {}

            # VALIDAÇÃO DE UNICIDADE: Verifica se já existe um nó com o mesmo dataType
            for child_node in parent_node['nodes'].values():
                if child_node.get('dataType') == data_type:
                    print(f"Erro: Já existe um nó do tipo '{data_type}' neste pai.")
                    return {}

            # Busca o schema para o tipo de dado
            schema = self.get_data_schema(data_type)
            if not schema or not isinstance(schema, dict):
                # Se não houver schema, não cria o nó
                print(f"Schema para o tipo '{data_type}' não encontrado ou inválido.")
                return {}

            # Cria a estrutura de dados inicial com base no schema
            initial_data = {key: "" for key in schema.keys()}

            # Gera UUID para o novo nó e logicalId (simplificado)
            new_uuid = str(uuid.uuid4())
            num_children = len(parent_node['nodes'])
            new_logical_id = f"{parent_logical_id}.{num_children + 1}"

            new_node = {
                "logicalId": new_logical_id,
                "displayName": child_name,
                "isDataNode": False,  # Este nó agora é um container de tabela
                "dataType": data_type,  # <-- NOVA CHAVE: identifica o tipo de dado
                "data": initial_data,  # <-- Armazena os campos como um dicionário
                "nodes": {}  # Nós de dados não têm filhos
            }

            parent_node['nodes'][new_uuid] = new_node
            self.is_dirty = True
            return self.project_data
        except Exception as e:
            print(f"Erro em add_data_node: {e}")
            return {}
    
    def remove_data_node(self, parent_uuid: str, data_type: str) -> dict:
        """
        Remove um nó filho que representa um tipo de dado específico.
        
        Args:
            parent_uuid: UUID do nó pai
            data_type: Tipo de dado a ser removido (ex: "barras", "cabos_bt")
            
        Returns:
            Dicionário completo com os dados do projeto atualizados (ou {} em caso de erro)
        """
        try:
            if not self.project_data:
                return {}
            
            parent_node, _ = self._find_node_by_uuid(parent_uuid)
            if parent_node is None:
                return {}
            
            if 'nodes' not in parent_node:
                return {}
            
            # Encontra o UUID do nó com o dataType correspondente
            node_uuid_to_remove = None
            for child_uuid, child_node in parent_node['nodes'].items():
                if child_node.get('dataType') == data_type:
                    node_uuid_to_remove = child_uuid
                    break
            
            if node_uuid_to_remove is None:
                print(f"Erro: Nó do tipo '{data_type}' não encontrado.")
                return {}
            
            # Remove o nó
            del parent_node['nodes'][node_uuid_to_remove]
            self.is_dirty = True
            return self.project_data
            
        except Exception as e:
            print(f"Erro em remove_data_node: {e}")
            return {}
    
    def get_child_nodes_by_type(self, parent_uuid: str) -> dict:
        """
        Retorna um dicionário com os nós filhos que possuem dataType.
        
        Args:
            parent_uuid: UUID do nó pai
            
        Returns:
            Dicionário no formato {'uuid': {'displayName': '...', 'dataType': '...'}}
        """
        try:
            child_nodes = {}
            parent_node, _ = self._find_node_by_uuid(parent_uuid)
            
            if parent_node and 'nodes' in parent_node:
                for child_uuid, child_node in parent_node['nodes'].items():
                    if 'dataType' in child_node:
                        child_nodes[child_uuid] = {
                            'displayName': child_node.get('displayName', ''),
                            'dataType': child_node.get('dataType', '')
                        }
            
            return child_nodes
        except Exception as e:
            print(f"Erro em get_child_nodes_by_type: {e}")
            return {}
    
    def update_node_name(self, node_uuid: str, new_name: str) -> bool:
        """
        Atualiza o displayName de um nó identificado pelo UUID.
        
        Args:
            node_uuid: UUID do nó a ser renomeado
            new_name: Novo nome do nó
            
        Returns:
            True se atualizado com sucesso, False caso contrário
        """
        if not self.project_path or not os.path.exists(self.project_path):
            return False
        
        try:
            # Encontra o nó pelo UUID
            node, _ = self._find_node_by_uuid(node_uuid)
            
            if node is None:
                print(f"Erro: Nó com UUID '{node_uuid}' não encontrado")
                return False
            
            # Atualiza o displayName
            node['displayName'] = new_name
            
            # Marca como modificado (dirty)
            self.is_dirty = True
            
            return True
        except Exception as e:
            print(f"Erro ao atualizar nome do nó: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def delete_node(self, node_uuid: str) -> dict:
        """
        Exclui um nó identificado pelo UUID.
        Se o nó excluído era isDataNode, o pai se torna o novo isDataNode.
        
        Args:
            node_uuid: UUID do nó a ser excluído
            
        Returns:
            Dicionário completo com os dados do projeto atualizados (ou {} em caso de erro)
        """
        try:
            if not self.project_data:
                return {}
            
            # Encontra o nó e seu pai
            node_to_delete, parent_node = self._find_node_by_uuid(node_uuid)
            
            if node_to_delete is None:
                print(f"Erro: Nó com UUID '{node_uuid}' não encontrado")
                return {}
            
            # Não pode excluir o nó raiz
            logical_id = node_to_delete.get('logicalId', '')
            if logical_id == 'root':
                print("Erro: Não é possível excluir o nó raiz")
                return {}
            
            # Verifica se o nó a ser excluído era isDataNode
            was_data_node = node_to_delete.get('isDataNode', False)
            
            # Encontra o dicionário que contém este nó para poder deletá-lo
            # Precisa buscar novamente para ter acesso ao dicionário pai
            def _find_and_delete(nodes_dict: dict) -> bool:
                if node_uuid in nodes_dict:
                    del nodes_dict[node_uuid]
                    return True
                
                for node_data in nodes_dict.values():
                    if 'nodes' in node_data and node_data['nodes']:
                        if _find_and_delete(node_data['nodes']):
                            return True
                
                return False
            
            # Remove o nó
            if not _find_and_delete(self.project_data['projectTree']):
                print("Erro ao remover nó da estrutura")
                return {}
            
            # Se o nó excluído era isDataNode, o pai se torna o novo isDataNode
            if was_data_node and parent_node:
                parent_node['isDataNode'] = True
            
            # Marca como modificado (dirty)
            self.is_dirty = True
            
            return self.project_data
            
        except Exception as e:
            import traceback
            print(f"Erro ao excluir nó: {e}")
            traceback.print_exc()
            return {}
    
    def get_node_snapshot(self, node_uuid: str) -> dict | None:
        """
        Obtém um snapshot completo de um nó para copiar.
        
        Args:
            node_uuid: UUID do nó a ser copiado
            
        Returns:
            Dicionário com os dados do nó ou None se não encontrado
        """
        try:
            node, _ = self._find_node_by_uuid(node_uuid)
            
            if node is None:
                return None
            
            # Retorna uma cópia profunda do nó (sem o UUID da chave)
            import copy
            return copy.deepcopy(node)
            
        except Exception as e:
            print(f"Erro ao obter snapshot do nó: {e}")
            return None
    
    def get_node_data(self, node_uuid: str) -> dict | None:
        """
        Obtém os dados associados a um nó.
        
        Args:
            node_uuid: UUID do nó
            
        Returns:
            Dicionário com os dados do nó ou None se não encontrado ou vazio
        """
        try:
            node, _ = self._find_node_by_uuid(node_uuid)
            
            if node is None:
                return None
            
            # Retorna o conteúdo da chave 'data', ou None se estiver vazia
            node_data = node.get('data', {})
            return node_data if node_data else None
            
        except Exception as e:
            print(f"Erro ao obter dados do nó: {e}")
            return None
    
    def clear_node_data(self, node_uuid: str) -> bool:
        """
        Limpa os dados associados a um nó.
        
        Args:
            node_uuid: UUID do nó
            
        Returns:
            True se os dados foram limpos com sucesso, False caso contrário
        """
        try:
            node, _ = self._find_node_by_uuid(node_uuid)
            
            if node is None:
                print(f"Erro: Nó com UUID '{node_uuid}' não encontrado")
                return False
            
            # Redefine a chave de dados para um dicionário vazio
            node['data'] = {}
            
            # Marca como modificado (dirty)
            self.is_dirty = True
            
            return True
            
        except Exception as e:
            print(f"Erro ao limpar dados do nó: {e}")
            return False
    
    def is_data_node(self, node_uuid: str) -> bool:
        """
        Verifica se um nó é um "nó de dados" (pode conter dados).
        
        Regras:
        - Nós do tipo node-X sem filhos: podem conter dados
        - Nós do tipo node-X.Y: podem conter dados (são folhas)
        - Nós do tipo node-X com filhos: NÃO podem conter dados (são estruturais)
        - Nó root: NÃO é nó de dados
        
        Args:
            node_uuid: UUID do nó
            
        Returns:
            True se o nó pode conter dados, False caso contrário
        """
        try:
            node, _ = self._find_node_by_uuid(node_uuid)
            
            if node is None:
                return False
            
            # Se o JSON contém uma flag explícita, respeita-a (prioridade)
            if 'isDataNode' in node:
                try:
                    return bool(node.get('isDataNode'))
                except Exception:
                    # se por algum motivo a flag estiver inválida, cai para inferência
                    pass

            logical_id = node.get('logicalId', '')

            # Root não é nó de dados
            if logical_id == 'root':
                return False

            # Nós do tipo node-X.Y são sempre nós de dados (folhas)
            if '.' in logical_id:
                return True

            # Nós do tipo node-X são nós de dados apenas se não tiverem filhos
            has_children = 'nodes' in node and len(node.get('nodes', {})) > 0
            return not has_children
            
        except Exception as e:
            print(f"Erro ao verificar se é nó de dados: {e}")
            return False
    
    def _migrate_add_data_key(self):
        """
        Migração automática: adiciona a chave "data": {} a todos os nós que não a possuem.
        Isso garante compatibilidade retroativa com projetos criados antes da implementação
        do sistema de gerenciamento de dados.
        """
        def add_data_recursive(nodes_dict: dict):
            for node_data in nodes_dict.values():
                # Adiciona a chave "data" se não existir
                if 'data' not in node_data:
                    node_data['data'] = {}
                
                # Processa filhos recursivamente
                if 'nodes' in node_data and node_data['nodes']:
                    add_data_recursive(node_data['nodes'])
        
        try:
            if self.project_data and 'projectTree' in self.project_data:
                add_data_recursive(self.project_data['projectTree'])
        except Exception as e:
            print(f"Erro durante migração de dados: {e}")

    def update_project_metadata(self, new_metadata: dict) -> bool:
        """
        Atualiza os metadados do projeto e o nome do nó raiz.
        
        Args:
            new_metadata: Dicionário com os novos dados ('cs', 'cliente').
            
        Returns:
            True se atualizado com sucesso, False caso contrário.
        """
        try:
            if not self.project_data or 'projectMetadata' not in self.project_data:
                return False

            # Atualiza os metadados
            self.project_data['projectMetadata']['CS'] = new_metadata.get('cs', '')
            self.project_data['projectMetadata']['cliente'] = new_metadata.get('cliente', '')

            # Atualiza o displayName do nó raiz para refletir a mudança
            cs = new_metadata.get('cs', '')
            cliente = new_metadata.get('cliente', '')
            root_display_name = f"CS-{cs} - {cliente}"
            
            # Encontra o nó raiz e atualiza seu nome
            root_node, _ = self._find_node_by_uuid(next(iter(self.project_data['projectTree'])))
            if root_node:
                root_node['displayName'] = root_display_name

            self.is_dirty = True
            return True
        except Exception as e:
            print(f"Erro ao atualizar metadados: {e}")
            return False

    def get_data_schema(self, type_name: str) -> dict:
        """Retorna o schema de campos para um tipo de dado (ex: 'barras').

        Usa `data_map.py` para carregar o mapa editável em `data_map.json`.
        """
        try:
            return data_map.get_schema(type_name)
        except Exception as e:
            print(f"Erro ao obter schema de dados para '{type_name}': {e}")
            return {}

    def update_node_data(self, node_uuid: str, data: dict) -> bool:
        """Atualiza a chave `data` do nó identificado por `node_uuid` no projeto em memória.

        Marca o modelo como sujo (`is_dirty=True`) e retorna True se o nó foi encontrado e atualizado.
        """
        try:
            node, _ = self._find_node_by_uuid(node_uuid)
            if node is None:
                # tenta buscar diretamente na raiz se a chave for top-level
                if 'projectTree' in self.project_data and node_uuid in self.project_data['projectTree']:
                    node = self.project_data['projectTree'][node_uuid]
            if node is None:
                return False
            node['data'] = data
            self.is_dirty = True
            return True
        except Exception as e:
            print(f"Erro ao atualizar dados do nó: {e}")
            return False
