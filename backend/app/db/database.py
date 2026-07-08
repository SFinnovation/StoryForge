# -*- coding: utf-8 -*-
"""数据库连接管理
- 默认 SQLite(开发): sqlite:///./storyforge.db
- 通过环境变量 DATABASE_URL 可切换 MySQL(部署):
  mysql+pymysql://user:pass@host:3306/storyforge?charset=utf8mb4
"""
import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./storyforge.db")

# SQLite 需要关闭同线程检查以配合 FastAPI 多线程
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,   # MySQL 长连接保活; SQLite 下无副作用
    echo=False,
)

# SQLite 默认不启用外键约束, 每个连接都要显式打开
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _enable_sqlite_fk(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类"""


def get_db():
    """FastAPI 依赖注入用的会话生成器

    用法:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)): ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
