# Proposal Skill Builder

历史策划案例离线编译成 Skill Registry

## 安装

```bash
pip install -e .
```

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