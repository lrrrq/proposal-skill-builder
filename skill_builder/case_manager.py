"""
case_manager - 案例管理
"""

import json
import os
import shutil
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict

from .config import Config
from .db import get_connection
from .utils import now_iso


def get_next_case_number() -> int:
    """获取下一个 case 序号（找最大数字后加1）"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT case_id FROM cases")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return 1

    max_num = 0
    for row in rows:
        case_id = row["case_id"]
        try:
            num = int(case_id.replace("case_", ""))
            if num > max_num:
                max_num = num
        except ValueError:
            continue

    return max_num + 1


def cleanup_case_artifacts(case_dir: Path, meta_tmp_path: Path = None):
    """清理 case 相关产物（目录和临时文件）"""
    # 先清理 .tmp 文件
    if meta_tmp_path and meta_tmp_path.exists():
        try:
            meta_tmp_path.unlink()
        except Exception:
            pass

    # 清理目录内的 .tmp 文件
    if case_dir.exists():
        for p in case_dir.glob("*.tmp"):
            try:
                p.unlink()
            except Exception:
                pass

        # 只删除空目录
        try:
            if not any(case_dir.iterdir()):
                case_dir.rmdir()
        except Exception:
            pass


def write_json_atomic_temp(meta_path: Path, data: dict) -> Path:
    """
    原子写入 JSON（先写 .tmp 再 rename）

    失败时确保 .tmp 文件被清理，不会残留。
    """
    tmp_path = Path(str(meta_path) + ".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        return tmp_path
    except Exception:
        # 写入失败时确保清理残留的 .tmp 文件
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass
        raise


def rollback_created_case(case_id: str, source_file_id: str):
    """
    回滚已创建的 case（用于处理原子替换失败后的紧急修复）

    1. 从 cases 表删除记录
    2. 将 source_files.case_id 置空
    3. 删除 case 目录

    如果回滚也失败，必须抛出明确异常。
    """
    conn = get_connection()
    cur = conn.cursor()

    try:
        # 删除 cases 记录
        cur.execute("DELETE FROM cases WHERE case_id = ?", (case_id,))

        # 将 source_files.case_id 置空
        cur.execute(
            "UPDATE source_files SET case_id = NULL, updated_at = ? WHERE file_id = ?",
            (now_iso(), source_file_id)
        )

        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        raise RuntimeError(
            f"回滚失败，需要人工修复！\n"
            f"请手动执行：\n"
            f"  1. DELETE FROM cases WHERE case_id = '{case_id}';\n"
            f"  2. UPDATE source_files SET case_id = NULL WHERE file_id = '{source_file_id}';\n"
            f"  3. rm -rf {Config.CASES_DIR / case_id}\n"
            f"错误: {str(e)}"
        )
    finally:
        conn.close()

    # 删除 case 目录
    case_dir = Config.CASES_DIR / case_id
    if case_dir.exists():
        try:
            shutil.rmtree(case_dir)
        except Exception:
            pass


def create_case(source_file_id: str, title: str) -> Dict:
    """
    为 source_file 创建 case

    严格保证数据库和文件系统的一致性：
    - 先准备好所有数据和临时文件
    - 再开启数据库事务
    - 数据库成功后原子替换临时文件
    - 任何失败都要回滚

    Returns:
        {"success": bool, "case_id": str, "message": str, "meta_path": str}
    """
    # ========== 阶段 1: 前置检查和准备 ==========

    conn = get_connection()

    # 检查 source_file 是否存在
    cur = conn.cursor()
    cur.execute("SELECT * FROM source_files WHERE file_id = ?", (source_file_id,))
    source_file = cur.fetchone()

    if source_file is None:
        conn.close()
        return {"success": False, "case_id": None, "message": f"文件不存在: {source_file_id}"}

    # 检查状态是否为 accepted
    if source_file["status"] != "accepted":
        conn.close()
        return {
            "success": False,
            "case_id": None,
            "message": f"文件状态不是 accepted（当前: {source_file['status']}），无法创建案例"
        }

    # 检查是否已有 case_id
    if source_file["case_id"]:
        conn.close()
        return {
            "success": False,
            "case_id": source_file["case_id"],
            "message": f"该文件已绑定案例: {source_file['case_id']}"
        }

    # 生成 case_id
    case_number = get_next_case_number()
    case_id = f"case_{case_number:04d}"
    now = now_iso()

    # 继承 source_file 的 dataset
    dataset = source_file.get("dataset", "prod")

    # 准备 source_meta 数据
    source_meta = {
        "case_id": case_id,
        "title": title,
        "source_file_id": source_file_id,
        "original_filename": source_file["original_filename"],
        "current_path": source_file["current_path"],
        "sha256": source_file["sha256"],
        "file_size": source_file["file_size"],
        "dataset": dataset,
        "created_at": now,
    }

    # 创建 case 目录
    case_dir = Config.CASES_DIR / case_id
    try:
        case_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        conn.close()
        return {"success": False, "case_id": None, "message": f"无法创建 case 目录: {str(e)}"}

    # 写入临时 JSON 文件
    meta_path = case_dir / "source_meta.json"
    tmp_path = None
    try:
        tmp_path = write_json_atomic_temp(meta_path, source_meta)
    except Exception as e:
        cleanup_case_artifacts(case_dir, tmp_path)
        conn.close()
        return {"success": False, "case_id": None, "message": f"无法写入 meta 临时文件: {str(e)}"}

    # ========== 阶段 2: 数据库事务 ==========

    try:
        cur.execute("""
            INSERT INTO cases (case_id, title, status, dataset, created_at, updated_at)
            VALUES (?, ?, 'draft', ?, ?, ?)
        """, (case_id, title, dataset, now, now))

        cur.execute("""
            UPDATE source_files
            SET case_id = ?, updated_at = ?
            WHERE file_id = ?
        """, (case_id, now, source_file_id))

        conn.commit()
    except sqlite3.IntegrityError as e:
        # case_id 唯一约束冲突
        conn.rollback()
        conn.close()
        cleanup_case_artifacts(case_dir, tmp_path)
        return {
            "success": False,
            "case_id": None,
            "message": f"case_id 冲突，请重新运行 create-case。错误: {str(e)}"
        }
    except Exception as e:
        conn.rollback()
        conn.close()
        cleanup_case_artifacts(case_dir, tmp_path)
        return {"success": False, "case_id": None, "message": f"数据库事务失败: {str(e)}"}

    # ========== 阶段 3: 原子替换临时文件 ==========

    try:
        tmp_path = Path(str(meta_path) + ".tmp")
        os.replace(tmp_path, meta_path)  # 跨平台原子替换
    except Exception as e:
        # 原子替换失败，需要回滚数据库
        try:
            rollback_created_case(case_id, source_file_id)
        except RuntimeError as re:
            conn.close()
            return {
                "success": False,
                "case_id": case_id,
                "message": f"严重错误：原子替换失败且回滚也失败。{str(re)}",
                "meta_path": None
            }
        conn.close()
        return {"success": False, "case_id": None, "message": f"原子替换 meta 文件失败，已回滚: {str(e)}"}

    conn.close()

    return {
        "success": True,
        "case_id": case_id,
        "message": f"案例创建成功: {case_id}",
        "meta_path": str(meta_path),
    }


def list_files() -> List[Dict]:
    """列出所有 source_files"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT file_id, original_filename, status, case_id
        FROM source_files
        ORDER BY created_at DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def list_cases(dataset: str = "all") -> List[Dict]:
    """列出所有 cases（含 source file 信息，支持 dataset 筛选）"""
    conn = get_connection()
    cur = conn.cursor()

    if dataset == "all":
        cur.execute("""
            SELECT c.case_id, c.title, c.status, c.dataset, c.created_at,
                   sf.original_filename, sf.current_path
            FROM cases c
            LEFT JOIN source_files sf ON c.case_id = sf.case_id
            ORDER BY c.created_at DESC
        """)
    else:
        cur.execute("""
            SELECT c.case_id, c.title, c.status, c.dataset, c.created_at,
                   sf.original_filename, sf.current_path
            FROM cases c
            LEFT JOIN source_files sf ON c.case_id = sf.case_id
            WHERE c.dataset = ?
            ORDER BY c.created_at DESC
        """, (dataset,))

    rows = cur.fetchall()
    conn.close()

    results = []
    for row in rows:
        d = dict(row)
        current_path = d.get("current_path") or ""
        ext = ""
        if current_path:
            p = Path(current_path)
            ext = p.suffix.lower()
        d["source_ext"] = ext
        results.append(d)

    return results


def get_case_by_id(case_id: str) -> Optional[Dict]:
    """根据 case_id 获取 case 详情"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_file_by_id(file_id: str) -> Optional[Dict]:
    """根据 file_id 获取 source_file 详情"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM source_files WHERE file_id = ?", (file_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None