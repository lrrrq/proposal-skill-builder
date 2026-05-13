"""
CLI - 命令行入口
"""

import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        prog="skill_builder",
        description="历史策划案例离线编译成 Skill Registry"
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # init 命令
    subparsers.add_parser("init", help="初始化项目")

    # status 命令
    subparsers.add_parser("status", help="显示项目状态")

    # intake 命令
    intake_parser = subparsers.add_parser("intake", help="摄入 staging 目录下的文件")
    intake_parser.add_argument("--dataset", default="prod",
                             choices=["prod", "test"],
                             help="数据集（默认 prod）")

    # create-case 命令
    create_case_parser = subparsers.add_parser("create-case", help="创建案例")
    create_case_parser.add_argument("--file-id", required=True, help="文件 ID")
    create_case_parser.add_argument("--title", required=True, help="案例标题")

    # list-files 命令
    subparsers.add_parser("list-files", help="列出所有文件")

    # list-cases 命令
    list_cases_parser = subparsers.add_parser("list-cases", help="列出所有案例")
    list_cases_parser.add_argument("--dataset", default="all",
                                 choices=["all", "prod", "test"],
                                 help="数据集筛选（默认 all）")

    # compile-case 命令
    compile_case_parser = subparsers.add_parser("compile-case", help="编译案例")
    compile_case_parser.add_argument("case_id", help="Case ID (如 case_0001)")

    # extract-patterns 命令
    extract_patterns_parser = subparsers.add_parser("extract-patterns", help="提取 Patterns")
    extract_patterns_parser.add_argument("case_id", help="Case ID (如 case_0001)")

    # describe-assets 命令
    describe_parser = subparsers.add_parser("describe-assets", help="生成资产视觉描述")
    describe_parser.add_argument("case_id", help="Case ID (如 case_0001)")
    describe_parser.add_argument("--provider", default="mock",
                               choices=["mock", "minimax-mcp", "openai-compatible"],
                               help="AI Provider (默认 mock)")
    describe_parser.add_argument("--dry-run", action="store_true",
                               help="Dry-run 模式，不调用真实 API")
    describe_parser.add_argument("--limit", type=int, default=0,
                               help="最多处理 N 个资产（默认不限制）")
    describe_parser.add_argument("--asset-id", type=str, default=None,
                               help="只处理指定 asset_id")

    # check-ai-provider 命令
    check_parser = subparsers.add_parser("check-ai-provider", help="检查 AI Provider 配置")
    check_parser.add_argument("--provider", required=True,
                            choices=["minimax-text", "minimax-mcp", "openai-compatible"],
                            help="AI Provider")

    # batch-compile 命令
    batch_parser = subparsers.add_parser("batch-compile", help="批量编译案例")
    batch_parser.add_argument("--limit", type=int, default=5, help="最多处理数量（默认 5）")
    batch_parser.add_argument("--dataset", default="prod",
                           choices=["all", "prod", "test"],
                           help="数据集筛选（默认 prod）")

    # mark-case-dataset 命令
    mark_case_parser = subparsers.add_parser("mark-case-dataset", help="标记案例数据集")
    mark_case_parser.add_argument("case_id", help="Case ID")
    mark_case_parser.add_argument("--dataset", required=True,
                                 choices=["prod", "test"],
                                 help="目标数据集")

    # mark-file-dataset 命令
    mark_file_parser = subparsers.add_parser("mark-file-dataset", help="标记文件数据集")
    mark_file_parser.add_argument("file_id", help="File ID")
    mark_file_parser.add_argument("--dataset", required=True,
                                 choices=["prod", "test"],
                                 help="目标数据集")

    # build-ai-fragments 命令
    build_ai_parser = subparsers.add_parser("build-ai-fragments", help="从 descriptions.json 生成 ai_fragments.json")
    build_ai_parser.add_argument("case_id", help="Case ID (如 case_0001)")

    # compose-skill 命令
    compose_parser = subparsers.add_parser("compose-skill", help="合成 draft Skill")
    compose_parser.add_argument("case_id", help="Case ID (如 case_0001)")
    compose_parser.add_argument("--skill-id", required=True, help="Skill ID (如 luxury-hotel-festival)")

    # check-skill 命令
    check_parser = subparsers.add_parser("check-skill", help="检查 draft Skill 质量")
    check_parser.add_argument("skill_id", help="Skill ID (如 luxury-hotel-festival)")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)
    elif args.command == "init":
        from .commands import init
        init()
    elif args.command == "status":
        from .commands import status
        status()
    elif args.command == "intake":
        from .commands import intake
        intake(args)
    elif args.command == "create-case":
        from .commands import cmd_create_case
        cmd_create_case(args)
    elif args.command == "list-files":
        from .commands import cmd_list_files
        cmd_list_files(args)
    elif args.command == "list-cases":
        from .commands import cmd_list_cases
        cmd_list_cases(args)
    elif args.command == "compile-case":
        from .commands import cmd_compile_case
        cmd_compile_case(args)
    elif args.command == "extract-patterns":
        from .commands import cmd_extract_patterns
        cmd_extract_patterns(args)
    elif args.command == "describe-assets":
        from .commands import cmd_describe_assets
        cmd_describe_assets(args)
    elif args.command == "batch-compile":
        from .commands import cmd_batch_compile
        cmd_batch_compile(args)
    elif args.command == "mark-case-dataset":
        from .commands import cmd_mark_case_dataset
        cmd_mark_case_dataset(args)
    elif args.command == "mark-file-dataset":
        from .commands import cmd_mark_file_dataset
        cmd_mark_file_dataset(args)
    elif args.command == "check-ai-provider":
        from .commands import cmd_check_ai_provider
        cmd_check_ai_provider(args)
    elif args.command == "build-ai-fragments":
        from .commands import cmd_build_ai_fragments
        cmd_build_ai_fragments(args)
    elif args.command == "compose-skill":
        from .commands import cmd_compose_skill
        cmd_compose_skill(args)
    elif args.command == "check-skill":
        from .commands import cmd_check_skill
        cmd_check_skill(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
