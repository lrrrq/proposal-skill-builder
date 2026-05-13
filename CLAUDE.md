# Proposal Skill Builder - 工程规则

## 项目定位

**离线 Skill 资产编译器 + Registry 资产准备器**

本项目将历史策划案例离线编译成可复用 Skill Registry，供 OpenClaw 只读调用。OpenClaw 负责最终的 Brief 理解和方案输出，本项目不实现该功能。

## 核心约束

### 架构顺序
1. **本地 CLI 优先**：先做本地 CLI 闭环，再考虑外部接入
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
│   ├── draft/         # 草稿（不进入正式 registry）
│   ├── published/      # 已发布（正式上线）
│   └── quarantine/     # 隔离
├── docs/               # 集成文档（占位）
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

## 技能存储规则

| 目录 | 用途 | 说明 |
|------|------|------|
| `skills/draft/` | 草稿区 | compose-skill 生成，**不进入正式 registry** |
| `skills/published/` | 发布区 | 正式上线后才移动到这里 |
| `registry/skill_registry.json` | 正式注册表 | **只登记 skills/published** |
| `compiled/cases/` | 案例编译产出 | fragments/patterns/strategies 等 |

### Registry 规则
- **draft Skill**：`skills/draft/<skill_id>/` → **不进入正式 registry**
- **正式 Registry**：`registry/skill_registry.json` → **只在 publish-skill 后更新**
- **OpenClaw 只读**：只读取 `skills/published/` 和 `registry/`

## 开发阶段划分

| Phase | 内容 | 状态 | 禁止项 |
|-------|------|------|--------|
| Phase 1 | Foundation CLI（intake + compile-case）| ✅ 完成 | 无 |
| Phase 2 | Vision Layer（describe-assets + ai_fragments）| ✅ 完成 | 无 |
| Phase 3 | Strategy Layer（build-strategies + StrategyUnit）| ✅ 完成 | 无 |
| Phase 3.5 | Knowledge Quality Consolidation（Fragment Compression）| 🔄 当前 | 无 |
| Phase 4 | Skill Asset Hardening | ⏳ 待开始 | 无 |
| Phase 5 | Publish + Registry | ❌ 禁止当前实现 | publish-skill, route |
| Phase 6 | OpenClaw Integration Support | ❌ 禁止当前实现 | 在线接入 |

### Phase 3.5 当前任务
**Fragment Compression**：压缩短文本/重复/低信息 fragments，提升 Pattern 质量

### Phase 6 说明
OpenClaw Integration Support 只提供：
- Registry 只读访问协议
- Skill 文档说明
- 调用协议
- 示例 Brief
- 只读说明文档

**不实现**：在线接入、Web 服务、方案输出器

## 项目非目标（绝对禁止）

以下功能在任何阶段都不实现：

1. **❌ 不做前端**：无 Web 界面、无 React/Vue、无在线编辑器
2. **❌ 不做智能问答**：无聊天系统、无 RAG、无问答 API
3. **❌ 不做最终提案输出器**：方案生成由 OpenClaw 负责
4. **❌ 不做完整 SaaS**：纯离线 CLI + Registry 准备
5. **❌ 不做数据库**：禁止引入 SQLite 以外的数据库
6. **❌ 不做 Web 服务**：禁止 Flask/Django/FastAPI

## 依赖管理规则

### 允许的依赖

**核心框架**：Python 标准库 + argparse（CLI 入口）

**文档解析与视觉处理**（必要依赖）：
| 依赖 | 用途 | 阶段 |
|------|------|------|
| `pymupdf` | PDF 解析 | Phase 1 |
| `pillow` | 图片处理 | Phase 2 |
| `python-pptx` | PPTX 解析 | Phase 1 |
| `python-docx` | DOCX 解析 | Phase 1 |
| `openai` | AI API 调用 | Phase 2-3 |
| `requests` | HTTP 请求 | Phase 2-3 |

### 禁止的依赖

- ❌ 禁止引入 `pandas`、`numpy` 等数据分析库
- ❌ 禁止引入 Web 框架（Flask/Django/FastAPI 等）
- ❌ 禁止引入复杂任务队列（Celery 等）
- ❌ 禁止引入前端框架（React/Vue 等）
- ❌ 禁止引入非必要的机器学习库

### 新增依赖规则

新增依赖必须满足：
1. 说明用途
2. 标注所属 Phase
3. 说明替代方案（如无替代必须说明理由）
4. 提供验证命令

## 禁止事项

### 绝对禁止（任何阶段都不实现）

- ❌ 不允许实现前端界面
- ❌ 不允许实现智能问答或聊天系统
- ❌ 不允许实现方案输出器
- ❌ 不允许实现完整 SaaS
- ❌ 不允许引入禁止的依赖
- ❌ 不允许修改 `/Applications/lrq/coding/text-agent/` 下的旧项目
- ❌ 不允许在 CLI 中直接 `print(source_file.content)`
- ❌ 不允许跳过 `init_db()` 直接操作数据库
- ❌ 不允许一次性开发完整解析链路（先跑通 md/txt）

### 当前阶段禁止（Phase 5/6 才考虑）

- ❌ **publish-skill**：禁止当前实现，属于 Phase 5
- ❌ **route/路由系统**：禁止当前实现，属于 Phase 5
- ❌ **钉钉接入**：禁止当前实现，属于 Phase 6
- ❌ **OpenClaw 在线接入**：禁止当前实现，属于 Phase 6

### 当前阶段允许

- ✅ **compress-fragments**：Phase 3.5 当前任务
- ✅ **compose-skill**：生成 draft Skill
- ✅ **check-skill**：质量检查
- ✅ **build-strategies**：StrategyUnit 提取