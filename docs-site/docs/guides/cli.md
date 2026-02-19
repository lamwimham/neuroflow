# NeuroFlow CLI 使用指南

NeuroFlow 命令行工具让你可以快速创建和管理 Agent、Skills 和 Tools。

## 安装

```bash
cd sdk
pip install -e .
```

## 快速开始

```bash
# 查看帮助
neuroflow --help

# 查看版本
neuroflow --version
```

## 命令总览

| 命令 | 说明 |
|------|------|
| `neuroflow init` | 创建新项目 |
| `neuroflow agent` | Agent 管理 |
| `neuroflow skill` | Skill 管理 |
| `neuroflow tool` | Tool 管理 |
| `neuroflow run` | 运行应用 |
| `neuroflow serve` | 启动服务器 |

---

## 项目管理

### 创建项目

```bash
# 创建新项目
neuroflow init my-project

# 使用完整模板
neuroflow init my-project --template full
```

---

## Agent 管理

### 创建 Agent

```bash
# 创建基本 Agent
neuroflow agent create assistant

# 指定描述和 LLM 提供商
neuroflow agent create analyst \
  --description="数据分析专家" \
  --llm-provider anthropic
```

### 列出 Agents

```bash
neuroflow agent list
```

### 运行 Agent

```bash
neuroflow agent run assistant "你好，请介绍一下自己"
```

---

## Skill 管理

Skills 是模块化的 Agent 能力包，将程序性知识封装成可复用的技能。

### 创建 Skill

```bash
# 基本用法
neuroflow skill create my-skill \
  --description="技能描述，包含触发词"

# 完整选项
neuroflow skill create data-analysis \
  --description="数据分析框架。触发词：数据分析、数据洞察、统计" \
  --category data-analysis \
  --template standard \
  --with-framework \
  --with-examples \
  --with-scripts \
  --assign-to assistant
```

### 选项说明

| 选项 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--description` | `-d` | 技能描述（必需） | - |
| `--category` | `-c` | 技能分类 | general |
| `--template` | `-t` | 模板类型 | standard |
| `--output-dir` | `-o` | 输出目录 | skills |
| `--with-framework` | - | 生成 FRAMEWORK.md | ❌ |
| `--with-examples` | - | 生成 EXAMPLES.md | ❌ |
| `--with-scripts` | - | 生成 scripts 目录 | ❌ |
| `--with-resources` | - | 生成 resources 目录 | ❌ |
| `--assign-to` | `-a` | 分配给 Agent | - |
| `--author` | - | 作者名 | Your Name |
| `--force` | `-f` | 覆盖已存在的 skill | ❌ |

### 模板类型

| 模板 | 说明 | SKILL.md 详细程度 | 适用场景 |
|------|------|------------------|----------|
| `minimal` | 最小模板 | ~20 行 | 简单技能 |
| `standard` | 标准模板 | ~80 行 | 大多数技能 |
| `advanced` | 高级模板 | ~200 行 | 复杂工作流 |

### 技能分类

- `data-analysis` - 数据分析
- `code-review` - 代码审查
- `documentation` - 文档生成
- `testing` - 测试
- `security` - 安全
- `performance` - 性能优化
- `general` - 通用

### 示例

#### 创建简单 Skill

```bash
neuroflow skill create greet \
  --description="问候技能。触发词：问候、打招呼、你好" \
  --template minimal
```

#### 创建完整 Skill

```bash
neuroflow skill create code-review \
  --description="代码审查框架。触发词：代码审查、review、代码质量" \
  --category code-review \
  --template standard \
  --with-framework \
  --with-examples \
  --with-scripts \
  --assign-to assistant \
  --assign-to reviewer
```

#### 创建高级 Skill

```bash
neuroflow skill create competitive-analysis \
  --description="竞争情报分析。触发词：竞争对手、竞争分析、市场定位" \
  --category data-analysis \
  --template advanced
```

### 列出 Skills

```bash
# 列出所有
neuroflow skill list

# 按类别筛选
neuroflow skill list --category data-analysis

# 使用不同格式
neuroflow skill list --format simple
neuroflow skill list --format json
```

### 查看 Skill 详情

```bash
neuroflow skill show data-analysis
```

### 验证 Skill

```bash
# 基本验证
neuroflow skill validate data-analysis

# 严格模式（警告也视为错误）
neuroflow skill validate data-analysis --strict
```

### 分配 Skill 到 Agent

```bash
# 分配
neuroflow skill assign data-analysis assistant

# 分配给多个 Agent
neuroflow skill assign data-analysis analyst
neuroflow skill assign data-analysis reporter

# 移除分配
neuroflow skill assign data-analysis assistant --remove
```

### Skill 目录结构

```
skill-name/
├── SKILL.md                 # 必需：入口文件
├── FRAMEWORK.md             # 可选：详细框架
├── EXAMPLES.md              # 可选：使用示例
├── scripts/
│   ├── process.py          # 可选：Python 脚本
│   └── process.sh          # 可选：Bash 脚本
└── resources/
    └── .gitkeep            # 可选：资源目录
```

### SKILL.md 格式

```markdown
---
name: skill-name
description: 技能描述。触发词：关键词 1、关键词 2
version: 1.0.0
author: Your Name
category: category-name
tags:
  - tag1
  - tag2
trigger_words:
  - keyword1
  - keyword2
assigned_agents:
  - assistant
  - analyst
---

# SKILL NAME

## Goal
技能目标

## Workflow
执行步骤

## Output Format
输出格式
```

---

## Tool 管理

### 创建 Tool

```bash
# 基本用法
neuroflow tool create my-tool \
  --description="工具描述"

# 指定输出目录
neuroflow tool create calculator \
  --description="计算器工具" \
  --output-dir tools
```

### 列出 Tools

```bash
neuroflow tool list
```

### 测试 Tool

```bash
neuroflow tool test calculator
```

---

## 运行应用

### 运行脚本

```bash
# 运行应用
neuroflow run app.py

# 详细模式
neuroflow run app.py --verbose
```

### 启动服务器

```bash
# 基本启动
neuroflow serve

# 自定义端口
neuroflow serve --port 8080

# 自动重载
neuroflow serve --reload

# 多进程
neuroflow serve --workers 4
```

---

## 完整工作流示例

### 1. 创建项目

```bash
neuroflow init my-assistant
cd my-assistant
```

### 2. 创建 Agent

```bash
neuroflow agent create assistant \
  --description="智能助手" \
  --llm-provider openai
```

### 3. 创建 Skills

```bash
# 数据分析技能
neuroflow skill create data-analysis \
  --description="数据分析框架。触发词：数据分析、统计、洞察" \
  --category data-analysis \
  --template standard \
  --assign-to assistant

# 代码审查技能
neuroflow skill create code-review \
  --description="代码审查框架。触发词：代码审查、review" \
  --category code-review \
  --template standard \
  --assign-to assistant
```

### 4. 创建 Tools

```bash
neuroflow tool create calculator \
  --description="计算器"
```

### 5. 运行

```bash
neuroflow run app.py
```

---

## 最佳实践

### Skill 命名

- 使用小写字母和连字符
- 使用描述性名称
- 避免保留字

```bash
# ✅ 好
neuroflow skill create data-analysis
neuroflow skill create code-review

# ❌ 避免
neuroflow skill create DataAnalysis
neuroflow skill create skill1
```

### Skill 描述

描述应该包含功能和触发词：

```bash
# ✅ 好
--description="代码审查框架。用于审查代码质量、安全性和可维护性。触发词：代码审查、review、代码质量"

# ❌ 差
--description="一个很有用的技能"
```

### 模板选择

- **minimal**: 简单技能，快速原型
- **standard**: 生产技能（推荐）
- **advanced**: 复杂工作流，企业级技能

### 文件组织

```
my-project/
├── agents/          # Agent 定义
├── skills/          # Skills
│   ├── data-analysis/
│   └── code-review/
├── tools/           # Tools
│   └── calculator/
└── app.py          # 应用入口
```

---

## 故障排除

### 命令未找到

```bash
# 确保已安装
pip install -e .

# 检查路径
which neuroflow
```

### Skill 验证失败

```bash
# 查看详细错误
neuroflow skill validate my-skill

# 检查必需字段
# - name
# - description
```

### 权限问题

```bash
# 使用 --user 安装
pip install --user -e .
```

---

## 相关文档

- [Skills 使用指南](../SKILLS_GUIDE.md)
- [Agent 开发指南](../guides/building-agents.md)
- [工具开发指南](../guides/developing-tools.md)
