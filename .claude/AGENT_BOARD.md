# Agent Board - Proposal Skill Builder

## Agent 角色定义

| Agent | 类型 | 职责 | 权限 |
|-------|------|------|------|
| Orchestrator | general-purpose | 协调者：分配任务、监督进度、控制流程 | 只读，可以分配任务 |
| Implementer | general-purpose | 实现者：执行编码、文件修改 | 可修改代码文件 |
| Reviewer | general-purpose | 审查者：代码审查、安全检查 | 只读，输出意见 |
| QA | general-purpose | 验证者：运行测试、执行命令验证 | 只读，执行验证命令 |
| Governor | general-purpose | 治理者：检查禁止项、合规性 | 只读，有一票否决权 |
| VersionManager | general-purpose | 版本管理者：git 状态检查、commit 建议 | 只读，不允许自动 commit |

## 当前 Sprint 可用 Agent

### 1. Orchestrator (本会话)
- 分配任务
- 协调执行顺序
- 生成最终简报

### 2. Implementer (根据需要)
- 执行代码修改
- 创建新文件
- 修改现有文件

### 3. Reviewer
- 代码审查
- 安全检查
- 只输出意见，不直接改代码

### 4. QA
- 运行 CLI 命令验证
- 执行测试
- 输出验证结果

### 5. Governor
- 检查禁止项
- 合规性验证
- 有一票否决权

### 6. VersionManager
- git status 检查
- 生成 commit 建议
- 不允许自动 commit

## 任务分配规则

1. **同一文件同一时间只允许一个 Agent 修改**
2. **审查 Agent 只输出意见，不改代码**
3. **治理 Agent 发现禁止项立即停止**
4. **版本管理 Agent 只能建议，不能执行**

## 当前阶段

Phase 3: Strategy Layer Enhancement

## 当前 Sprint

目标：Phase 3 收口检查 + 稳定性修复 + 版本整理
