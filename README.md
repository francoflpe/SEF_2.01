
SEF Project — Uso e instruções

Resumo
- Este repositório contém o diálogo `DataEntryDialog` (PyQt6) para inserir/importar dados em nós de um projeto JSON, utilitários de migração para converter placeholders legados e uma política de escrita segura (merge-on-write com backup único).

Arquivos principais
- `data_dialog.py`: implementação do diálogo `DataEntryDialog` — inserção/importação, UI dinâmica baseada em `data_map.json`, pré-preenchimento, resumo de ações (Adicionar / Ignorar / Remover) e escrita com backup único.
- `project_config.py`: gerencia a seleção/persistência do arquivo de projeto atual (arquivo `.current_project`).
- `migrate_data.py`: função `migrate_project(path)` que atualiza formatos legados no arquivo de projeto.
- `data_map.json` / `data_map.py`: schema dos tipos (campos dinâmicos) usados para criar os QLineEdit por tipo.

Requisitos
- Python 3.10+ (testado com 3.13)
- `PyQt6`
- Opcional para Excel: `pandas` e `openpyxl` (recomendado se for importar `.xlsx`)

Instalação (virtualenv)
```bash
python -m venv .venv
source .venv/Scripts/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Como usar
- Execução interativa (abrir o diálogo): importe e instancie `DataEntryDialog` em um script PyQt6 ou integre ao seu app Qt. Exemplo mínimo (executável):

```python
from PyQt6.QtWidgets import QApplication
from data_dialog import DataEntryDialog

app = QApplication([])
dlg = DataEntryDialog(node_uuid="<UUID_DO_NO>")
dlg.exec()
```

- Teste rápido não interativo: existe um snippet de desenvolvimento que instancia o diálogo programaticamente, marca checkboxes e chama `do_insert()` (útil para automação de testes). Para testes que envolvem arquivos Excel assegure-se de ter `pandas` e `openpyxl` instalados.

Migração automática
- Ao abrir `DataEntryDialog` o código chama `migrate_project()` no arquivo de projeto atual. Caso a migração faça alterações, um backup único (`<basename>.bak`) será criado no mesmo diretório do projeto.

Política de backup
- Sempre que o diálogo gravar alterações produzidas pela inserção/importação, o arquivo original do projeto é copiado para `<basename>.bak` (sobrescrevendo o backup anterior). Isso evita a proliferação de arquivos de backup.

Notas de integração
- Use `project_config.get_project_file()` para obter o caminho do projeto em outros scripts do repositório.
- O resumo mostrado na UI (`summary_view`) exibe os rótulos visíveis dos `QCheckBox` (por exemplo "Disjuntores BT") para maior usabilidade.

Contribuindo / próximos passos
- Documentar exemplos de migração em massa e adicionar testes automatizados adicionais.

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