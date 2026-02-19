# NeuroFlow Skills 使用指南

NeuroFlow Skills 是模块化的 Agent 能力包，将程序性知识封装成可复用的技能。

## 什么是 Skills

**Skills** 是 NeuroFlow 中用于封装 Agent 程序性知识的机制，包含：
- **指令**（SKILL.md）- 如何执行任务的详细说明
- **资源**（可选）- 文档、模板、参考材料
- **脚本**（可选）- 确定性处理的代码

### 核心特点

- ✅ **可组合** - Skills 可以互相调用
- ✅ **可移植** - 跨项目共享
- ✅ **按需调用** - 基于描述自动匹配
- ✅ **渐进式披露** - 控制上下文成本

## 快速开始

### 创建第一个 Skill

```bash
# 创建标准模板的 Skill
neuroflow skill create my-skill \
  --description="我的技能描述。触发词：关键词 1、关键词 2" \
  --category general \
  --template standard
```

### Skill 目录结构

```
my-skill/
├── SKILL.md                 # 必需的入口文件
├── FRAMEWORK.md             # 详细框架（可选）
├── EXAMPLES.md              # 使用示例（可选）
└── scripts/
│   └── process.py          # 处理脚本（可选）
```

## CLI 命令

### 创建 Skill

```bash
# 最小模板
neuroflow skill create my-skill \
  --description="简单技能" \
  --template minimal

# 标准模板（推荐）
neuroflow skill create my-skill \
  --description="标准技能，包含完整工作流" \
  --category data-analysis \
  --template standard

# 高级模板
neuroflow skill create my-skill \
  --description="高级技能，包含框架和示例" \
  --category code-review \
  --template advanced
```

### 列出 Skills

```bash
# 列出所有 skills
neuroflow skill list

# 按类别筛选
neuroflow skill list --category code-review
```

### 查看 Skill 详情

```bash
neuroflow skill show my-skill
```

### 验证 Skill

```bash
# 验证 skill 格式
neuroflow skill validate my-skill
```

## SKILL.md 格式

### 基本结构

```markdown
---
name: skill-name
description: 技能描述，包含触发词
version: 1.0.0
author: Your Name
category: category-name
created: YYYY-MM-DD
tags:
  - tag1
  - tag2
trigger_words:
  - keyword1
  - keyword2
---

# SKILL NAME

## Goal
技能目标

## Workflow
执行步骤

## Output Format
输出格式
```

### 必需字段

| 字段 | 说明 |
|------|------|
| `name` | 技能名称（唯一标识） |
| `description` | 技能描述和触发词 |

### 推荐字段

| 字段 | 说明 |
|------|------|
| `version` | 版本号 |
| `author` | 作者 |
| `category` | 分类 |
| `tags` | 标签列表 |
| `trigger_words` | 触发词列表 |

## 最佳实践

### 1. Description 是"路由规则"

```yaml
# ✅ 好的 description
description: 代码审查框架。用于审查代码质量、安全性和可维护性。
             触发词：代码审查、review、代码质量、安全检查、最佳实践

# ❌ 差的 description  
description: 一个很有用的技能
```

### 2. 保持入口文件简洁

- SKILL.md 正文 ≤ 500 行
- 复杂内容拆分到子文件（FRAMEWORK.md、EXAMPLES.md）
- 使用脚本处理确定性任务

### 3. 指令要具体可执行

```markdown
# ✅ 好的指令
## Workflow
1. 读取待审查的代码文件
2. 检查代码风格（参考 STYLE.md）
3. 识别潜在的安全问题
4. 生成审查报告

# ❌ 差的指令
## Workflow
1. 审查代码
2. 输出结果
```

### 4. 定义清晰的输出格式

```markdown
## Output Format
```markdown
# 代码审查报告

## 摘要
<简要总结>

## 发现的问题
### 严重问题
- [ ] 问题 1
- [ ] 问题 2

### 建议改进
- [ ] 改进 1
- [ ] 改进 2

## 总体评价
<评价>
```
```

## 示例 Skills

### 1. 竞争分析 Skill

```bash
neuroflow skill create competitive-analysis \
  --description="竞争情报分析框架。用于结构化比较竞争对手，输出可操作建议。触发词：竞争对手、竞争分析、市场定位、差异化" \
  --category data-analysis \
  --template standard
```

### 2. 代码审查 Skill

```bash
neuroflow skill create code-review \
  --description="代码审查框架。审查代码质量、安全性、性能。触发词：代码审查、review、代码质量、安全检查" \
  --category code-review \
  --template standard
```

### 3. 文档生成 Skill

```bash
neuroflow skill create documentation-generator \
  --description="API 文档生成框架。从代码生成结构化文档。触发词：文档、API 文档、生成文档、说明文档" \
  --category documentation \
  --template standard
```

## Skill 部署

### 个人 Skills

```bash
# 部署到个人目录
mkdir -p ~/.neuroflow/skills
cp -r my-skill ~/.neuroflow/skills/
```

### 项目 Skills

```bash
# 部署到项目目录
mkdir -p .neuroflow/skills
cp -r my-skill .neuroflow/skills/
```

## 与其他功能集成

### 与 MCP 集成

```yaml
# 在 SKILL.md 中声明 MCP 依赖
dependencies:
  - mcp: database
  - mcp: web-search
```

### 与 Tools 集成

```yaml
# 声明需要的工具
tools_required:
  - read_file
  - write_file
  - run_command
```

## 故障排除

### Skill 未被触发

检查：
1. description 是否包含用户会说的关键词
2. trigger_words 是否完整
3. 是否部署到正确位置

### Skill 验证失败

```bash
# 运行验证
neuroflow skill validate my-skill

# 检查常见错误
- 缺少 YAML frontmatter
- 缺少必需字段（name, description）
- YAML 格式错误
```

## 相关文档

- [CLI 使用指南](CLI_GUIDE.md)
- [Agent 开发指南](guides/building-agents.md)
- [工具开发指南](guides/developing-tools.md)
