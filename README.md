# Proposal Skill Builder

> 离线编译历史策划案例 → Skill Registry

把历史提案 PDF / PPT / DOC / MD 编译成结构化 Skill 资产，
供下游 agent（如 OpenClaw）按 brief 调用。本仓库是**离线 CLI**——
纯 Python 标准库 + SQLite，无 Web、无 DB 服务、无外部 API 强依赖。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org)
[![Platforms](https://img.shields.io/badge/platforms-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey)](https://github.com/)

---

## 为什么做这个

策划公司积累了上千份历史提案，但这些 PDF / PPT 不能被 agent 直接消费。
本项目把它们离线编译成可重用的 Skill Registry：

| 阶段 | 产物 | 用途 |
|---|---|---|
| Intake | `source_proposals/accepted/` + `source_files` row | 文件摄入 + SHA256 去重 |
| Compile-case | `compiled/cases/<id>/fragments.json` | 文本分段、提取 |
| Extract-patterns | `compiled/cases/<id>/patterns.json` | 模式识别 |
| Build-strategies | `compiled/cases/<id>/strategy_dna.md` | 策略 DNA |
| Compose-skill | `skills/draft/<skill_id>/` | 草稿 Skill |
| Publish-skill | `skills/published/<skill_id>/` + `registry/skill_registry.json` | 正式上线 |

下游 agent（如 OpenClaw）只读 `skills/published/` 和 `registry/`。

## 安装

需要 **Python 3.9+**，**纯标准库**，不需要任何 pip 依赖。

```bash
git clone https://github.com/lrrrq/proposal-skill-builder.git
cd proposal-skill-builder

# 可选：editable install
pip install -e .
```

## 快速上手

```bash
# 1. 初始化（创建目录 + SQLite db）
python -m skill_builder.cli init

# 2. 把策划案放到 staging/，然后摄入
python -m skill_builder.cli intake
#   → accepted/ duplicates/ rejected/ 三个目录

# 3. 从 accepted 文件创建 case
python -m skill_builder.cli create-case --file-id <id> --title "..."

# 4. 编译 case（提取 fragments）
python -m skill_builder.cli compile-case case_0001

# 5. 提取 patterns / strategies / skill（按需）
python -m skill_builder.cli extract-patterns case_0001
python -m skill_builder.cli build-strategies case_0001
python -m skill_builder.cli compose-skill case_0001 --skill-id my-skill

# 6. 发布到 registry
python -m skill_builder.cli publish-skill my-skill
```

## CLI 命令一览

| 命令 | 作用 |
|---|---|
| `init` | 初始化项目目录和 SQLite |
| `status` | 显示项目状态 |
| `intake` | 摄入 `staging/` 下的文件 |
| `list-files` | 列出所有 source file |
| `list-cases` | 列出所有 case |
| `create-case --file-id <id> --title <t>` | 创建 case |
| `compile-case <case_id>` | 编译 case 到 fragments.json |
| `extract-patterns <case_id>` | 提取 patterns |
| `describe-assets <case_id>` | 视觉资产描述（需 AI provider） |
| `build-strategies <case_id>` | 构建 StrategyUnit + strategy_dna |
| `compose-skill <case_id> --skill-id <id>` | 合成 draft Skill |
| `check-skill <skill_id>` | 检查 draft Skill 质量 |
| `compress-fragments <case_id>` | 压缩碎片（Phase 3.5） |
| `publish-skill <skill_id>` | 发布到 registry（Phase 5） |
| `inspect-registry` | 检查 registry 健康度 |
| `repair-registry` | 修复 registry drift |
| **`inspect-source-drift`** | **检查 source_files 与 fs 的 drift** |
| **`repair-source-drift [--apply]`** | **修复 drift（默认 dry-run）** |
| `case-readiness <case_id>` | 检查 case 是否适合进 Skill 生成 |
| `analyze-project <case_id>` | 项目级分析 |
| `test-skill-reuse <skill_id> --brief <b>` | 测试 Skill 对新 brief 的可用性 |
| `batch-compile` | 批量编译 |
| `batch-validation` | 批量验证所有 case |
| `check-ai-provider --provider <p>` | 校验 AI provider 配置 |

## 跨平台支持

- **macOS / Linux / Windows** 全平台支持（CI matrix 已配）
- 路径用 `pathlib.Path`，自动适配 `/` vs `\`
- subprocess 用 `sys.executable` 找 Python，Windows 上不会因缺 `python3` 报 NotFound
- 文件 IO 全部 `encoding="utf-8"`，避开 Windows GBK 默认编码陷阱
- LibreOffice 路径支持 macOS / Linux / Windows 默认安装位置
- 临时目录用 `tempfile.mkdtemp()`，避开 `/tmp` 在 Windows 上不存在的问题

## 运行测试

```bash
# 本地：跨平台 smoke test
python tests/test_cross_platform.py

# 详细模式
python tests/test_cross_platform.py -v

# 或用 pytest
python -m pytest tests/ -v
```

## 项目结构

```
proposal-skill-builder/
├── skill_builder/         # 核心 CLI 模块
│   ├── cli.py             # argparse 入口
│   ├── commands.py        # 命令实现
│   ├── config.py          # 路径配置（基于 __file__，跨平台）
│   ├── db.py              # SQLite 管理
│   ├── drift_check.py     # source_files drift 检测/修复
│   ├── intake.py          # 文件摄入
│   ├── case_manager.py    # case CRUD
│   ├── compiler.py        # 案例编译
│   ├── parser.py          # 多格式解析
│   ├── extractor.py       # Fragment 提取
│   ├── office_converter.py# PPTX → PDF (LibreOffice, 跨平台路径)
│   └── ...                # 其余模块
├── source_proposals/      # 源文件工作流
│   ├── staging/           # 待摄入
│   ├── accepted/          # 已摄入
│   ├── duplicates/        # 重复
│   └── rejected/          # 不支持
├── compiled/              # 编译产出
│   └── cases/             # case_xxxx/
├── skills/                # Skill 仓库
│   ├── draft/             # 草稿（不进入正式 registry）
│   ├── published/         # 已发布
│   └── quarantine/        # 隔离
├── registry/              # Skill registry（只读快照）
├── tests/                 # 跨平台 smoke test
│   └── test_cross_platform.py
├── data/                  # SQLite db
├── reports/               # 运行报告
├── docs/                  # 文档
└── .github/workflows/     # CI matrix
    └── test.yml
```

## 状态机

```
staging ──intake──> accepted ──create-case──> cases.draft ──compile-case──> cases.compiled
                                            └─────────────────> cases.failed
duplicates                                              ▲
rejected                                                │
```

`status` 字段在 `cases` 表里维护。`compile-case` 跑成功 = `compiled`，
失败 = `failed` 并把 `error_message` 写入。

## Drift 检测

本项目是离线 CLI，所有状态靠 SQLite + filesystem 双写。
一旦 `accepted/` 目录被 git/迁移/误删，db 和 fs 就会不一致。
新增两个命令处理这种情况：

```bash
# 1. 先看 drift 范围（只读）
python -m skill_builder.cli inspect-source-drift

# 2. 确认后打标记（默认 dry-run，加 --apply 才落库）
python -m skill_builder.cli repair-source-drift --apply
```

被打标记的 row 在 `source_files.error_message` 里写明原因，
后续可以选：重新 intake / mark-case-dataset 挪到 test 数据集 / 接受永久丢失。

## 路线图

- ✅ Phase 1: Foundation CLI（intake + compile-case）
- ✅ Phase 2: Vision Layer（describe-assets + ai_fragments）
- ✅ Phase 3: Strategy Layer（build-strategies + StrategyUnit）
- 🔄 Phase 3.5: Knowledge Quality Consolidation（Fragment Compression）
- ✅ Phase 4: Skill Asset Hardening（**cross-platform**）
- ⏳ Phase 5: Publish + Registry（publish-skill, route）
- ⏳ Phase 6: OpenClaw Integration Support（只读协议，不做在线接入）

## 许可

MIT License — 见 [LICENSE](LICENSE)。

## 贡献

欢迎 PR。改动前请：

1. 跑 `python tests/test_cross_platform.py` 全过
2. 新功能必须附 smoke test
3. 不要引入标准库之外的依赖（项目约束）