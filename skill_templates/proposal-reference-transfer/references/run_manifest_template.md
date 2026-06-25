# RUN_MANIFEST 模板（v0.2 必出文档）

> **来源**：`reports/huayuquan-doc-2026-07/skill-v0.2-changelog-confirmed.md §4 经验 6+7`
> **适用**：每次按本 skill 跑出 PPT 后，必须产出此文档

---

# RUN_MANIFEST — <Brief 标题>

> **项目**: <客户名><品牌 / 产品名><项目类型>
> **skill**: proposal-reference-transfer v<版本号>
> **生成时间**: YYYY-MM-DD
> **session_id**: mvs_<id>
> **agent**: <agent 名>

---

## 1. 工作流阶段时间线

| 时间 | 阶段 | 产物 | 文件 |
|------|------|------|------|
| HH:MM | **Brief 接收** | <brief 内容> | (input) |
| HH:MM | **v1 proposal 落地** | 4 段式正文 + PPT 结构 + 完整方案 | `proposal.md` |
| HH:MM | **v1 deck 渲染** | <页数>页 PPT，<占位策略> | `deck.pptx` |
| HH:MM | **AI 生图** | <N>张真图，<耗时>s | `deck_assets/` |
| HH:MM | **v2 用户微调** | <用户反馈> | (WPS / Keynote) |
| HH:MM | **打包** | <产物 zip> | `<name>-bundle.zip` |

---

## 2. 关键对话决策点

### Stage 1 — 需求接收

**用户**: "<原始 brief>"

### Stage 2 — 第一版 proposal

**用户**: "<反馈>"
**关键决策**: <skill 决策点 + 替代方案>

### Stage N — <阶段名>

**用户**: "<反馈>"
**关键决策**: <决策>

---

## 3. 使用的资源（pack + references）

### Brand-style-pack

- `brand-style-pack/<company>/<filename>` — <说明>

### References

- `references/<filename>` — <说明>

### Evals

- `evals/<filename>` — <失败模式 / 自检项>

### 一手素材

- <客户原始素材来源>

### AI 生图

- 端点: `<api endpoint>`
- 模型: `<model>`
- aspect_ratio: `<ratio>`
- API key 来源: `<env var>` ⚠️ 不要在代码里硬编码

---

## 4. 技术栈

| 层 | 技术 | 原因 |
|---|---|---|
| 提案生成 | <技术> | <原因> |
| PPT 渲染 | <技术> | <原因> |
| AI 生图 | <技术> | <原因> |
| 占位图（兜底）| <技术> | <原因> |
| 参考片海报 | <技术> | <原因> |

---

## 5. 文件清单（本 bundle 包含）

```
<name>-bundle.zip
├── README.md                         ← 本文件
├── proposal.md                       ← 提案正文（v<版本>）
├── deck.pptx                         ← PPT 最终版（v<版本>，<页数>页，<大小>）
├── gen_deck.py                       ← PPT 渲染脚本
├── gen_assets.py                     ← 占位图脚本（兜底）
├── gen_ai_images.py                  ← AI 生图脚本
└── deck_assets/                      ← <N>张 16:9 占位图
    ├── <slide>_<n>.png               ← <说明>[AI/PIL]
    └── references_raw/               ← <N>张原始素材
```

---

## 6. 后续建议

### 给 client 的下一步

1. <下一步>
2. <下一步>

### 给 skill 的改进（v<next>）

- <改进方向 1>
- <改进方向 2>

---

## 7. 安全注意

⚠️ **本次 workflow 触发的安全问题**：<如有>

- 影响范围: <代码 / 配置文件>
- 缓解: <改进方案>
- 已写入 agent memory: `<路径>`

---

## 8. mavis session 持久化

- 当前 session_id: `mvs_<id>`
- 当前 session <持久化状态>: `<~/.mavis/agents/<agent>/sessions/<sess_id>/>`
- 持久化触发: <条件>
- 替代记录: 本 RUN_MANIFEST.md + daemon log