# Merge Policy - Proposal Skill Builder

## 基本规则

1. **不允许自动 commit**
2. **不允许自动 merge**
3. **所有 merge 必须经过人工确认**

## Commit 规则

### 必须人工确认的情况
- 首次提交新仓库
- 合并分支
- 删除文件
- 修改已有功能
- 引入新依赖
- Phase 收口提交

### 可以直接提交的情况
- 文档更新（CLAUDE.md 等）
- 测试产物清理
- 临时文件删除
- Sprint 简报更新

### 禁止项
- ❌ 禁止自动 commit（包括 Phase 收口）
- ❌ 禁止自动 merge
- ❌ 禁止在未人工确认前 push

## 文件分类

### 必须人工确认才能提交
| 类型 | 示例 |
|------|------|
| 核心代码 | cli.py, commands.py, *.py |
| 数据结构 | schemas.py, models.py |
| 新依赖 | pyproject.toml |
| 删除文件 | 任何删除操作 |

### 可以直接提交
| 类型 | 示例 |
|------|------|
| 文档 | CLAUDE.md, README.md, .claude/*.md |
| 测试报告 | reports/*.md |
| 编译产物 | compiled/, skills/draft/ |
| 配置文件 | .gitignore |
| Sprint 简报 | .claude/runs/current/*.md |

## 提交前检查清单

- [ ] 无禁止项触碰
- [ ] 无新依赖引入（除非说明用途）
- [ ] 测试通过（验证命令运行正常）
- [ ] 文档已更新（如果需要）
- [ ] Sprint 简报已生成（如果是 Phase 收口）

## Commit Message 格式

```
<type>: <简短描述>

<详细说明（如果需要）>

<关联的 Phase 或 Issue>
```

### Type 分类
- `fix:` - 缺陷修复
- `feat:` - 新功能
- `docs:` - 文档更新
- `refactor:` - 重构
- `chore:` - 杂项

## 当前状态

- 未提交改动：待清理
- 当前阶段：Phase 3.5 Knowledge Quality Consolidation
- 下一任务：Fragment Compression 验证与收口

## Sprint 流程

1. 创建 `.claude/runs/current/task_card.md`
2. 按任务卡执行
3. 生成 `.claude/runs/current/sprint_report_*.md`
4. 人工确认后执行 commit