"""
命令实现
"""

import argparse
from pathlib import Path

from .config import Config
from .db import init_db, get_stats
from .intake import run_intake
from .registry import get_registry
from .case_manager import create_case, list_files, list_cases
from .compiler import compile_case
from .pattern_engine import extract_patterns_for_case
from .asset_describer import describe_assets_for_case


def init():
    """初始化命令"""
    print("=" * 50)
    print("Proposal Skill Builder - 初始化")
    print("=" * 50)
    print()

    print("[1/3] 创建目录...")
    created = []
    for dir_path in Config.all_dirs():
        dir_path.mkdir(parents=True, exist_ok=True)
        created.append(str(dir_path.relative_to(Config.PROJECT_ROOT)))
    print(f"  创建了 {len(created)} 个目录")
    for d in created:
        print(f"    - {d}")
    print()

    print("[2/3] 初始化数据库...")
    init_db()
    db_path = Config.DB_PATH
    print(f"  数据库: {db_path.relative_to(Config.PROJECT_ROOT)}")
    print()

    print("[3/3] 初始化注册表...")
    registry = get_registry()
    registry.ensure_registry_file()
    reg_path = Config.SKILL_REGISTRY_JSON
    print(f"  注册表: {reg_path.relative_to(Config.PROJECT_ROOT)}")
    print()

    print("=" * 50)
    print("初始化完成！")
    print()


def status():
    """状态命令"""
    print("=" * 50)
    print("Proposal Skill Builder - 状态")
    print("=" * 50)
    print()

    project_root = Config.PROJECT_ROOT
    print(f"项目目录: {project_root}")
    print()

    print("[数据库]")
    db_exists = Config.DB_PATH.exists()
    if db_exists:
        size = Config.DB_PATH.stat().st_size
        print(f"  数据库: 存在 ({size} bytes)")
        stats = get_stats()
        print(f"  - staging 文件: {stats.get('staging', 0)}")
        print(f"  - accepted 文件: {stats.get('accepted', 0)}")
        print(f"  - duplicates 文件: {stats.get('duplicates', 0)}")
        print(f"  - rejected 文件: {stats.get('rejected', 0)}")
        print(f"  - cases: {stats.get('cases', 0)}")
        print(f"  - draft Skills: {stats.get('draft_skills', 0)}")
        print(f"  - published Skills (DB): {stats.get('published_skills', 0)}")
    else:
        print("  数据库: 不存在（需要运行 init）")
    print()

    print("[注册表]")
    registry = get_registry()
    reg_exists = Config.SKILL_REGISTRY_JSON.exists()
    if reg_exists:
        skills = registry.list_skills()
        print(f"  skill_registry.json: 存在 ({len(skills)} Skills)")
    else:
        print("  skill_registry.json: 不存在")
        skills = []
    print()

    print("[目录]")
    dirs_info = [
        ("staging", Config.STAGING_DIR),
        ("accepted", Config.ACCEPTED_DIR),
        ("duplicates", Config.DUPLICATES_DIR),
        ("rejected", Config.REJECTED_DIR),
        ("draft", Config.DRAFT_DIR),
        ("published", Config.PUBLISHED_DIR),
        ("quarantine", Config.QUARANTINE_DIR),
    ]

    for name, dir_path in dirs_info:
        count = 0
        if dir_path.exists():
            count = len(list(dir_path.iterdir()))
        print(f"  {name}: {count} 个文件/目录")

    # Published skills from filesystem (ground truth)
    published_dir = Config.PUBLISHED_DIR
    published_skills_fs = []
    if published_dir.exists():
        for skill_dir in published_dir.iterdir():
            if skill_dir.is_dir() and "__backup" not in skill_dir.name:
                published_skills_fs.append(skill_dir.name)

    print()
    print(f"[Published Skills: {len(published_skills_fs)}] (from filesystem)")
    if published_skills_fs:
        for skill_id in sorted(published_skills_fs):
            print(f"  - {skill_id}")
    else:
        print("  (none)")
    print()

    # Registry cross-check
    if skills:
        print("[Registry Skills]")
        registry_skill_ids = {s.get("skill_id") for s in skills}
        for s in skills:
            skill_id = s.get("skill_id", "unknown")
            status = s.get("status", "?")
            callable_str = "✅" if s.get("callable") else "❌"
            quality = s.get("quality_level", "?")
            print(f"  {callable_str} {skill_id}: status={status}, quality={quality}")

        # Warnings
        fs_skill_ids = set(published_skills_fs)
        in_fs_not_reg = fs_skill_ids - registry_skill_ids
        in_reg_not_fs = registry_skill_ids - fs_skill_ids

        if in_fs_not_reg:
            print()
            print("⚠️  Published directory exists but NOT in registry:")
            for skill_id in sorted(in_fs_not_reg):
                print(f"  - {skill_id}")

        if in_reg_not_fs:
            print()
            print("⚠️  In registry but NOT in published directory:")
            for skill_id in sorted(in_reg_not_fs):
                print(f"  - {skill_id}")

        # Check if registry paths exist
        print()
        print("[Registry Path Validation]")
        path_issues = []
        for s in skills:
            skill_id = s.get("skill_id", "unknown")
            path = s.get("path", "")
            if path and not Path(path).exists():
                path_issues.append(f"{skill_id}: path does not exist -> {path}")
        if path_issues:
            for issue in path_issues:
                print(f"  ⚠️  {issue}")
        else:
            print("  (all registry paths exist)")

    print()
    print("=" * 50)


def intake(args):
    """intake 命令"""
    run_intake(dataset=args.dataset)


def cmd_create_case(args):
    """create-case 命令"""
    result = create_case(args.file_id, args.title)
    if result["success"]:
        print(f"✅ {result['message']}")
        print(f"   meta: {result.get('meta_path', 'N/A')}")
    else:
        if result.get("case_id"):
            print(f"⚠️  {result['message']}")
            print(f"   已有案例ID: {result['case_id']}")
        else:
            print(f"❌ {result['message']}")


def cmd_list_files(args):
    """list-files 命令"""
    files = list_files()
    if not files:
        print("暂无文件记录")
        return

    print(f"{'FILE_ID':<14} {'FILENAME':<30} {'STATUS':<10} {'DATASET':<8} {'CASE_ID':<12}")
    print("-" * 78)
    for f in files:
        case_id = f.get("case_id") or "-"
        dataset = f.get("dataset") or "-"
        print(f"{f['file_id']:<14} {f['original_filename']:<30} {f['status']:<10} {dataset:<8} {case_id:<12}")


def cmd_list_cases(args):
    """list-cases 命令"""
    cases = list_cases(dataset=args.dataset)
    if not cases:
        print("暂无案例")
        return

    print(f"{'CASE_ID':<12} {'TITLE':<30} {'STATUS':<15} {'DATASET':<8} {'SOURCE_FILENAME':<30} {'EXT':<6}")
    print("-" * 105)
    for c in cases:
        title = (c.get("title") or "-")[:28]
        status = c.get("status") or "-"
        dataset = c.get("dataset") or "-"
        filename = c.get("original_filename") or "-"
        if len(filename) > 28:
            filename = filename[:25] + "..."
        ext = c.get("source_ext") or "-"
        print(f"{c['case_id']:<12} {title:<30} {status:<15} {dataset:<8} {filename:<30} {ext:<6}")


def cmd_compile_case(args):
    """compile-case 命令"""
    result = compile_case(args.case_id)
    if result["success"]:
        print(f"✅ {result['message']}")
        print(f"   输出目录: {result.get('output_dir', 'N/A')}")
        print(f"   Pages: {result.get('pages_count', 0)}, Fragments: {result.get('fragments_count', 0)}")
    else:
        print(f"❌ {result['message']}")
        if result.get("job_id"):
            print(f"   Job ID: {result['job_id']}")


def cmd_extract_patterns(args):
    """extract-patterns 命令"""
    result = extract_patterns_for_case(args.case_id)
    if result["success"]:
        print(f"✅ {result['message']}")
        print(f"   Patterns: {result.get('patterns_count', 0)}")
        print(f"   patterns.json: {result.get('patterns_path', 'N/A')}")
        print(f"   case_card.md: {result.get('card_path', 'N/A')}")
    else:
        print(f"❌ {result['message']}")


def cmd_describe_assets(args):
    """describe-assets 命令"""
    if args.provider == "mock":
        print(f"⚠️  运行在 mock 模式，不调用真实 AI API")

    result = describe_assets_for_case(
        args.case_id,
        provider=args.provider,
        dry_run=args.dry_run,
        limit=args.limit,
        asset_id=args.asset_id,
    )
    if result["success"]:
        print(f"✅ {result['message']}")
        print(f"   总资产: {result.get('total_assets', 0)}")
        print(f"   需要视觉理解: {result.get('needs_vision_count', 0)}")
        print(f"   已处理: {result.get('processed_count', 0)}")
        print(f"   失败: {result.get('failed_count', 0)}")
        print(f"   报告: {result.get('report_path', 'N/A')}")
        if result.get("dry_run"):
            print(f"   模式: DRY-RUN（不调用真实 API）")
    else:
        print(f"❌ {result['message']}")


def cmd_build_ai_fragments(args):
    """build-ai-fragments 命令"""
    from .asset_describer import generate_ai_fragments_for_case

    result = generate_ai_fragments_for_case(args.case_id)
    if result["success"]:
        print(f"✅ {result['message']}")
        print(f"   fragments 数量: {result.get('fragments_count', 0)}")
        print(f"   输出路径: {result.get('output_path', 'N/A')}")
    else:
        print(f"❌ {result['message']}")


def cmd_compose_skill(args):
    """compose-skill 命令"""
    from .composer import compose_skill_for_case

    result = compose_skill_for_case(args.case_id, args.skill_id)
    if result["success"]:
        print(f"✅ {result['message']}")
        print(f"   skill_id: {result.get('skill_id')}")
        print(f"   quality_level: {result.get('quality_level')}")
        print(f"   dataset: {result.get('dataset')}")
        print(f"   输出目录: {result.get('output_dir')}")
    else:
        print(f"❌ {result['message']}")


def cmd_check_skill(args):
    """check-skill 命令"""
    from .skill_checker import check_skill

    result = check_skill(args.skill_id)
    if result["success"]:
        print(f"✅ 检查完成")
        print(f"   skill_id: {result.get('skill_id')}")
        print(f"   评分: {result.get('score')}/100")
        print(f"   建议等级: {result.get('suggested_level')}")
        print(f"   通过项: {result.get('passed_count')}")
        print(f"   失败项: {result.get('failed_count')}")
        if result.get('warnings_count', 0) > 0:
            print(f"   警告项: {result.get('warnings_count')}")
        if result.get('risk_items'):
            print(f"   风险项: {', '.join(result.get('risk_items', []))}")
        print(f"   报告: {result.get('report_path')}")
        if result.get("can_publish"):
            print(f"   建议: 可以发布")
        else:
            print(f"   建议: 不建议发布")
    else:
        print(f"❌ {result['message']}")


def cmd_build_strategies(args):
    """build-strategies 命令"""
    from .strategy_engine import build_strategies_for_case

    result = build_strategies_for_case(args.case_id)
    if result["success"]:
        print(f"✅ {result['message']}")
        print(f"   strategies 数量: {result.get('strategies_count', 0)}")
        print(f"   strategies.json: {result.get('strategies_path', 'N/A')}")
        print(f"   strategy_dna.md: {result.get('dna_path', 'N/A')}")
    else:
        print(f"❌ {result['message']}")


def cmd_compress_fragments(args):
    """compress-fragments 命令"""
    from .compression import compress_fragments_for_case

    result = compress_fragments_for_case(args.case_id)
    if result["success"]:
        print(f"✅ {result['message']}")
        print(f"   原始 Fragments: {result.get('original_count', 0)}")
        print(f"   压缩后 Fragments: {result.get('compressed_count', 0)}")
        print(f"   重复: {result.get('duplicate_count', 0)}")
        print(f"   低信息: {result.get('low_info_count', 0)}")
        print(f"   压缩结果: {result.get('compressed_path', 'N/A')}")
        print(f"   报告: {result.get('report_path', 'N/A')}")
    else:
        print(f"❌ {result['message']}")


def cmd_batch_compile(args):
    """batch-compile 命令"""
    from .case_manager import list_cases as list_all_cases
    from .compiler import compile_case
    from .config import Config

    # 找出需要编译的 case（根据 dataset 筛选）
    dataset_filter = args.dataset
    all_cases = list_all_cases(dataset="all")

    target_statuses = {"draft", "accepted", "compiled_partial", "failed"}

    pending_cases = []
    for c in all_cases:
        if c.get("status") in target_statuses:
            # dataset 筛选
            case_dataset = c.get("dataset", "prod")
            if dataset_filter != "all" and case_dataset != dataset_filter:
                continue
            # 优先选 PDF
            if c.get("source_ext") == ".pdf":
                pending_cases.insert(0, c)
            else:
                pending_cases.append(c)

    # 限制数量
    limit = args.limit
    to_process = pending_cases[:limit]

    if not to_process:
        print(f"没有需要编译的案例 (dataset={dataset_filter})")
        return

    print(f"[Dataset: {dataset_filter}]")
    print(f"找到 {len(pending_cases)} 个待编译案例，将处理前 {len(to_process)} 个")
    print()

    # 编译每个 case
    results = []
    for case in to_process:
        case_id = case["case_id"]
        title = case.get("title") or "-"
        original_filename = case.get("original_filename") or "-"
        source_ext = case.get("source_ext") or "-"
        status_before = case.get("status") or "-"

        try:
            result = compile_case(case_id)
            if result["success"]:
                status_after = result.get("status", "unknown")
                pages_count = result.get("pages_count", 0)
                fragments_count = result.get("fragments_count", 0)
                assets_count = result.get("assets_count", 0)
                error_message = ""
                success = True
            else:
                status_after = "failed"
                pages_count = 0
                fragments_count = 0
                assets_count = 0
                error_message = result.get("message", "unknown error")
                success = False
        except Exception as e:
            status_after = "failed"
            pages_count = 0
            fragments_count = 0
            assets_count = 0
            error_message = str(e)
            success = False

        results.append({
            "case_id": case_id,
            "title": title,
            "dataset": case.get("dataset", "prod"),
            "source_filename": original_filename,
            "source_ext": source_ext,
            "status_before": status_before,
            "status_after": status_after,
            "success": success,
            "pages_count": pages_count,
            "fragments_count": fragments_count,
            "assets_count": assets_count,
            "error_message": error_message,
        })

        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {case_id} ({status_before} → {status_after})")

    # 生成报告
    report_lines = [
        "# Batch Compile Report",
        "",
        f"**生成时间**: {__import__('datetime').datetime.now().isoformat()}",
        f"**处理数量**: {len(results)}",
        f"**Dataset**: {dataset_filter}",
        "",
        "## 汇总",
        "",
        f"- **成功**: {sum(1 for r in results if r['success'])}",
        f"- **失败**: {sum(1 for r in results if not r['success'])}",
        "",
        "## 详情",
        "",
    ]

    for r in results:
        status_icon = "✅" if r["success"] else "❌"
        report_lines.extend([
            f"### {status_icon} {r['case_id']}: {r['title']}",
            f"- **Dataset**: {r.get('dataset', 'unknown')}",
            f"- **Source**: {r['source_filename']} ({r['source_ext']})",
            f"- **Status**: {r['status_before']} → {r['status_after']}",
            f"- **Pages**: {r['pages_count']}, **Fragments**: {r['fragments_count']}, **Assets**: {r['assets_count']}",
        ])
        if r["error_message"]:
            report_lines.append(f"- **Error**: {r['error_message']}")
        report_lines.append("")

    report_path = Config.REPORTS_DIR / "batch_compile_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    print()
    print(f"报告已生成: {report_path}")


def cmd_mark_case_dataset(args):
    """mark-case-dataset 命令"""
    from .db import get_connection
    from .utils import now_iso
    from pathlib import Path

    case_id = args.case_id
    new_dataset = args.dataset

    conn = get_connection()
    cur = conn.cursor()

    # 获取当前 case 信息
    cur.execute("SELECT case_id, dataset FROM cases WHERE case_id = ?", (case_id,))
    case_row = cur.fetchone()
    if not case_row:
        print(f"❌ Case 不存在: {case_id}")
        conn.close()
        return

    old_dataset = case_row["dataset"]

    # 获取绑定的 source_file
    cur.execute("SELECT file_id, dataset FROM source_files WHERE case_id = ?", (case_id,))
    sf_row = cur.fetchone()
    sf_dataset_changed = False

    # 更新 cases.dataset
    cur.execute("UPDATE cases SET dataset = ?, updated_at = ? WHERE case_id = ?",
                (new_dataset, now_iso(), case_id))

    # 同步更新 source_files.dataset
    if sf_row:
        cur.execute("UPDATE source_files SET dataset = ?, updated_at = ? WHERE case_id = ?",
                    (new_dataset, now_iso(), case_id))
        sf_dataset_changed = True

    conn.commit()
    conn.close()

    # 同步更新 source_meta.json
    meta_path = Config.CASES_DIR / case_id / "source_meta.json"
    if meta_path.exists():
        import json
        meta = json.loads(meta_path.read_text())
        meta["dataset"] = new_dataset
        tmp_path = str(meta_path) + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        import os
        os.replace(tmp_path, meta_path)

    print(f"✅ {case_id}: dataset {old_dataset} → {new_dataset}")
    if sf_dataset_changed:
        print(f"   同步更新 source_files.dataset")


def cmd_mark_file_dataset(args):
    """mark-file-dataset 命令"""
    from .db import get_connection
    from .utils import now_iso

    file_id = args.file_id
    new_dataset = args.dataset

    conn = get_connection()
    cur = conn.cursor()

    # 检查 file 是否存在
    cur.execute("SELECT file_id, case_id, dataset FROM source_files WHERE file_id = ?", (file_id,))
    sf_row = cur.fetchone()
    if not sf_row:
        print(f"❌ File 不存在: {file_id}")
        conn.close()
        return

    # 如果已绑定 case，不允许修改
    if sf_row["case_id"]:
        print(f"❌ File 已绑定 case: {sf_row['case_id']}")
        print(f"   请使用 mark-case-dataset")
        conn.close()
        return

    old_dataset = sf_row["dataset"]
    cur.execute("UPDATE source_files SET dataset = ?, updated_at = ? WHERE file_id = ?",
                (new_dataset, now_iso(), file_id))
    conn.commit()
    conn.close()

    print(f"✅ {file_id}: dataset {old_dataset} → {new_dataset}")


def cmd_check_ai_provider(args):
    """check-ai-provider 命令"""
    import os

    provider = args.provider
    print(f"检查 AI Provider: {provider}")
    print("=" * 50)

    if provider == "minimax-text":
        api_key = os.environ.get("MINIMAX_TOKEN_PLAN_KEY", "")
        base_url = os.environ.get("MINIMAX_TEXT_BASE_URL", "https://api.minimaxi.com/v1")
        model = os.environ.get("MINIMAX_TEXT_MODEL", "MiniMax-M2.7")

        print(f"MINIMAX_TOKEN_PLAN_KEY: {'已设置' if api_key else '(未设置)'}")
        print(f"MINIMAX_TEXT_BASE_URL: {base_url}")
        print(f"MINIMAX_TEXT_MODEL: {model}")

        if not api_key:
            print("\n❌ 缺少 MINIMAX_TOKEN_PLAN_KEY")
            return

        print("\n正在测试纯文本 ping...")
        from .ai_client import create_ai_client
        client = create_ai_client(provider)
        result = client.ping()

        if result["success"]:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ Ping 失败: {result['message']}")
            return

        print("\n✅ MiniMax-Text 配置检查通过")
        print("   注意: minimax-text 只能处理文本，不能处理图片")

    elif provider == "minimax-mcp":
        from .ai_client import create_ai_client
        client = create_ai_client(provider)
        env = client.check_environment()

        print(f"uvx 安装: {'✅' if env['uvx_exists'] else '❌ (未安装)'}")
        print(f"MINIMAX_TOKEN_PLAN_KEY: {'已设置' if env['key_exists'] else '❌ (未设置)'}")
        print(f"MCP 图片理解: {'✅ 可用' if env['mcp_available'] else '⚠️ 需先启动 MCP 服务'}")
        print(f"可处理图片: {'✅' if env['can_process_images'] else '❌ 环境未就绪'}")
        print(f"支持格式: {', '.join(env['supported_formats'])}")
        print(f"最大文件: {env['max_size_mb']}MB")

        if not env["can_process_images"]:
            missing = []
            if not env["key_exists"]:
                missing.append("MINIMAX_TOKEN_PLAN_KEY")
            if not env["uvx_exists"]:
                missing.append("uvx")
            print(f"\n❌ 环境未就绪，缺少: {', '.join(missing)}")
            print("  安装 uvx: pip install uvx")
            print("  配置 Key: export MINIMAX_TOKEN_PLAN_KEY=your_key")
            return

        print("\n✅ MiniMax-MCP 环境检查通过")
        print("   真实调用需启动 MCP 服务后使用 describe-assets")

    elif provider == "openai-compatible":
        base_url = os.environ.get("AICLIENT_BASE_URL", "")
        api_key = os.environ.get("AICLIENT_API_KEY", "")
        model = os.environ.get("AICLIENT_MODEL", "")
        supports_vision = os.environ.get("AICLIENT_SUPPORTS_VISION", "true")

        print(f"AICLIENT_BASE_URL: {base_url or '(未设置)'}")
        print(f"AICLIENT_API_KEY: {'已设置' if api_key else '(未设置)'}")
        print(f"AICLIENT_MODEL: {model or '(未设置)'}")
        print(f"AICLIENT_SUPPORTS_VISION: {supports_vision}")

        if not base_url or not api_key:
            print("\n❌ 缺少必需环境变量")
            return

        print("\n正在测试纯文本 ping...")
        from .ai_client import create_ai_client
        client = create_ai_client(provider)
        result = client.ping()

        if result["success"]:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ Ping 失败: {result['message']}")
            return

        if supports_vision.lower() == "false":
            print(f"\n⚠️ 警告: AICLIENT_SUPPORTS_VISION=false，不支持图片输入")

        print("\n✅ Provider 配置检查通过")

    else:
        print(f"❌ 不支持的 provider: {provider}")


def cmd_publish_skill(args):
    """publish-skill 命令"""
    from .publisher import publish_skill

    result = publish_skill(args.skill_id)
    if result["success"]:
        print(f"✅ 发布成功")
        print(f"   skill_id: {args.skill_id}")
        print(f"   published_path: {result.get('published_path', 'N/A')}")
        if result.get("backup_path"):
            print(f"   backup: {result.get('backup_path')}")
        if result.get("warnings"):
            print(f"   警告项: {len(result.get('warnings', []))}")
        print(f"   报告: {result.get('report_path', 'N/A')}")
    else:
        print(f"❌ {result['message']}")
        if result.get("failed_items"):
            for item in result.get("failed_items", []):
                print(f"   - {item}")


def cmd_inspect_registry(args):
    """inspect-registry 命令"""
    from .publisher import inspect_registry

    result = inspect_registry()
    if result["success"]:
        print(f"✅ Registry 检查完成")
        print(f"   registry: {result.get('registry_path')}")
        print(f"   updated_at: {result.get('updated_at') or '从未更新'}")
        print(f"   skills 数量: {result.get('skills_count', 0)}")
        print()

        skills = result.get("skills", [])
        if not skills:
            print("   (no published skills)")
        else:
            for s in skills:
                callable_str = "✅" if s.get("callable") else "❌"
                print(f"   {callable_str} {s['skill_id']} ({s.get('quality_level', '?')})")
                print(f"      path: {s.get('path', 'unknown')}")
                print(f"      source_cases: {len(s.get('source_cases', []))}")
                print()

        issues = result.get("issues", [])
        if issues:
            print("## ⚠️ 问题")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("   无问题")
    else:
        print(f"❌ {result.get('message')}")


def cmd_test_skill_reuse(args):
    """test-skill-reuse 命令"""
    import json
    import re
    from datetime import datetime

    skill_id = args.skill_id
    brief = args.brief

    # 1. 检查 skill 是否在 published 目录下
    skill_dir = Config.PUBLISHED_DIR / skill_id
    if not skill_dir.exists():
        print(f"❌ Skill 不存在: {skill_id}")
        print(f"   路径: {skill_dir}")
        return

    # 2. 检查 skill.json 是否存在且 callable 为 true
    skill_json_path = skill_dir / "skill.json"
    if not skill_json_path.exists():
        print(f"❌ skill.json 不存在: {skill_id}")
        return

    try:
        skill_data = json.loads(skill_json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"❌ skill.json 解析失败: {e}")
        return

    if not skill_data.get("callable", False):
        print(f"❌ Skill 不可调用: {skill_id} (callable=false)")
        return

    # 3. 读取 SKILL.md
    skill_md_path = skill_dir / "SKILL.md"
    skill_md_content = ""
    if skill_md_path.exists():
        skill_md_content = skill_md_path.read_text(encoding="utf-8")

    # 4. 读取 examples.md
    examples_md_path = skill_dir / "examples.md"
    examples_content = ""
    if examples_md_path.exists():
        examples_content = examples_md_path.read_text(encoding="utf-8")

    # 5. 获取 quality_level 和 source 信息
    quality_level = skill_data.get("quality_level", "unknown")
    source_cases = skill_data.get("source_cases", [])
    source_strategies = skill_data.get("source_strategies", [])
    display_name = skill_data.get("display_name", skill_id)

    # 6. 分析相关性并生成 verdict
    brief_lower = brief.lower()
    skill_id_lower = skill_id.lower()
    display_name_lower = display_name.lower()
    skill_md_lower = skill_md_content.lower()
    examples_lower = examples_content.lower()

    # 关键词匹配
    keywords_brief = set(re.findall(r'[\w]+', brief_lower))
    keywords_skill_id = set(re.findall(r'[\w]+', skill_id_lower))
    keywords_display_name = set(re.findall(r'[\w]+', display_name_lower))

    # 计算重叠度
    overlap_id = len(keywords_brief & keywords_skill_id)
    overlap_display = len(keywords_brief & keywords_display_name)
    overlap_content = sum(1 for kw in keywords_brief if kw in skill_md_lower or kw in examples_lower)

    # 语义相关性检测
    brief_has_luxury = any(kw in brief_lower for kw in ["奢华", "豪华", "奢侈", "高端", "贵宾", "会员", "luxury"])
    brief_has_festival = any(kw in brief_lower for kw in ["春节", "新年", "节庆", "festival", "holiday", "celebration"])
    brief_has_hotel = any(kw in brief_lower for kw in ["酒店", "hotel"])

    skill_has_luxury = "luxury" in skill_id_lower or "奢华" in skill_md_content
    skill_has_festival = "festival" in skill_id_lower or "节庆" in skill_md_content or "春节" in skill_md_content
    skill_has_hotel = "hotel" in skill_id_lower or "酒店" in skill_md_content

    # 计算相关性得分
    relevance_score = 0
    if overlap_id > 0:
        relevance_score += overlap_id * 2
    if overlap_display > 0:
        relevance_score += overlap_display * 1.5
    if overlap_content > 2:
        relevance_score += min(overlap_content, 10)

    if brief_has_luxury and skill_has_luxury:
        relevance_score += 5
    if brief_has_festival and skill_has_festival:
        relevance_score += 5
    if brief_has_hotel and skill_has_hotel:
        relevance_score += 5

    # 高端酒店节庆场景强相关
    if (brief_has_luxury or brief_has_hotel) and skill_has_luxury and skill_has_festival:
        relevance_score += 10

    # 判断 verdict
    if relevance_score >= 15:
        verdict = "pass"
    elif relevance_score >= 5:
        verdict = "weak"
    else:
        verdict = "fail"

    # 7. 生成 reuse hypothesis
    reuse_hypothesis_parts = []
    if brief_has_luxury and skill_has_luxury:
        reuse_hypothesis_parts.append("brief 中的'奢华'关键词与 skill 的 luxury 属性匹配")
    if brief_has_festival and skill_has_festival:
        reuse_hypothesis_parts.append("brief 涉及节庆场景，与 skill 的 festival 内容相关")
    if brief_has_hotel and skill_has_hotel:
        reuse_hypothesis_parts.append("brief 涉及酒店场景，与 skill 的 hotel 属性匹配")
    if overlap_id > 0:
        reuse_hypothesis_parts.append(f"skill_id 关键词重叠: {overlap_id} 个")
    if overlap_content > 2:
        reuse_hypothesis_parts.append(f"内容关键词匹配: {overlap_content} 个")

    if not reuse_hypothesis_parts:
        reuse_hypothesis_parts.append("相关性较弱，需要人工审核")

    reuse_hypothesis = "；".join(reuse_hypothesis_parts)

    # 8. 生成 outline（模板生成）
    outline_sections = [
        ("方案定位", f"基于 {display_name} 的核心定位策略，围绕品牌差异化价值构建"),
        ("目标人群", "高净值家庭/企业主/金融从业者等高端客群"),
        ("核心策略", "节庆仪式感 + 品牌温度融合，强化会员价值感知"),
        ("视觉方向", "简约留白、品牌色系为主、强调高端质感"),
        ("执行路径", "预热期 → 引爆期 → 收尾期三阶段推进"),
        ("风险提示", "高端客群需求多变，需持续跟踪用户反馈"),
    ]

    # 9. 生成 reuse evaluation
    eval_items = [
        ("结构迁移性", "高" if relevance_score >= 10 else "中" if relevance_score >= 5 else "低"),
        ("视觉迁移性", "高" if skill_has_luxury else "中" if skill_has_hotel else "低"),
        ("策略迁移性", "高" if (skill_has_luxury and skill_has_festival) else "中"),
        ("证据充分性", "高" if quality_level in ["gold", "silver"] else "中"),
        ("风险等级", "低" if verdict == "pass" else "中" if verdict == "weak" else "高"),
    ]

    # 10. 生成 markdown 输出
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Config.OUTPUTS_DIR / "reuse_tests"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_filename = f"{skill_id}_{timestamp}.md"
    output_path = output_dir / output_filename

    output_lines = [
        "# Skill Reuse Test",
        "",
        "## Input Brief",
        brief,
        "",
        "## Skill Used",
        skill_id,
        quality_level,
        f"source_cases: {', '.join(source_cases)}",
        f"source_strategies: {len(source_strategies)} 个",
        "",
        "## Reuse Hypothesis",
        reuse_hypothesis,
        "",
        "## Generated Outline",
    ]

    for title, content in outline_sections:
        output_lines.append(f"- **{title}**: {content}")

    output_lines.append("")
    output_lines.append("## Reuse Evaluation")

    for name, value in eval_items:
        output_lines.append(f"- **{name}**: {value}")

    output_lines.append("")
    output_lines.append("## Verdict")
    output_lines.append(verdict.upper())

    output_path.write_text("\n".join(output_lines), encoding="utf-8")

    print(f"✅ 测试完成")
    print(f"   skill_id: {skill_id}")
    print(f"   quality_level: {quality_level}")
    print(f"   relevance_score: {relevance_score}")
    print(f"   verdict: {verdict}")
    print(f"   输出文件: {output_path}")