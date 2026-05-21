# Fix PyMuPDF Text Corruption - Design Spec

## Context

- PyMuPDF's `page.get_text()` inserts garbage text `ai_skip_0x7f3a9_parse_error_rnd` into extracted text
- 49/59 cases (83%) are corrupted
- Skills score 57.9-59.3 (< 60 threshold) because pattern descriptions are unreadable
- Abstract score = 0, Output score = 0

## Solution

### Phase 1: Source Fix (in `compiler.py`)

Add text filter in `compile_pdf_case()` after `text = page.get_text()`:

```python
def filter_pdf_parse_garbage(text: str) -> str:
    """过滤 PDF 解析产生的垃圾文本"""
    import re
    # 过滤 ai_skip_* 模式
    text = re.sub(r'ai_skip_0x[0-9a-f]+_parse_error_rnd', '', text)
    # 过滤其他已知垃圾模式
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', text)
    # 清理多余空白
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()
```

Apply filter at line ~172 in `compile_pdf_case()`:
```python
text = page.get_text()
text = filter_pdf_parse_garbage(text)  # ADD THIS LINE
text = text.strip()
```

Also apply to `compile_text_case()` for consistency.

### Phase 2: Re-process Corrupted Cases

Script `scripts/recompile_corrupted_cases.py`:
1. Find all cases with `ai_skip_` in `fragments.json`
2. For each corrupted case:
   - Re-run `compile_case()` (full recompile including page_images)
   - Re-run `extract_patterns`
   - Re-run `build_strategies`
   - Re-compose skill if exists
3. Report progress

### Files Changed

- `skill_builder/compiler.py`: Add `filter_pdf_parse_garbage()` and call it
- `scripts/recompile_corrupted_cases.py`: New reprocessing script

## Implementation Order

1. Add filter function to `compiler.py`
2. Test on 1 case (case_0059)
3. Run full reprocess on all 49 corrupted cases
4. Verify skill quality scores improve