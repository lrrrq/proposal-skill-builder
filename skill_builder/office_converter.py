"""
office_converter - Office 文件转换（PPTX → PDF）
"""

import subprocess
import shutil
from pathlib import Path
from typing import Optional


def find_libreoffice_executable() -> Optional[Path]:
    """
    查找 LibreOffice 可执行文件（跨平台）

    Returns:
        Path 或 None

    Cross-platform note
    -------------------
    On macOS the binary lives inside an .app bundle, on Linux it's usually
    under /usr/bin or /opt, and on Windows it's under Program Files.
    ``shutil.which`` is portable, so we trust PATH first and only fall
    back to platform-specific absolute paths if PATH lookup fails.
    """
    candidates = [
        # PATH-resolved names — work on every platform when LibreOffice is
        # installed system-wide (Homebrew apt, choco, scoop, etc.).
        "soffice",
        "soffice.exe",
        "libreoffice",
        "libreoffice.exe",
        # Platform-specific absolute paths as last resort.
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",          # macOS GUI install
        "/usr/bin/soffice",                                              # Debian/Ubuntu
        "/usr/bin/libreoffice",
        "/opt/homebrew/bin/soffice",                                     # Homebrew (Apple Silicon)
        "/opt/homebrew/bin/libreoffice",
        "/usr/local/bin/soffice",                                        # Homebrew (Intel)
        "/usr/local/bin/libreoffice",
        r"C:\Program Files\LibreOffice\program\soffice.exe",             # Windows default
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",       # Windows 32-bit
    ]

    for candidate in candidates:
        found = shutil.which(candidate)
        if found:
            return Path(found)

    return None


def convert_pptx_to_pdf(input_path: Path, output_dir: Path) -> Optional[Path]:
    """
    使用 LibreOffice 将 PPTX 转换为 PDF

    Args:
        input_path: PPTX 文件路径
        output_dir: PDF 输出目录

    Returns:
        PDF 文件路径，或 None（转换失败）
    """
    libreoffice = find_libreoffice_executable()
    if libreoffice is None:
        return None

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 使用 LibreOffice 转换命令
        # soffice --headless --convert-to pdf --outdir output_dir input.pptx
        result = subprocess.run(
            [
                str(libreoffice),
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(output_dir),
                str(input_path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,  # 2分钟超时
        )

        if result.returncode != 0:
            return None

        # 查找生成的 PDF
        # LibreOffice 会把 input.pptx 转换为 input.pdf 在 output_dir
        pdf_name = input_path.stem + ".pdf"
        pdf_path = output_dir / pdf_name

        if pdf_path.exists():
            return pdf_path

        return None

    except Exception:
        return None


def is_libreoffice_available() -> bool:
    """检查 LibreOffice 是否可用"""
    return find_libreoffice_executable() is not None