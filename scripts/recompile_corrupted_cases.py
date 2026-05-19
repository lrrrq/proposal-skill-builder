#!/usr/bin/env python3
"""
recompile_corrupted_cases.py

重新处理被 PyMuPDF 垃圾文本污染的 cases。
对每个 corrupted case:
1. 重新编译 (compile-case)
2. 重新提取 patterns (extract-patterns)
3. 重新构建 strategies (build-strategies)
4. 如果有 skill，重新组合 (compose-skill)
"""

import json
import subprocess
import sys
from pathlib import Path

SKILL_BUILDER = Path(__file__).parent.parent
CASES_DIR = SKILL_BUILDER / "compiled" / "cases"

def find_corrupted_cases():
    """找到所有包含 ai_skip_ 垃圾文本的 cases"""
    corrupted = []
    for case_dir in CASES_DIR.iterdir():
        if not case_dir.is_dir() or not case_dir.name.startswith("case_"):
            continue
        fragments_path = case_dir / "fragments.json"
        if not fragments_path.exists():
            continue
        try:
            data = json.loads(fragments_path.read_text())
            for frag in data:
                if "ai_skip_" in frag.get("raw_text", ""):
                    corrupted.append(case_dir.name)
                    break
        except Exception:
            continue
    return sorted(corrupted)

def run_command(cmd, cwd=None):
    """运行命令并返回结果"""
    result = subprocess.run(
        cmd, shell=True, cwd=cwd or SKILL_BUILDER,
        capture_output=True, text=True
    )
    return result.returncode, result.stdout, result.stderr

def reprocess_case(case_id):
    """重新处理单个 case"""
    print(f"\n{'='*60}")
    print(f"处理: {case_id}")
    print('='*60)

    # 1. compile-case
    print(f"[1/4] compile-case {case_id}")
    code, out, err = run_command(f"python3 -m skill_builder.cli compile-case {case_id}")
    if code != 0:
        print(f"  ❌ compile-case 失败: {err[:200]}")
        return False
    print(f"  ✅ compile-case 完成")

    # 2. extract-patterns
    print(f"[2/4] extract-patterns {case_id}")
    code, out, err = run_command(f"python3 -m skill_builder.cli extract-patterns {case_id}")
    if code != 0:
        print(f"  ❌ extract-patterns 失败: {err[:200]}")
        return False
    print(f"  ✅ extract-patterns 完成")

    # 3. build-strategies
    print(f"[3/4] build-strategies {case_id}")
    code, out, err = run_command(f"python3 -m skill_builder.cli build-strategies {case_id}")
    if code != 0:
        print(f"  ❌ build-strategies 失败: {err[:200]}")
        return False
    print(f"  ✅ build-strategies 完成")

    # 4. 检查是否有 draft skill 需要重新组合
    skill_id = case_id.replace("case_", "skill-")  # case_0059 -> skill-0059
    draft_skill = SKILL_BUILDER / "skills" / "draft" / skill_id
    if draft_skill.exists():
        print(f"[4/4] compose-skill {case_id}")
        code, out, err = run_command(f"python3 -m skill_builder.cli compose-skill {case_id} --skill-id {skill_id}")
        if code != 0:
            print(f"  ⚠️  compose-skill 失败（跳过）: {err[:200]}")
        else:
            print(f"  ✅ compose-skill 完成")
    else:
        print(f"[4/4] (无 draft skill，跳过)")

    return True

def main():
    print("🔍 查找被污染的 cases...")
    corrupted = find_corrupted_cases()
    print(f"找到 {len(corrupted)} 个被污染的 cases")

    if not corrupted:
        print("✅ 没有被污染的 cases")
        return

    print("\n开始重新处理...")
    success = 0
    failed = []

    for case_id in corrupted:
        if reprocess_case(case_id):
            success += 1
        else:
            failed.append(case_id)

    print(f"\n{'='*60}")
    print(f"处理完成: {success} 成功, {len(failed)} 失败")
    if failed:
        print(f"失败: {', '.join(failed)}")

    # 验证修复
    print("\n验证修复结果...")
    still_corrupted = find_corrupted_cases()
    if still_corrupted:
        print(f"⚠️  仍有 {len(still_corrupted)} 个 case 被污染")
    else:
        print("✅ 所有 cases 已修复")

if __name__ == "__main__":
    main()