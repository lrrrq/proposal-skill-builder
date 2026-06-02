# Current State

> 状态: 当前阶段记录
> 更新时间: 2026-06-02

## 1. 当前阶段

当前阶段为 `Runtime Validation Preparation`。

本阶段目标是从离线 skill builder 进入 runtime validation。优先补齐协议、metadata、schema、router selection、context assembly 和 checker 校准。

## 2. 已有基础

- 已有 source proposal 摄入目录。
- 已有 compiled cases 中间产物。
- 已有 draft / published skill 目录。
- 已有 registry 只读发布习惯。
- 已有 `router_v2` 最小闭环。
- 已有 quality / human review / OpenClaw integration 占位文档。
- 已验证过领导人直播参考案到美的集团访谈直播的迁移路径。

## 3. 本轮新增协议

- `docs/PROJECT_HANDOFF.md`
- `docs/RUNTIME_PROTOCOL.md`
- `docs/SKILL_SCHEMA.md`
- `docs/PATTERN_SCHEMA.md`
- `docs/VALIDATION_PROTOCOL.md`
- `docs/CURRENT_STATE.md`

## 4. 冻结范围

当前不扩展:

- Web 服务。
- 前端界面。
- 多 Agent 编排。
- 完整 PPT 自动化。
- 新数据库。
- 在线问答系统。
- OpenClaw 自由调度能力。

当前不应优先做:

- 继续堆更多案例 pipeline。
- 大规模重构现有 compiler。
- 将 router_v2 直接扩成完整方案输出器。
- 让 execution skill 覆盖品牌、策略和结构判断。

## 5. 下一步任务

1. 给现有 Skill 增加向后兼容 metadata 字段。
2. 将现有 Pattern 转换或补强为 `docs/PATTERN_SCHEMA.md` 的字段。
3. 修改 `router_v2`，让它输出 Skill Selection 结果和排除原因。
4. 设计 Context Assembler 的最小输入输出。
5. 选 10 个旧案例建立 gold sample。
6. 用 gold sample 校准 Checker。

## 6. 交接说明

新执行者接手时，不要从对话历史推断项目方向。先读:

1. `CLAUDE.md`
2. `docs/PROJECT_HANDOFF.md`
3. `docs/CURRENT_STATE.md`
4. `docs/RUNTIME_PROTOCOL.md`
5. `docs/SKILL_SCHEMA.md`
6. `docs/PATTERN_SCHEMA.md`
7. `docs/VALIDATION_PROTOCOL.md`

如果对话要求与上述文档冲突，除非用户明确更新规则，否则以仓库文档为准。

