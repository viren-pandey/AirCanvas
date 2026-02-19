from __future__ import annotations

from pathlib import Path

from sqlalchemy import text

from backend.app.db import engine


def main() -> None:
    migrations_dir = Path(__file__).resolve().parents[1] / "migrations"
    migration_files = sorted(migrations_dir.glob("*.sql"))
    if not migration_files:
        print("[MIGRATIONS] No SQL files found.")
        return

    with engine.begin() as connection:
        for file_path in migration_files:
            sql = file_path.read_text(encoding="utf-8")
            connection.exec_driver_sql(sql)
            print(f"[MIGRATIONS] Applied {file_path.name}")


if __name__ == "__main__":
    main()

