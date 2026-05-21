# PyMuPDF Text Corruption Fix - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix PyMuPDF text corruption by adding filter to `compiler.py` and reprocessing 49 corrupted cases.

**Architecture:** Add text filter function that removes `ai_skip_0x[0-9a-f]+_parse_error_rnd` garbage patterns from PDF text extraction. Create reprocessing script to re-run compile + extract-patterns + build-strategies on corrupted cases.

**Tech Stack:** Python, PyMuPDF, sqlite3, existing skill_builder CLI

---

## Task 1: Add `filter_pdf_parse_garbage()` to `compiler.py`

**Files:**
- Modify: `skill_builder/compiler.py:1-24` (imports section)
- Modify: `skill_builder/compiler.py:150-285` (compile_pdf_case function)
- Test: Manual verification by running `python3 -m skill_builder.cli compile-case case_0059`

- [ ] **Step 1: Add filter function after imports (line ~24)**

```python
def filter_pdf_parse_garbage(text: str) -> str:
    """过滤 PDF 解析产生的垃圾文本

    PyMuPDF 有时会插入 ai_skip_0x[hex]_parse_error_rnd 标记，
    这些需要被清理。
    """
    import re
    # 过滤 ai_skip_* 模式
    text = re.sub(r'ai_skip_0x[0-9a-f]+_parse_error_rnd', '', text)
    # 过滤控制字符 (\x00-\x1f except \x09\x0a\x0d)
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', text)
    # 清理多余换行
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()
```

- [ ] **Step 2: Apply filter in compile_pdf_case after text extraction (line ~172)**

Find this code:
```python
        # 提取文本
        text = page.get_text()
        text = text.strip()
```

Replace with:
```python
        # 提取文本
        text = page.get_text()
        text = filter_pdf_parse_garbage(text)
        text = text.strip()
```

- [ ] **Step 3: Test on case_0059**

Run: `cd /Applications/lrq/coding/proposal-skill-builder && python3 -m skill_builder.cli compile-case case_0059`

Expected: Success, check fragments.json for no `ai_skip_` content

- [ ] **Step 4: Verify fix**

Run: `python3 -c "import json; f=open('compiled/cases/case_0059/fragments.json'); data=json.load(f); corrupt=[x for x in data if 'ai_skip_' in x['raw_text']]; print(f'Corrupted fragments: {len(corrupt)}')"`

Expected: `Corrupted fragments: 0`

- [ ] **Step 5: Commit**

```bash
git add skill_builder/compiler.py
git commit -m "fix: add filter_pdf_parse_garbage to remove PyMuPDF garbage text"
```

---

## Task 2: Create `scripts/recompile_corrupted_cases.py`

**Files:**
- Create: `scripts/recompile_corrupted_cases.py`
- Run: Manual test script

- [ ] **Step 1: Create the reprocessing script**

```python
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
```

- [ ] **Step 2: Run on first 3 corrupted cases as test**

Run: `cd /Applications/lrq/coding/proposal-skill-builder && python3 scripts/recompile_corrupted_cases.py 2>&1 | head -80`

Expected: See 3 cases being reprocessed, each step showing ✅ or ❌

- [ ] **Step 3: Commit script**

```bash
git add scripts/recompile_corrupted_cases.py
git commit -m "feat: add script to reprocess corrupted cases"
```

---

## Task 3: Run full reprocess on all corrupted cases

**Files:**
- Run: `scripts/recompile_corrupted_cases.py`
- Verify: Check skill quality scores improve

- [ ] **Step 1: Run full reprocess**

Run: `cd /Applications/lrq/coding/proposal-skill-builder && python3 scripts/recompile_corrupted_cases.py`

Expected: Processing 49 cases, each 4 steps

- [ ] **Step 2: Verify skill quality improvement**

Run: `python3 -m skill_builder.cli check-skill luxury-hotel-festival 2>&1 | grep -E "评分|建议等级|通过项"`

Expected: Score improved above 60 if case was reprocessed

- [ ] **Step 3: Check batch-validation scores**

Run: `python3 -m skill_builder.cli batch-validation --limit 5 2>&1`

Expected: Higher scores than before (57.9-59.3 range should improve)