#!/usr/bin/env python3
"""
CLI de gestion de la base de données Mini Trello.

Commandes disponibles :
  migrate   — exécute les migrations SQL (crée / met à jour les tables)
  seed      — insère les données de démonstration
  reset     — supprime la BDD, re-migre et re-seed

Usage depuis la racine du projet :
  python scripts/db.py migrate
  python scripts/db.py seed
  python scripts/db.py reset
"""
import argparse
import os
import sys

# Rendre les imports du projet disponibles quel que soit le répertoire de lancement du script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import DB_FILE, run_seeds, setup_database


def cmd_migrate(_args) -> None:
    print("→ Migrations en cours…")
    setup_database()
    print("✓ Migrations terminées.")


def cmd_seed(_args) -> None:
    print("→ Seeds en cours…")
    run_seeds()
    print("✓ Seeds terminés.")


def cmd_reset(_args) -> None:
    print("→ Réinitialisation de la base de données…")
    if DB_FILE.exists():
        DB_FILE.unlink()
        print(f"  BDD supprimée : {DB_FILE}")
    setup_database()
    print("  Migrations exécutées.")
    run_seeds()
    print("✓ Réinitialisation terminée.")


_COMMANDS = {
    "migrate": cmd_migrate,
    "seed":    cmd_seed,
    "reset":   cmd_reset,
}

parser = argparse.ArgumentParser(
    prog="python scripts/db.py",
    description="Gestion de la base de données Mini Trello",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=(
        "Exemples :\n"
        "  python scripts/db.py migrate   # initialise les tables\n"
        "  python scripts/db.py seed      # insère les données de démo\n"
        "  python scripts/db.py reset     # repart de zéro\n"
    ),
)
subparsers = parser.add_subparsers(dest="command", metavar="commande")
subparsers.add_parser("migrate", help="Exécuter les migrations SQL")
subparsers.add_parser("seed",    help="Insérer les données de démonstration")
subparsers.add_parser("reset",   help="Supprimer la BDD, re-migrer et re-seeder")

args = parser.parse_args()

if args.command in _COMMANDS:
    _COMMANDS[args.command](args)
else:
    parser.print_help()
