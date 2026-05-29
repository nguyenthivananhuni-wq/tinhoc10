"""Copy TOÀN BỘ dữ liệu từ SQLite local (data/app.db) sang Postgres.

Mục đích: sau khi chuyển deploy sang Postgres, dữ liệu mới giống y hệt dữ liệu
cũ ở máy local (user, attempt, mastery, goal, topic, question — kèm nguyên ID).

Cách dùng (chạy ở MÁY LOCAL, KHÔNG phải trên Render):

    # Lấy "External Database URL" của Postgres trong Render Dashboard, rồi:
    # PowerShell:
    $env:TARGET_DATABASE_URL = "postgresql://user:pass@host.singapore-postgres.render.com/dbname"
    venv\Scripts\python.exe -m scripts.migrate_to_postgres

Mặc định script CHỈ chèn vào bảng đang rỗng (an toàn, không ghi đè).
Thêm --wipe để xóa sạch dữ liệu đích trước khi copy (dùng khi muốn ép giống hệt local).
Thêm --dry-run để chỉ xem sẽ copy bao nhiêu dòng, không ghi gì.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Console Windows mặc định cp1252 không in được tiếng Việt có dấu → ép UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from sqlalchemy import create_engine, func, select, text

# Đăng ký toàn bộ bảng vào metadata để biết thứ tự khóa ngoại.
from app.models import (  # noqa: F401  (import để metadata có đủ bảng)
    Attempt,
    LearningGoal,
    MasteryState,
    Question,
    Topic,
    User,
)
from sqlmodel import SQLModel

SQLITE_PATH = Path(__file__).resolve().parent.parent / "data" / "app.db"


def _normalize(url: str) -> str:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wipe", action="store_true", help="Xóa sạch bảng đích trước khi copy")
    ap.add_argument("--dry-run", action="store_true", help="Chỉ đếm, không ghi")
    args = ap.parse_args()

    target_raw = os.environ.get("TARGET_DATABASE_URL", "").strip()
    if not target_raw:
        print("LỖI: chưa đặt TARGET_DATABASE_URL (External Database URL của Render Postgres).")
        return 1
    if not SQLITE_PATH.exists():
        print(f"LỖI: không thấy SQLite nguồn tại {SQLITE_PATH}")
        return 1

    src = create_engine(f"sqlite:///{SQLITE_PATH}")
    dst = create_engine(_normalize(target_raw), pool_pre_ping=True)

    # Tạo bảng ở đích nếu chưa có.
    if not args.dry_run:
        SQLModel.metadata.create_all(dst)

    # sorted_tables: bảng cha (được tham chiếu) đứng trước bảng con → đúng thứ tự INSERT.
    ordered = SQLModel.metadata.sorted_tables

    with src.connect() as sconn, dst.begin() as dconn:
        if args.wipe and not args.dry_run:
            # Xóa theo thứ tự ngược (con trước, cha sau) để không vỡ khóa ngoại.
            for tbl in reversed(ordered):
                dconn.execute(tbl.delete())
                print(f"[wipe] đã xóa sạch {tbl.name}")

        for tbl in ordered:
            rows = [dict(r._mapping) for r in sconn.execute(select(tbl))]
            if not rows:
                print(f"[skip] {tbl.name}: nguồn rỗng")
                continue

            if not args.wipe:
                existing = dconn.execute(select(func.count()).select_from(tbl)).scalar_one()
                if existing:
                    print(f"[skip] {tbl.name}: đích đã có {existing} dòng (dùng --wipe để ghi đè)")
                    continue

            if args.dry_run:
                print(f"[dry] {tbl.name}: sẽ copy {len(rows)} dòng")
                continue

            dconn.execute(tbl.insert(), rows)
            print(f"[copy] {tbl.name}: {len(rows)} dòng")

        # Reset sequence của Postgres để ID tự tăng tiếp sau MAX(id) hiện có.
        if not args.dry_run and dst.dialect.name == "postgresql":
            for tbl in ordered:
                if "id" in tbl.c:
                    dconn.execute(
                        text(
                            "SELECT setval(pg_get_serial_sequence(:t, 'id'), "
                            # Bọc tên bảng trong "" vì có tên (vd user) trùng từ khóa Postgres.
                            'COALESCE((SELECT MAX(id) FROM "' + tbl.name + '"), 1), true)'
                        ),
                        {"t": tbl.name},
                    )
            print("[seq] đã reset sequence Postgres")

    print("XONG." if not args.dry_run else "DRY-RUN xong (chưa ghi gì).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
