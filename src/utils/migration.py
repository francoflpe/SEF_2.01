import json
import os
import shutil
from datetime import datetime
from data import data_map

ROOT = os.path.dirname(__file__)
TESTE_PATH = os.path.join(ROOT, 'teste.json')


def backup_file(path: str) -> str:
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = path + f'.bak_{ts}'
    shutil.copy2(path, dest)
    return dest


def migrate_node(node: dict, types_map: dict) -> int:
    """Migrate 'data' in a single node; returns number of changes made."""
    changed = 0
    if not isinstance(node, dict):
        return 0
    data = node.get('data')
    if isinstance(data, dict):
        # iterate keys to avoid runtime change issues
        for tipo, val in list(data.items()):
            schema = types_map.get(tipo)
            if schema:
                # if value is boolean or not a dict, replace with blank dict
                if not isinstance(val, dict):
                    blank = {k: "" for k in schema.keys()}
                    node['data'][tipo] = blank
                    changed += 1
                else:
                    # if dict, ensure all schema keys exist
                    for k in schema.keys():
                        if k not in val:
                            val[k] = ""
                            changed += 1
    # recurse into children
    children = node.get('nodes', {})
    if isinstance(children, dict):
        for child in children.values():
            changed += migrate_node(child, types_map)
    return changed


def migrate_project(teste_path: str = None) -> int:
    """Execute migration on the given teste.json path (or default TESTE_PATH).

    Returns number of changes applied.
    """
    path = teste_path or TESTE_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    mp = data_map.load_map()
    types_map = mp.get('types', {})

    # read project
    with open(path, 'r', encoding='utf-8') as f:
        projeto = json.load(f)

    changed = 0
    tree = projeto.get('projectTree', {})
    for node in tree.values():
        changed += migrate_node(node, types_map)

    if changed > 0:
        bak = backup_file(path)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(projeto, f, indent=4, ensure_ascii=False)
        return changed
    return 0


def main():
    try:
        changed = migrate_project(TESTE_PATH)
        if changed > 0:
            print(f'Migration applied. {changed} changes made.')
        else:
            print('No changes necessary.')
    except FileNotFoundError:
        print('teste.json not found at', TESTE_PATH)


if __name__ == '__main__':
    main()
