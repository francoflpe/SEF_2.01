# Arquitetura do Projeto SEF-2.01

## Estrutura Atual de Diretórios

```
SEF-2.01/
├── src/                          # Código-fonte da aplicação
│   ├── main.py                   # Ponto de entrada da aplicação
│   ├── __init__.py               # Marca src como pacote Python
│   │
│   ├── core/                     # Núcleo MVC da aplicação
│   │   ├── main_controller.py   # Controller principal (orquestra View e Model)
│   │   ├── main_view.py         # View principal (interface Qt)
│   │   ├── project_model.py     # Model principal (lógica de dados e persistência)
│   │   ├── commands.py          # Comandos para Undo/Redo
│   │   └── __init__.py
│   │
│   ├── components/               # Componentes UI reutilizáveis
│   │   ├── data_entry_dialog.py       # Diálogo de edição/visualização de dados
│   │   ├── project_metadata_dialog.py # Diálogo de metadados do projeto
│   │   └── __init__.py
│   │
│   ├── data/                     # Camada de dados
│   │   ├── data_map.py          # Mapeamento de schemas e labels dos tipos de dados
│   │   ├── data_map.json        # Schema JSON editável dos tipos de dados
│   │   ├── pandas_model.py      # Adapter entre Pandas e QTableView
│   │   └── __init__.py
│   │
│   ├── data_models/              # Modelos específicos por tipo de dado (FUTURO)
│   │   └── __init__.py          # Placeholder para futuros módulos especializados
│   │
│   └── utils/                    # Utilitários e ferramentas
│       ├── project_config.py    # Gerenciamento de configuração de projetos
│       ├── migration.py         # Migração de esquemas de dados
│       ├── migrate_cli.py       # CLI para migração em lote
│       └── __init__.py
│
├── resources/                    # Recursos da aplicação
│   └── qtbase_pt.qm             # Tradução Qt para português
│
├── run.bat                       # Script de execução (Windows)
├── requirements.txt              # Dependências Python
├── README.md                     # Documentação do projeto
├── REFATORACAO.md               # Histórico de refatorações
└── ARQUITETURA.md               # Este arquivo

```

## Padrão de Arquitetura: MVC (Model-View-Controller)

### Model (`src/core/project_model.py`)
**Responsabilidade:** Lógica de negócio e persistência de dados.

- Gerencia a estrutura de dados do projeto (JSON hierárquico)
- Valida e sincroniza nós de dados
- Salva e carrega projetos
- **NÃO possui conhecimento da interface gráfica**

Métodos principais:
- `load_project()`, `save_project()`
- `add_node_to_json()`, `delete_node()`
- `add_data_node()`, `remove_data_node()`
- `sync_data_nodes()` - **Sincroniza tipos de dados (Fase 1)**
- `get_types_to_remove()` - **Prepara confirmação de remoção**

### View (`src/core/main_view.py`)
**Responsabilidade:** Interface gráfica do usuário.

- Renderiza widgets Qt (QTreeView, QTableView, menus, etc.)
- Emite sinais para o Controller quando o usuário interage
- **NÃO contém lógica de negócio**

Componentes principais:
- `QTreeView` - Explorador de projeto
- `QTableView` - Visualização de dados tabulares
- Menus e barras de ferramentas

### Controller (`src/core/main_controller.py`)
**Responsabilidade:** Orquestração entre View e Model.

- Conecta sinais da View aos métodos de manipulação
- Chama métodos do Model em resposta a ações do usuário
- Atualiza a View após mudanças no Model
- Gerencia diálogos de confirmação e validação

Fluxo típico:
```
Usuário interage → View emite sinal → Controller captura → 
Controller chama Model → Model altera dados → 
Controller atualiza View
```

## Lógica Centralizada de Operações (Fase 2)

### Exclusão de Nós
**Função central:** `MainController.handle_delete_item_by_uuid()`

Todas as operações de exclusão passam por esta função:
- Menu de contexto → `handle_delete_item()` → `handle_delete_item_by_uuid()`
- Tecla Delete → `handle_delete_key_press()` → `handle_delete_item()` → `handle_delete_item_by_uuid()`

Fluxo unificado:
1. Valida o nó
2. Pede confirmação ao usuário
3. Chama `model.delete_node()`
4. Salva o projeto
5. Atualiza a UI

### Sincronização de Nós de Dados (Fase 1)
**Função central:** `MainController.sync_data_nodes_for_parent()`

Gerencia adição e remoção de tipos de dados:
1. Calcula diferenças (via `model.get_types_to_remove()`)
2. Pede confirmação se houver remoções
3. Chama `model.sync_data_nodes()` que:
   - Remove tipos não desejados
   - Adiciona tipos faltantes
4. Salva o projeto
5. Atualiza a UI

Chamado por: `DataEntryDialog.do_insert()`

## Expansão Futura

### Módulos Específicos por Tipo de Dado (`src/data_models/`)

Cada tipo de dado (barras, cabos_bt, etc.) poderá ter seu próprio módulo:

```python
# Exemplo: src/data_models/barras_model.py

class BarrasModel:
    """Lógica específica para dados de barras."""
    
    def get_column_headers(self) -> list:
        """Retorna cabeçalhos customizados para a tabela."""
        return ["Barra", "Tensão Nominal (V)", "Corrente 3P (A)", ...]
    
    def validate_data(self, data: dict) -> tuple[bool, str]:
        """Valida dados específicos de barras."""
        if not data.get('nominalVoltage'):
            return False, "Tensão nominal é obrigatória"
        return True, ""
    
    def get_editor_widget(self, field: str) -> QWidget:
        """Retorna widget de edição customizado."""
        if field == 'nominalVoltage':
            return VoltageComboBox()  # Widget especializado
        return QLineEdit()
```

### Regras de Negócio (`src/core/business/`)

Para lógica complexa que não pertence ao Model principal:

```python
# Exemplo: src/core/business/electrical_calculations.py

def calculate_short_circuit_current(voltage, impedance):
    """Calcula corrente de curto-circuito."""
    ...

def validate_cable_sizing(current, cable_type):
    """Valida dimensionamento de cabos."""
    ...
```

### Testes (`tests/`)

Estrutura planejada para testes unitários:
```
tests/
├── test_project_model.py
├── test_data_sync.py
├── test_deletion_logic.py
└── test_data_models/
    ├── test_barras_model.py
    └── test_cabos_bt_model.py
```

## Princípios de Design

1. **Separação de Responsabilidades:** MVC estrito
2. **Single Source of Truth:** Operações críticas centralizadas
3. **DRY (Don't Repeat Yourself):** Reutilização de código
4. **Extensibilidade:** Fácil adicionar novos tipos de dados
5. **Testabilidade:** Lógica isolada e testável

## Execução

```bash
# Desenvolvimento
python src/main.py

# Produção (Windows)
run.bat
```

## Dependências

- Python 3.13+
- PyQt6 (interface gráfica)
- pandas (manipulação de dados)
- openpyxl (importação Excel)

Ver `requirements.txt` para versões específicas.

## Histórico

- **Fase 1 (2026-03-03):** Centralização da lógica de sincronização de nós
- **Fase 2 (2026-03-03):** Unificação da lógica de exclusão
- **Fase 3 (2026-03-03):** Preparação para expansão futura
