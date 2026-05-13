# Proposal Skill Builder - 工程规则

## 项目背景

本项目将历史策划案例离线编译成可复用 Skill Registry，供 OpenClaw 或在线生成入口只读调用。

## 核心约束

### 架构顺序
1. **本地 CLI 优先**：先做本地 CLI 闭环，再考虑钉钉或 Web 服务
2. **测试链路优先**：先支持 `md/txt` 测试链路，再支持 `pptx/pdf/docx`
3. **SQLite 状态库**：所有状态通过 SQLite 管理，不引入额外数据库
4. **只读发布**：OpenClaw 只读取 `skills/published` 和 `registry`，不修改源案例

### 技术约束
- **禁止引入无必要依赖**：只用 Python 标准库 + argparse
- **禁止重构无关文件**：每次修改只涉及目标文件，不做全局重构
- **幂等性**：CLI 命令重复执行不能破坏已有数据
- **一致性**：数据库和文件系统操作必须保证原子性

### 开发节奏
- **小步迭代**：不允许一次性搭完整平台
- **可验证**：每一步功能必须有可运行验证命令
- **人工确认**：敏感操作（删除、覆盖）必须输出明确提示

## 项目结构

```
proposal-skill-builder/
├── skill_builder/        # 核心代码（纯 Python）
│   ├── cli.py          # CLI 入口
│   ├── commands.py     # 命令实现
│   ├── config.py       # 路径配置
│   ├── db.py           # SQLite 管理
│   ├── case_manager.py # 案例管理
│   ├── compiler.py      # 案例编译
│   ├── parser.py       # 文件解析
│   ├── extractor.py    # Fragment 提取
│   └── ...
├── source_proposals/   # 源文件工作流
│   ├── staging/        # 待摄入
│   ├── accepted/       # 已摄入
│   ├── duplicates/     # 重复
│   └── rejected/       # 不支持
├── compiled/           # 编译产出
│   └── cases/         # case_xxxx/
├── skills/             # Skill 仓库
│   ├── draft/         # 草稿
│   ├── published/      # 已发布
│   └── quarantine/     # 隔离
└── registry/           # 注册表（只读快照）
```

## CLI 命令约定

### 必须的验证命令
```bash
python -m skill_builder.cli init        # 初始化
python -m skill_builder.cli status      # 查看状态
python -m skill_builder.cli list-files  # 列出文件
python -m skill_builder.cli list-cases  # 列出案例
```

### 开发新命令流程
1. 在 `cli.py` 注册 subparser
2. 在 `commands.py` 实现 handler
3. 在对应模块实现业务逻辑
4. 提供验证命令

### 命令幂等性要求
- `intake`：重复运行不会重复摄入相同 SHA256 文件
- `create-case`：重复绑定同一文件返回已有 case_id
- `compile-case`：已 compiled 的 case 可重新编译覆盖

## 数据一致性规则

### 数据库操作
- 开启事务 → 执行操作 → commit
- 失败时 rollback + 清理文件系统残留
- 禁止在事务外修改数据库

### 文件系统操作
- 先写 `.tmp` 文件
- 数据库成功后 `os.replace()` 原子替换
- 失败时清理 `.tmp`

### 迁移规则
- `init_db()` 创建表后必须调用 `run_migrations()`
- `ensure_column()` 使用白名单校验表名
- 创建索引必须处理 `IntegrityError`

## 代码风格

### 错误处理
- 失败返回 dict: `{"success": False, "message": "...", "detail": "..."}`
- 成功返回 dict: `{"success": True, "case_id": "...", ...}`
- 禁止抛出未捕获的异常中断 CLI

### 日志与输出
- CLI 输出使用 `print()`，格式固定
- 成功: `✅ 消息`
- 警告: `⚠️ 消息`
- 失败: `❌ 消息`

### 模块依赖
```
cli.py → commands.py → [db.py, config.py, utils.py]
                     → [case_manager.py, compiler.py, parser.py, extractor.py]
```

## 下一步开发优先级

1. **Pattern 提取**：从 `fragments.json` 提取可复用 Pattern
2. **Skill 组装**：多个 Pattern + Strategy DNA → Skill
3. **Skill 发布**：从 `draft` 移动到 `published`
4. **Registry 更新**：注册新 Skill 到 `skill_registry.json`

## 禁止事项

- ❌ 不允许引入 `pandas`、`numpy` 等非必要依赖
- ❌ 不允许修改 `/Applications/lrq/coding/text-agent/` 下的旧项目
- ❌ 不允许在 CLI 中直接 `print(source_file.content)`
- ❌ 不允许跳过 `init_db()` 直接操作数据库
- ❌ 不允许一次性开发完整解析链路（先跑通 md/txt）
