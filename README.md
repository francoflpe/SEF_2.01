# SEF-2.01 - Software de Estudos Focus

## Resumo

Aplicação desktop em PyQt6 para gerenciamento de projetos elétricos com arquitetura MVC robusta. 

O projeto permite:
- Criar e gerenciar projetos hierárquicos (árvore de nós)
- Adicionar tipos de dados específicos (barras, cabos, disjuntores, etc.)
- Importar/exportar dados de arquivos Excel, CSV e JSON
- Sincronizar automaticamente nós de dados
- Visualizar dados tabulares com Pandas
- Salvar projetos em formato JSON estruturado

## Arquitetura

O projeto segue **padrão MVC** estrito com estrutura modular:

```
src/
├── main.py                 # Ponto de entrada
├── core/                   # Núcleo MVC
│   ├── main_controller.py # Orquestrador
│   ├── main_view.py       # Interface Qt
│   ├── project_model.py   # Lógica de negócio
│   └── commands.py        # Undo/Redo
├── components/            # Componentes UI reutilizáveis
│   ├── data_entry_dialog.py
│   └── project_metadata_dialog.py
├── data/                  # Camada de dados
│   ├── data_map.py       # Schemas de tipos
│   ├── data_map.json     # Configuração de schemas
│   └── pandas_model.py   # Adapter Pandas↔Qt
├── data_models/          # Modelos especializados (FUTURO)
│   └── barras_model.py   # Template de exemplo
└── utils/                # Utilitários
    ├── project_config.py
    ├── migration.py
    └── migrate_cli.py
```

Ver [ARQUITETURA.md](ARQUITETURA.md) para detalhes completos.

## Requisitos

- **Python 3.13+**
- PyQt6 (interface gráfica)
- pandas (manipulação de dados)
- openpyxl (importação Excel - opcional)

## Instalação

```bash
# Clone o repositório
git clone <repository-url>
cd SEF-2.01

# Crie ambiente virtual (recomendado)
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Instale dependências
pip install -r requirements.txt
```

## Execução

### Windows
```bash
# Opção 1: Script conveniente
run.bat

# Opção 2: Comando direto
python src/main.py
```

### Linux/Mac
```bash
python src/main.py
```

## Funcionalidades Principais

### 1. Gerenciamento de Projetos
- Criar novo projeto com metadados (CS, cliente)
- Abrir projetos existentes (JSON)
- Salvar/Salvar Como
- Detectar mudanças não salvas

### 2. Árvore Hierárquica
- Adicionar/remover nós
- Renomear nós (F2)
- Excluir nós (Delete)
- Copiar/colar estruturas
- Menu de contexto

### 3. Tipos de Dados
- **Barras** - Barramentos elétricos
- **Cabos BT/MT** - Cabos de baixa/média tensão
- **Disjuntores BT/MT** - Dispositivos de proteção
- **Fusíveis** - Proteção por fusível
- **Chaves Seccionadoras** - Chaves de manobra
- **Saturação TC** - Transformadores de corrente

### 4. Editor de Dados
- Interface intuitiva com checkboxes
- Pré-visualização de mudanças (Adicionar/Ignorar/Remover)
- Importação de Excel/CSV/JSON
- Validação de unicidade (não permite duplicatas)
- Confirmação de remoções
- Backup automático (.bak)

### 5. Visualização
- QTreeView - Explorador de projeto
- QTableView - Dados tabulares (Pandas)
- Alternância de visualização por tipo

## Refatorações Recentes (Março 2026)

### Fase 1: Centralização da Lógica de Sincronização
✅ **Método único:** `ProjectModel.sync_data_nodes()`  
✅ **Orquestração:** `MainController.sync_data_nodes_for_parent()`  
✅ **Simplificação:** `DataEntryDialog.do_insert()` → uma única chamada  

### Fase 2: Unificação da Lógica de Exclusão
✅ **Função central:** `MainController.handle_delete_item_by_uuid()`  
✅ **Consistência:** Todas exclusões passam pelo mesmo fluxo  
✅ **Confirmação:** Sempre pede confirmação antes de excluir  

### Fase 3: Preparação para Expansão
✅ **Estrutura modular:** `src/data_models/` criado  
✅ **Template:** `barras_model.py` como exemplo  
✅ **Documentação:** ARQUITETURA.md completo  

Ver [REFATORACAO.md](REFATORACAO.md) para histórico detalhado.

## Estrutura de Dados (JSON)

```json
{
  "projectMetadata": {
    "programa": "SEF - Software de Estudos Focus",
    "versao": "2.0.0",
    "dataDeCriacao": "03/03/2026 12:00",
    "CS": "1234",
    "cliente": "Empresa XYZ"
  },
  "projectTree": {
    "<uuid>": {
      "logicalId": "root",
      "displayName": "CS-1234 - Empresa XYZ",
      "isDataNode": true,
      "nodes": {
        "<uuid-filho>": {
          "logicalId": "node-1",
          "displayName": "Subestação Principal",
          "isDataNode": false,
          "dataType": "barras",
          "data": {
            "componentType": "Bus",
            "nominalVoltage": "13800",
            ...
          },
          "nodes": {}
        }
      }
    }
  }
}
```

## Migração de Dados

Para migrar projetos em lote:

```bash
# Arquivo único
python src/utils/migrate_cli.py --file projeto.json

# Diretório recursivo
python src/utils/migrate_cli.py --dir ./projetos
```

## Desenvolvimento Futuro

### Modelos Especializados (`src/data_models/`)
Cada tipo de dado poderá ter:
- Validações específicas
- Widgets customizados
- Formatação de valores
- Cálculos derivados

Exemplo:
```python
from data_models.barras_model import BarrasModel

model = BarrasModel()
headers = model.get_column_headers()
is_valid, errors = model.validate_data(data_dict)
widget = model.get_editor_widget("nominalVoltage")
```

### Regras de Negócio (`src/core/business/`)
Lógica complexa separada do Model principal:
- Cálculos elétricos
- Validações multi-campos
- Conversões de unidades

### Testes Automatizados (`tests/`)
```bash
pytest tests/
```

## Contribuindo

1. Fork o repositório
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## Princípios de Design

- **MVC Estrito:** Separação clara de responsabilidades
- **Single Source of Truth:** Operações centralizadas
- **DRY:** Evitar duplicação de código
- **Extensibilidade:** Fácil adicionar novos tipos
- **Testabilidade:** Lógica isolável

## Suporte

Para dúvidas ou problemas:
1. Consulte [ARQUITETURA.md](ARQUITETURA.md)
2. Consulte [REFATORACAO.md](REFATORACAO.md)
3. Abra uma issue no repositório

## Licença

[Especificar licença]

---

**Versão:** 2.0.0  
**Última atualização:** Março 2026

Contato
- Se quiser, adiciono um script `run_merge_test.py` ou exemplos adicionais de uso (testes automatizados). Diga qual você prefere.
# Aplicação de Análise de Dados Desktop

Este projeto é uma aplicação desktop para Windows, criada em Python com PyQt6, para manipulação de dados e cálculos numéricos, com uma arquitetura robusta e um sistema de gerenciamento de projeto baseado em JSON.

## 1. Pilha de Tecnologia (Tech Stack)

-   **Linguagem:** Python
-   **Interface Gráfica (GUI):** PyQt6
-   **Manipulação de Dados:** Pandas
-   **Cálculos Numéricos:** NumPy e SciPy (quando necessário)
-   **Gráficos:** Matplotlib
-   **Internacionalização:** `QTranslator` para tradução de componentes da interface.
-   **Empacotamento:** PyInstaller para criar o executável (`.exe`).
-   **Gerenciamento de Dependências:** `venv` e `requirements.txt`.

---

## 2. 🏛️ Arquitetura e Princípios de Código

Este documento define as regras e a filosofia de desenvolvimento para o projeto. O objetivo é criar um código limpo, sustentável e de fácil manutenção. **O GitHub Copilot e todos os desenvolvedores devem seguir estas diretrizes rigorosamente.**

### 2.1. Arquitetura Model-View-Controller (MVC)

O projeto segue uma variação do padrão **MVC** para garantir a separação de responsabilidades.

-   #### 📄 `model.py` - O Modelo (Model)
    -   **Responsabilidade:** Gerenciamento dos dados e da lógica de negócio. Contém a classe `ProjectModel`.
    -   **Regras:**
        -   É a única "fonte da verdade" para os dados do projeto (estrutura JSON, DataFrames, etc.).
        -   **NÃO** deve ter conhecimento da interface gráfica (ou seja, não deve importar `PyQt6`).
        -   Contém toda a lógica para carregar, manipular e salvar o arquivo de projeto `.json`.

-   #### 📄 `view.py` - A Visão (View)
    -   **Responsabilidade:** Apresentação da interface gráfica do usuário (GUI). Contém a classe `MainView`.
    -   **Regras:**
        -   Define a estrutura, o layout e a aparência dos widgets (`QMainWindow`, `QDockWidget`, etc.).
        -   É "passiva" (`dumb`). Não contém lógica de negócio.
        -   Quando o usuário interage, a `View` emite um **sinal** para notificar o `Controller`.

-   #### 📄 `controller.py` - O Controlador (Controller)
    -   **Responsabilidade:** Orquestrar a comunicação entre o `Model` e a `View`. Contém a classe `MainController`.
    -   **Regras:**
        -   Conecta os sinais da `View` aos seus próprios métodos (slots).
        -   Recebe as ações do usuário, invoca métodos do `Model` para processar dados e, em seguida, chama métodos da `View` para atualizar a exibição.
        -   Gerencia o estado da aplicação, como a pilha de `QUndoStack`.

-   #### 📄 `main.py` - O Ponto de Entrada
    -   **Responsabilidade:** Apenas inicializar e executar a aplicação.
    -   **Regras:**
        -   Configura o `QApplication` e carrega as traduções (`QTranslator`).
        -   Instancia o `MainController`.
        -   Inicia o loop de eventos da aplicação.

### 2.2. Princípios Fundamentais de Código

1.  **Responsabilidade Única (SRP):** Cada classe e método deve ter uma, e apenas uma, razão para existir e ser modificado. A estrutura MVC é a principal aplicação deste princípio.

2.  **Não se Repita (DRY):** Evite código duplicado. Refatore lógicas repetidas em métodos privados ou funções de utilidade e chame-os de onde for necessário.

3.  **Código Limpo e Legível:**
    -   **Nomenclatura Clara:** Use nomes descritivos para variáveis, funções e classes.
    -   **Funções Pequenas:** Métodos devem ser curtos e focados em uma única tarefa.
    -   **Tipagem de Dados (Type Hinting):** Todas as assinaturas de funções devem usar *type hints* (PEP 484).
    -   **Estilo PEP 8:** O código deve seguir o guia de estilo oficial do Python (use um formatador como o **Black**).
    -   **Documentação:** Use docstrings para todos os módulos, classes e métodos públicos.
    -   **Sem Ruído Visual:** **NÃO** adicione comentários decorativos ou separadores (`# ===`). A organização deve vir da estrutura do código.

---

## 3. 💾 Estrutura do Arquivo de Projeto (`.json`)

O projeto utiliza um arquivo `.json` para armazenar a hierarquia e os metadados.

### 3.1. `projectMetadata`

Contém informações gerais sobre o projeto.

```json
"projectMetadata": {
    "programa": "SEF - Software de Estudos Focus",
    "versao": "2.0.0",
    "dataDeCriacao": "28/02/2026 11:00",
    "CS": "12345",
    "cliente": "Empresa Exemplo"
}
```

### 3.2. `projectTree`

Define a estrutura hierárquica dos itens.

-   **Nós Estruturais vs. Nós de Dados:** Um nó só pode ter **ou** sub-nós (`nodes`) **ou** dados (`data`), nunca ambos.
    -   **Nó Estrutural (`node-X` com filhos):** Sua responsabilidade é organizar outros nós. Seu `isDataNode` é `false`.
    -   **Nó de Dados (`node-X` sem filhos ou `node-X.Y`):** É um "nó folha" que armazena os dados principais. Seu `isDataNode` é `true`.

-   **Estrutura de um Nó:**
    -   `logicalId`: Identificador hierárquico legível (`root`, `node-1`, `node-1.1`).
    -   `displayName`: Nome visível para o usuário.
    -   `isDataNode`: Booleano que indica se é um nó de dados ativo.
    -   `data`: Um dicionário reservado para armazenar os dados associados a um "nó de dados".
    -   `nodes`: Um dicionário que contém os nós filhos.

**Exemplo de Estrutura:**

```json
"projectTree": {
  "f4b7a1e0-...": {
    "logicalId": "root",
    "displayName": "CS-12345 - Empresa Exemplo",
    "isDataNode": false,
    "data": {},
    "nodes": {
      "a3b8e1c-...": {
        "logicalId": "node-1",
        "displayName": "Análise A",
        "isDataNode": false,
        "data": {},
        "nodes": {
          "f9e8a7b-...": {
            "logicalId": "node-1.1",
            "displayName": "Dados Sísmicos",
            "isDataNode": true,
            "data": { "tipo": "sísmica 3D", "linhas": 500 },
            "nodes": {}
          }
        }
      }
    }
  }
}
```

---

## 4. Arquitetura de Produtividade

### 4.1. Controle de Salvamento (Dirty State)

A aplicação gerencia um estado "sujo" (`is_dirty`) para rastrear modificações não salvas. Um asterisco `[*]` no título da janela indica ao usuário que há trabalho pendente de salvamento. O estado `is_dirty` é `false` apenas após salvar ou carregar um projeto.

### 4.2. Sistema de Desfazer/Refazer (Undo/Redo) Seletivo

O sistema `QUndoStack` é usado de forma **seletiva** para garantir uma experiência de usuário fluida sem comprometer a integridade da estrutura do projeto.

-   **Ações Desfazíveis:** Operações de edição que não alteram a estrutura fundamental, como **renomear um nó**, são encapsuladas em `QUndoCommand` e podem ser desfeitas/refeitas.
-   **Ações Permanentes:** Operações que modificam a estrutura da árvore, como **adicionar ou excluir um nó**, são **permanentes e imediatas**. Elas modificam o `ProjectModel` diretamente e disparam um salvamento no arquivo `.json`, não sendo adicionadas à pilha de Desfazer/Refazer.

Esta abordagem híbrida oferece a conveniência do Undo para edições textuais e a segurança de operações estruturais definitivas.

### 4.3. Lógica de Copiar/Colar

A funcionalidade permite duplicar nós. Ao copiar, um "snapshot" dos dados do nó é serializado como JSON e armazenado no `QClipboard`. A ação de colar desserializa esses dados para criar um novo nó com as propriedades do original.