# Runtime Protocol

> 状态: Runtime 链路协议
> 更新时间: 2026-06-02

## 1. 运行目标

Runtime 层负责把用户 brief 转化为 OpenClaw 可执行的成品上下文。它不重新编译旧案例，不扩展知识库，不让 Writer 自行决定调用什么。

标准链路:

```text
用户 brief
-> Runtime Router
-> Skill Selection
-> Context Assembler
-> OpenClaw Writer
-> Runtime Checker
-> revision instructions
```

## 2. Runtime Router

Router 的输入是用户 brief 和只读 registry。Router 不生成最终方案，只生成路由结果。

Router 必须判断:

- 项目类型: TVC、短视频矩阵、品牌片、年会、发布会、访谈直播、活动方案等。
- 品牌对象: 品牌名称、已有品牌人格、行业和调性。
- 商业目标: 引流、预约、招商、品牌升级、节日营销、招聘、内部传播等。
- 目标人群: 用户、经销商、内部员工、媒体、行业伙伴、消费者家庭等。
- 输出形态: MD、PPT 结构、PDF 策划案、脚本矩阵、执行方案等。
- 风险点: 品牌误判、行业错配、策略不适配、禁忌冲突、上下文不足。

Router 输出字段:

```yaml
brief_profile:
selected_skills:
selected_patterns:
excluded_skills:
context_budget:
assembly_order:
risk_flags:
next_action:
```

## 3. Skill Selection

Router 默认选择 3 到 5 个 Skill。数量不足时可以降级到 1 到 2 个，但必须写明原因。数量过多时应优先保留角色互补的 Skill。

优先级:

1. 精准品牌人格 Skill。
2. 同项目类型策略方法 Skill。
3. 同输出形态结构 Skill。
4. 同语言风格或乙方提案调性 Skill。
5. 执行输出 Skill。

排除规则:

- `not_applicable_when` 命中时必须排除。
- `conflict_with` 命中时必须排除或降权。
- 品牌调性明显冲突时必须排除。
- 只提供文案总结、没有触发条件和禁忌边界的 Skill 不能作为主 Skill。

## 4. Context Assembler

Assembler 只消费 Router 结果和被选 Skill/Pattern，不重新发明策略。

Assembler 输出 OpenClaw prompt 包，包含:

- brief profile。
- 品牌人格约束。
- 策略 pattern。
- 输出结构。
- 语言风格规则。
- 视觉/版式规则。
- 禁忌边界。
- 成品验收标准。
- 引用来源摘要。

Assembler 必须控制上下文体积。默认策略是少量高置信内容优先，不把所有来源全文塞给 Writer。

## 5. OpenClaw Writer

OpenClaw 只承担 Writer/Executor。

Writer 可以做:

- 根据 Assembler 输入生成方案、脚本、PPT 页序、PDF 文案。
- 在不违反上游约束的前提下补充自然语言表达。
- 将抽象策略转成可读、可交付文本。

Writer 不允许做:

- 自行重选 Skill。
- 自行扩大参考案例范围。
- 自行覆盖品牌人格。
- 自行改变输出结构的核心页序。
- 忽略禁忌边界。
- 将 Checker 失败项解释为“风格选择”。

## 6. Runtime Checker

Checker 接收 brief、Router 结果、Assembler 输入和 Writer 输出。Checker 不负责重写全文，只输出 verdict 和 revision instructions。

Checker 输出字段见 `docs/VALIDATION_PROTOCOL.md`。

## 7. 失败处理

Router 失败:

- 返回缺失字段和建议人工补充项。
- 不进入 Writer。

Assembler 失败:

- 返回冲突 Skill、上下文超预算或缺失结构。
- 不进入 Writer。

Checker 失败:

- 返回具体修改指令。
- 由 Writer 进行定向修订。

