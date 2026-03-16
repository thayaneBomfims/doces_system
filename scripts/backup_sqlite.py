from __future__ import annotations

import argparse
import datetime as dt
import gzip
import os
import pathlib
import sqlite3
import sys


def backup_sqlite(db_path: pathlib.Path, out_dir: pathlib.Path, keep: int, gzip_output: bool) -> pathlib.Path:
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"db_{timestamp}.sqlite3"
    backup_path = out_dir / backup_name

    if not db_path.exists():
        raise FileNotFoundError(f"Banco nao encontrado: {db_path}")

    src = sqlite3.connect(str(db_path))
    dst = sqlite3.connect(str(backup_path))
    try:
        src.execute("PRAGMA wal_checkpoint(FULL)")
        src.backup(dst)
    finally:
        dst.close()
        src.close()

    final_path = backup_path
    if gzip_output:
        gz_path = backup_path.with_suffix(backup_path.suffix + ".gz")
        with open(backup_path, "rb") as f_in, gzip.open(gz_path, "wb", compresslevel=9) as f_out:
            f_out.writelines(f_in)
        backup_path.unlink(missing_ok=True)
        final_path = gz_path

    cleanup_old_backups(out_dir, keep)
    return final_path


def cleanup_old_backups(out_dir: pathlib.Path, keep: int) -> None:
    files = sorted(
        [p for p in out_dir.iterdir() if p.name.startswith("db_") and (p.suffix in {".sqlite3", ".gz"} or p.name.endswith(".sqlite3.gz"))],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for old in files[keep:]:
        old.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cria backup do SQLite com timestamp.")
    parser.add_argument("--db", default="db.sqlite3", help="Caminho do banco SQLite")
    parser.add_argument("--out", default="backups", help="Diretorio de saida dos backups")
    parser.add_argument("--keep", type=int, default=14, help="Quantidade de backups para manter")
    parser.add_argument("--no-gzip", action="store_true", help="Nao comprime o arquivo de backup")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = pathlib.Path(args.db).resolve()
    out_dir = pathlib.Path(args.out).resolve()

    try:
        backup_path = backup_sqlite(
            db_path=db_path,
            out_dir=out_dir,
            keep=max(args.keep, 1),
            gzip_output=not args.no_gzip,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Erro no backup: {exc}", file=sys.stderr)
        return 1

    print(f"Backup criado: {backup_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
