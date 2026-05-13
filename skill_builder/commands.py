"""
命令实现
"""

import argparse

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
        print(f"  - published Skills: {stats.get('published_skills', 0)}")
    else:
        print("  数据库: 不存在（需要运行 init）")
    print()

    print("[注册表]")
    reg_exists = Config.SKILL_REGISTRY_JSON.exists()
    if reg_exists:
        registry = get_registry()
        skills = registry.list_skills()
        print(f"  skill_registry.json: 存在 ({len(skills)} Skills)")
    else:
        print("  skill_registry.json: 不存在")
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