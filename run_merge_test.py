"""Script de teste para validar merge-on-write.

Ele:
- cria um backup de `teste.json`;
- encontra o primeiro nó com `isDataNode == True`;
- aplica um merge de exemplo (adiciona/atualiza alguns campos de `cabos_bt`);
- grava o arquivo e mostra o antes/depois.

Use como: `python run_merge_test.py`
"""
import json
import os
import shutil
from datetime import datetime
import sys

# Adiciona src/ ao path para permitir imports dos módulos
ROOT = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(ROOT, 'src'))

from utils import project_config  # type: ignore
TESTE = project_config.get_project_file(prompt_if_missing=False) or os.path.join(ROOT, 'teste.json')


def backup(path):
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = path + f'.testbak_{ts}'
    shutil.copy2(path, dest)
    return dest


def find_first_data_node(tree: dict):
    for uid, node in tree.items():
        if node.get('isDataNode'):
            return uid, node
        # search children
        nodes = node.get('nodes', {})
        if isinstance(nodes, dict):
            for child_uid, child in nodes.items():
                if child.get('isDataNode'):
                    return child_uid, child
    return None, None


def apply_merge(node: dict, insertion: dict) -> dict:
    existing = node.get('data', {}) if isinstance(node.get('data', {}), dict) else {}
    changed = False
    for tipo, novo in insertion.items():
        antigo = existing.get(tipo)
        if isinstance(novo, dict):
            if isinstance(antigo, dict):
                for k, v in novo.items():
                    if v is not None and v != "":
                        antigo[k] = v
                        changed = True
                merged = antigo
            else:
                merged = novo
                changed = True
        else:
            if isinstance(antigo, dict):
                merged = antigo
            else:
                merged = novo
                changed = True
        existing[tipo] = merged
    if changed:
        node['data'] = existing
    return node


def main():
    if not os.path.exists(TESTE):
        print('teste.json not found')
        return

    bak = backup(TESTE)
    print('Backup created:', bak)

    with open(TESTE, 'r', encoding='utf-8') as f:
        projeto = json.load(f)

    uid, node = find_first_data_node(projeto.get('projectTree', {}))
    if not uid:
        print('No data node found')
        return

    print('Testing node:', uid)
    before = node.get('data', {})
    print('Before (excerpt):', {k: before.get(k) for k in ['cabos_bt', 'cabos_mt'] if k in before})

    # insertion sample: update some fields of cabos_bt
    insertion = {
        'cabos_bt': {
            'cableSize': '95',
            'ampacity': '220',
            'connectedBus': 'BUS_A'
        }
    }

    apply_merge(node, insertion)

    with open(TESTE, 'w', encoding='utf-8') as f:
        json.dump(projeto, f, indent=4, ensure_ascii=False)

    with open(TESTE, 'r', encoding='utf-8') as f:
        projeto2 = json.load(f)

    # locate the updated node by uid
    def find_by_uid(tree, target):
        if target in tree:
            return tree[target]
        for v in tree.values():
            nodes = v.get('nodes', {})
            if isinstance(nodes, dict):
                found = find_by_uid(nodes, target)
                if found:
                    return found
        return None

    updated = find_by_uid(projeto2.get('projectTree', {}), uid)
    after = updated.get('data', {}) if updated else {}
    print('After (excerpt):', {k: after.get(k) for k in ['cabos_bt', 'cabos_mt'] if k in after})


if __name__ == '__main__':
    main()
