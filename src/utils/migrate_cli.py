"""CLI utilitário para executar migração em um ou vários arquivos `teste.json`.

Uso:
  python migrate_cli.py --file path/to/teste.json
  python migrate_cli.py --dir path/to/search

Se `--dir` for fornecido, o script procura recursivamente por arquivos chamados `teste.json`.
"""
import argparse
import os
import sys
from utils import migration
from utils import project_config


def migrate_file(path: str) -> int:
    try:
        changed = migration.migrate_project(path)
        if changed > 0:
            print(f"Migrated: {path} ({changed} changes)")
        else:
            print(f"No changes: {path}")
        return changed
    except FileNotFoundError:
        print(f"File not found: {path}")
        return 0
    except Exception as e:
        print(f"Error migrating {path}: {e}")
        return 0


def migrate_dir(root: str) -> int:
    total = 0
    for dirpath, dirs, files in os.walk(root):
        for name in files:
            if name == 'teste.json':
                path = os.path.join(dirpath, name)
                total += migrate_file(path)
    return total


def main(argv=None):
    parser = argparse.ArgumentParser(description='Batch migrate teste.json files to schema format')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--file', '-f', help='Path to a teste.json file')
    group.add_argument('--dir', '-d', help='Directory to search recursively for teste.json')
    args = parser.parse_args(argv)

    if args.file:
        changed = migrate_file(args.file)
        return 0 if changed >= 0 else 1
    else:
        changed = migrate_dir(args.dir)
        print(f"Total changes applied: {changed}")
        return 0


if __name__ == '__main__':
    sys.exit(main())
