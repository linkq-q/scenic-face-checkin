"""
一键建表脚本。

使用方法：
  cd backend
  python init_db.py

脚本会自动创建 scenic_face 数据库（如不存在），然后依据 SQLAlchemy 模型建表。
"""

import sys

import pymysql
from sqlalchemy import text

# 导入所有模型，确保 metadata 已注册
import app.models  # noqa: F401
from app.core.config import settings
from app.database import Base, engine


def create_database_if_not_exists() -> None:
    conn = pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        charset="utf8mb4",
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{settings.DB_NAME}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
        conn.commit()
        print(f"[OK] 数据库 `{settings.DB_NAME}` 已就绪")
    finally:
        conn.close()


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    print("[OK] 数据表创建完成：visitors, tickets, checkin_logs")


def verify_tables() -> None:
    with engine.connect() as conn:
        result = conn.execute(text("SHOW TABLES;"))
        tables = [row[0] for row in result]
    print(f"[OK] 当前库中的表：{tables}")


if __name__ == "__main__":
    try:
        create_database_if_not_exists()
        create_tables()
        verify_tables()
        print("\n初始化完成，可以启动服务了。")
    except Exception as exc:
        print(f"[ERROR] 初始化失败：{exc}", file=sys.stderr)
        sys.exit(1)
