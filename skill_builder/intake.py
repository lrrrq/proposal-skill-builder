"""
intake - 文件摄入
"""

from pathlib import Path
from typing import List, Dict

from .config import Config
from .db import get_cursor, get_connection
from .utils import calculate_sha256, guess_mime_type, safe_move_file, now_iso, generate_file_id


ALLOWED_EXTENSIONS = {".pdf", ".pptx", ".docx", ".doc", ".md", ".txt"}


def scan_staging() -> List[Path]:
    """扫描 staging 目录，返回所有待处理文件"""
    staging = Config.STAGING_DIR
    if not staging.exists():
        return []

    files = []
    for ext in ALLOWED_EXTENSIONS:
        files.extend(staging.glob(f"*{ext}"))
        files.extend(staging.glob(f"*{ext.upper()}"))
    return sorted(files)


def check_duplicate_sha256(sha256: str) -> bool:
    """检查 SHA256 是否已存在于数据库"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM source_files WHERE sha256 = ? LIMIT 1", (sha256,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists


def record_file(
    file_id: str,
    original_filename: str,
    current_path: str,
    sha256: str,
    file_size: int,
    mime_type: str,
    status: str,
    dataset: str = "prod",
    error_message: str = None
):
    """记录文件到数据库"""
    with get_cursor() as cur:
        cur.execute("""
            INSERT INTO source_files
            (file_id, original_filename, current_path, sha256, file_size, mime_type, status, dataset, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (file_id, original_filename, current_path, sha256, file_size, mime_type, status, dataset, error_message))


def process_file(filepath: Path, dataset: str = "prod") -> Dict:
    """
    处理单个文件

    Returns:
        {
            "filename": str,
            "status": "accepted" | "duplicate" | "rejected" | "error",
            "message": str,
            "file_id": str,
        }
    """
    result = {
        "filename": filepath.name,
        "status": "error",
        "message": "",
        "file_id": None,
    }

    try:
        if not filepath.exists():
            result["message"] = "文件不存在"
            return result

        sha256 = calculate_sha256(filepath)
        file_size = filepath.stat().st_size

        ext = filepath.suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            dest = safe_move_file(filepath, Config.REJECTED_DIR)
            record_file(
                file_id=generate_file_id(),
                original_filename=filepath.name,
                current_path=str(dest),
                sha256=sha256,
                file_size=file_size,
                mime_type=guess_mime_type(filepath),
                status="rejected",
                dataset=dataset,
                error_message=f"不支持的格式: {ext}"
            )
            result["status"] = "rejected"
            result["message"] = f"格式不支持，已移至 rejected: {ext}"
            return result

        if check_duplicate_sha256(sha256):
            dest = safe_move_file(filepath, Config.DUPLICATES_DIR)
            record_file(
                file_id=generate_file_id(),
                original_filename=filepath.name,
                current_path=str(dest),
                sha256=sha256,
                file_size=file_size,
                mime_type=guess_mime_type(filepath),
                status="duplicate",
                dataset=dataset,
                error_message="SHA256 重复"
            )
            result["status"] = "duplicate"
            result["message"] = "SHA256 重复，已移至 duplicates"
            return result

        dest = safe_move_file(filepath, Config.ACCEPTED_DIR)
        file_id = generate_file_id()
        record_file(
            file_id=file_id,
            original_filename=filepath.name,
            current_path=str(dest),
            sha256=sha256,
            file_size=file_size,
            mime_type=guess_mime_type(filepath),
            status="accepted",
            dataset=dataset
        )
        result["status"] = "accepted"
        result["message"] = f"已摄入: {file_id}"
        result["file_id"] = file_id
        return result

    except Exception as e:
        result["message"] = f"处理失败: {str(e)}"
        return result


def ingest_all(dataset: str = "prod") -> List[Dict]:
    """摄入 staging 目录下所有合法文件"""
    files = scan_staging()
    if not files:
        return []

    results = []
    for filepath in files:
        result = process_file(filepath, dataset=dataset)
        results.append(result)

    return results


def generate_report(results: List[Dict], output_path: Path):
    """生成 intake 报告"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total = len(results)
    accepted = sum(1 for r in results if r["status"] == "accepted")
    duplicate = sum(1 for r in results if r["status"] == "duplicate")
    rejected = sum(1 for r in results if r["status"] == "rejected")
    errors = sum(1 for r in results if r["status"] == "error")

    lines = [
        "# Intake Report",
        "",
        f"**生成时间**: {now_iso()}",
        f"**总扫描数**: {total}",
        f"**Accepted**: {accepted}",
        f"**Duplicate**: {duplicate}",
        f"**Rejected**: {rejected}",
        f"**Error**: {errors}",
        "",
        "---",
        "",
        "## 详细结果",
        "",
    ]

    for i, r in enumerate(results, 1):
        status_icon = {
            "accepted": "✅",
            "duplicate": "📋",
            "rejected": "❌",
            "error": "⚠️",
        }.get(r["status"], "❓")

        lines.append(f"### {i}. {r['filename']} {status_icon}")
        lines.append(f"- **状态**: {r['status']}")
        lines.append(f"- **消息**: {r['message']}")
        if r.get("file_id"):
            lines.append(f"- **File ID**: `{r['file_id']}`")
        lines.append("")

    lines.extend([
        "---",
        "",
        "*由 Proposal Skill Builder 自动生成*",
    ])

    output_path.write_text("\n".join(lines), encoding="utf-8")


def run_intake(dataset: str = "prod"):
    """执行 intake 并生成报告"""
    print("=" * 50)
    print("Proposal Skill Builder - Intake")
    print("=" * 50)
    print()
    print(f"[Dataset]: {dataset}")
    print()

    Config.STAGING_DIR.mkdir(parents=True, exist_ok=True)

    print("[1/4] 扫描 staging 目录...")
    files = scan_staging()
    print(f"  发现 {len(files)} 个文件")
    print()

    if not files:
        print("  staging 目录为空，无文件需要处理")
        empty_results = []
        report_path = Config.REPORTS_DIR / "intake_report.md"
        generate_report(empty_results, report_path)
        print(f"  已生成空报告: reports/intake_report.md")
        print()
        print("=" * 50)
        return

    print("[2/4] 处理文件...")
    results = ingest_all(dataset=dataset)
    print()

    print("[3/4] 统计结果...")
    accepted = sum(1 for r in results if r["status"] == "accepted")
    duplicate = sum(1 for r in results if r["status"] == "duplicate")
    rejected = sum(1 for r in results if r["status"] == "rejected")
    errors = sum(1 for r in results if r["status"] == "error")
    print(f"  Accepted: {accepted}")
    print(f"  Duplicate: {duplicate}")
    print(f"  Rejected: {rejected}")
    print(f"  Error: {errors}")
    print()

    print("[4/4] 生成报告...")
    report_path = Config.REPORTS_DIR / "intake_report.md"
    generate_report(results, report_path)
    rel_path = report_path.relative_to(Config.PROJECT_ROOT)
    print(f"  报告已生成: {rel_path}")
    print()

    print("=" * 50)
    print("Intake 完成！")
    print()