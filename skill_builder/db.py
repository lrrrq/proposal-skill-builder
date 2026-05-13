"""
数据库 - SQLite 管理
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager

from .config import Config

# 允许操作的表名白名单
ALLOWED_TABLES = {"source_files", "cases", "jobs", "skills"}


def get_db_path():
    return Config.DB_PATH


def get_connection():
    """获取数据库连接"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_cursor():
    """上下文管理器：自动提交/回滚"""
    conn = get_connection()
    try:
        yield conn.cursor()
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _validate_table_name(table_name: str) -> bool:
    """验证表名是否在白名单中"""
    return table_name in ALLOWED_TABLES


def get_table_columns(table_name: str) -> set:
    """获取表的所有列名"""
    if not _validate_table_name(table_name):
        raise ValueError(f"不允许操作表: {table_name}")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    columns = {row["name"] for row in cur.fetchall()}
    conn.close()
    return columns


def ensure_column(table_name: str, column_name: str, column_sql: str):
    """确保表有指定列，不存在则添加"""
    if not _validate_table_name(table_name):
        raise ValueError(f"不允许操作表: {table_name}")

    existing = get_table_columns(table_name)
    if column_name not in existing:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}")
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def _ensure_unique_index(table_name: str, index_name: str, columns: tuple):
    """确保唯一索引存在"""
    if not _validate_table_name(table_name):
        raise ValueError(f"不允许操作表: {table_name}")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS {index_name} ON {table_name}({','.join(columns)})")
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise RuntimeError(
            f"创建唯一索引失败，可能是历史数据有重复值。\n"
            f"表: {table_name}, 索引: {index_name}, 列: {columns}\n"
            f"请先清理重复数据后再运行 init。\n"
            f"错误: {str(e)}"
        )
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"创建索引失败: {str(e)}")
    finally:
        conn.close()


def run_migrations():
    """运行数据库迁移"""
    # 添加 case_id 列
    ensure_column("source_files", "case_id", "TEXT")

    # 添加 dataset 列（所有表）
    ensure_column("source_files", "dataset", "TEXT DEFAULT 'prod'")
    ensure_column("cases", "dataset", "TEXT DEFAULT 'prod'")
    ensure_column("jobs", "dataset", "TEXT DEFAULT 'prod'")
    ensure_column("skills", "dataset", "TEXT DEFAULT 'prod'")

    # 创建唯一索引（防止数据不一致）
    _ensure_unique_index("cases", "idx_cases_case_id", ("case_id",))
    _ensure_unique_index("source_files", "idx_source_files_file_id", ("file_id",))


def init_db():
    """初始化数据库"""
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = get_connection()
    cur = conn.cursor()

    # source_files 表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS source_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT UNIQUE NOT NULL,
            original_filename TEXT NOT NULL,
            current_path TEXT NOT NULL,
            sha256 TEXT,
            file_size INTEGER,
            mime_type TEXT,
            status TEXT DEFAULT 'staging',
            case_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            error_message TEXT
        )
    """)

    # cases 表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT UNIQUE NOT NULL,
            title TEXT,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # jobs 表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT UNIQUE NOT NULL,
            case_id TEXT,
            stage TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            started_at TIMESTAMP,
            finished_at TIMESTAMP,
            error_message TEXT,
            FOREIGN KEY (case_id) REFERENCES cases(case_id)
        )
    """)

    # skills 表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_id TEXT UNIQUE NOT NULL,
            display_name TEXT,
            status TEXT DEFAULT 'draft',
            quality_level TEXT DEFAULT 'bronze',
            callable INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

    # 运行迁移
    run_migrations()


def get_stats():
    """获取统计数据"""
    stats = {}

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM source_files WHERE status = 'staging'")
    stats["staging"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM source_files WHERE status = 'accepted'")
    stats["accepted"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM source_files WHERE status = 'duplicate'")
    stats["duplicates"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM source_files WHERE status = 'rejected'")
    stats["rejected"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM cases")
    stats["cases"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM skills WHERE status = 'published'")
    stats["published_skills"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM skills WHERE status = 'draft'")
    stats["draft_skills"] = cur.fetchone()[0]

    conn.close()

    return stats