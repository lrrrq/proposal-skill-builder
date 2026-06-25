"""
drift_check - 检查并修复 source_files 表与 filesystem 之间的 drift

## 背景

proposal-skill-builder 是离线 CLI 工具，所有"源文件"的状态都在
source_files 表里。但实际场景里会出现：

1. 用户 git pull / 迁移 / 误删 accepted 目录
2. 数据库保留了 sha256 + current_path，但 fs 找不到
3. 后续 compile-case 会失败："文件不存在"

这种 db/fs 不一致就叫 "source drift"。

## 命令

- inspect-source-drift: 列出所有 drift（只读）
- repair-source-drift:  可选 mark 给 drift 行打 error_message
"""
import sqlite3
from datetime import datetime
from pathlib import Path

from .config import Config
from .db import get_connection


def _drift_marker(reason: str) -> str:
    """Generate a deterministic error_message for a drift row."""
    ts = datetime.utcnow().strftime("%Y-%m-%d")
    return f"source drift ({ts}): {reason}"


def inspect_source_drift(dataset: str = "all") -> dict:
    """Walk source_files, return rows whose current_path is missing on disk.

    Returns:
        {
            "success": True,
            "dataset": "all" | "prod" | "test",
            "total_scanned": int,
            "missing_count": int,
            "missing": [
                {
                    "file_id": str,
                    "original_filename": str,
                    "current_path": str,
                    "status": str,
                    "case_id": str | None,
                    "dataset": str,
                },
                ...
            ],
            "scanned_at": ISO8601 str,
        }
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        if dataset == "all":
            rows = conn.execute(
                "SELECT file_id, original_filename, current_path, status, case_id, dataset "
                "FROM source_files ORDER BY file_id"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT file_id, original_filename, current_path, status, case_id, dataset "
                "FROM source_files WHERE dataset=? ORDER BY file_id",
                (dataset,),
            ).fetchall()

        missing = []
        for r in rows:
            p = Path(r["current_path"])
            if not p.exists():
                missing.append({
                    "file_id": r["file_id"],
                    "original_filename": r["original_filename"],
                    "current_path": r["current_path"],
                    "status": r["status"],
                    "case_id": r["case_id"],
                    "dataset": r["dataset"],
                })

        return {
            "success": True,
            "dataset": dataset,
            "total_scanned": len(rows),
            "missing_count": len(missing),
            "missing": missing,
            "scanned_at": datetime.utcnow().isoformat() + "Z",
        }
    finally:
        conn.close()


def repair_source_drift(dataset: str = "all", dry_run: bool = True) -> dict:
    """Mark drift rows in source_files.error_message.

    Default dry_run=True: do not modify the DB; just report what would change.
    Set dry_run=False to actually update.

    Args:
        dataset: filter by dataset ("all", "prod", "test")
        dry_run: if True, only report; if False, UPDATE error_message

    Returns:
        {
            "success": True,
            "dry_run": bool,
            "dataset": str,
            "would_mark": int,            # rows that would/will be marked
            "marked": int,                # rows actually marked (0 if dry_run)
            "missing": [...],             # same shape as inspect_source_drift
            "marked_at": ISO8601 str | None,
        }
    """
    inspection = inspect_source_drift(dataset=dataset)
    missing = inspection["missing"]
    would_mark = len(missing)
    marked = 0
    marked_at = None

    if not dry_run and missing:
        conn = get_connection()
        try:
            cur = conn.cursor()
            now = datetime.utcnow().isoformat() + "Z"
            for m in missing:
                msg = _drift_marker(
                    f"file_id={m['file_id']} case_id={m['case_id']} path missing on disk; "
                    f"re-intake required to recover"
                )
                cur.execute(
                    "UPDATE source_files SET error_message=? WHERE file_id=?",
                    (msg, m["file_id"]),
                )
                marked += cur.rowcount
            conn.commit()
            marked_at = now
        finally:
            conn.close()

    return {
        "success": True,
        "dry_run": dry_run,
        "dataset": dataset,
        "missing_count": len(missing),
        "would_mark": would_mark,
        "marked": marked,
        "missing": missing,
        "marked_at": marked_at,
    }