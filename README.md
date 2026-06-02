# Proposal Skill Builder

历史策划案例离线编译成 Skill Registry

## 跨平台接手入口

本项目规则文档已升级为跨平台交接协议。无论你使用 Claude、Codex、ChatGPT 还是其他执行平台，开始工作前必须先读：

1. `CLAUDE.md` — 工程规则、禁止事项、当前阶段
2. `docs/PROJECT_HANDOFF.md` — 项目目标、系统边界、模块职责
3. `docs/CURRENT_STATE.md` — 当前阶段、冻结范围、下一步任务
4. `docs/SKILL_SCHEMA.md` — Skill Metadata 字段、五类 Skill 职责边界
5. `docs/PATTERN_SCHEMA.md` — Pattern 字段、触发/禁用条件、质量标准

如果对话上下文与仓库文档冲突，以仓库文档为准。

## 安装

```bash
pip install -e .
```

## 本地环境

```bash
cp .env.example .env
```

`.env` 只放本机密钥，不要提交到 Git。协作前后用 `git status --short --branch` 确认工作区状态；提交前用 `git diff --check` 检查换行和尾随空白。

## CLI 命令

### init - 初始化项目
```bash
python -m skill_builder.cli init
```

### status - 查看状态
```bash
python -m skill_builder.cli status
```

## 目录结构

```
proposal-skill-builder/
├── skill_builder/       # 核心代码
├── source_proposals/   # 策划案源文件
│   ├── staging/         # 待处理
│   ├── accepted/       # 已接受
│   ├── duplicates/     # 重复
│   └── rejected/       # 拒绝
├── data/               # 数据库
├── compiled/           # 编译结果
├── knowledge/          # 知识库
│   └── case_cards/     # 案例卡片
├── skills/             # Skill 仓库
│   ├── draft/          # 草稿
│   ├── published/      # 已发布
│   └── quarantine/     # 隔离
├── registry/           # 注册表
├── outputs/            # 输出
└── reports/            # 报告
```
