# Proposal Skill Builder - Agent Rules

固定使用中文对话、反馈。

## Think Before Coding

- 不确定时先说清假设；有多种解释时不要静默选择。
- 如果更简单的路径存在，直接说明取舍。
- 遇到信息不足或矛盾时停下来说明，不要假装确定。

## Simplicity First

- 只写满足当前目标的最少代码。
- 不为单次使用新增抽象。
- 不添加未被要求的功能、配置项或兜底逻辑。

## Surgical Changes

- 只改和任务直接相关的文件。
- 不顺手重构、不格式化无关代码。
- 匹配现有项目风格。
- 清理自己引入的未使用代码，不清理既有无关死代码。

## Goal-Driven Execution

- 把任务转成可验证目标。
- Bug 修复优先写能复现问题的测试，再修到通过。
- 多步骤任务先给简短计划，并为每步说明验证方式。

## Repo Sync Policy

- 仓库只同步源码、测试、文档、模板和必要配置。
- 不同步 `.env`、`.claude/scheduled_tasks.json`、本地素材、生成 skill、编译产物、报告和 registry 快照。
- Windows/macOS 协作以 `.gitattributes` 为准处理换行；不要提交本机路径或本机运行状态。
