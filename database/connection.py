import importlib
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

DB_FILE = Path(__file__).parent.parent / "database.db"
MIGRATIONS_DIR = Path(__file__).parent / "migrations"
SEEDS_DIR = MIGRATIONS_DIR / "seeds"


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def setup_database() -> None:
    """Exécute toutes les migrations SQL dans l'ordre."""
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        raise FileNotFoundError(f"Aucun fichier de migration dans : {MIGRATIONS_DIR}")
    with get_connection() as conn:
        for migration_file in migration_files:
            conn.executescript(migration_file.read_text(encoding="utf-8"))


def run_seeds() -> None:
    """Exécute tous les seeders Python dans l'ordre."""
    seed_files = sorted(f for f in SEEDS_DIR.glob("*.py") if f.name != "__init__.py")
    if not seed_files:
        raise FileNotFoundError(f"Aucun seeder dans : {SEEDS_DIR}")
    for seed_file in seed_files:
        module = importlib.import_module(f"database.migrations.seeds.{seed_file.stem}")
        print(f"  {seed_file.name}…", end=" ")
        module.run()
        print("ok")