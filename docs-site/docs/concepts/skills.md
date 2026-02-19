# Skills - 技能系统

> **状态**: ✅ 可用  
> **版本**: v1.0.0  
> **支持**: CLI 创建、验证、管理

**Skills** 是 NeuroFlow 中的可复用能力单元，定义了 Agent 可以执行的特定任务或工作流。Skills 提供了标准化的技能描述、执行框架和质量评估机制。

## 🎯 什么是 Skills？

Skills 是 NeuroFlow 的核心概念之一，它将复杂的任务分解为可复用、可组合的能力单元。每个 Skill 包含：

- **标准化描述** (`SKILL.md`): 技能的目的、工作流程、输入输出
- **执行框架** (`FRAMEWORK.md`): 实现细节、算法、代码结构
- **示例库** (`EXAMPLES.md`): 使用示例、最佳实践
- **脚本目录** (`scripts/`): 可执行代码、工具脚本
- **资源目录** (`resources/`): 模板、配置文件、参考数据

## 📁 Skills 目录结构

```
skills/
└── <skill-name>/
    ├── SKILL.md           # 技能定义（必需）
    ├── FRAMEWORK.md       # 实现框架（可选）
    ├── EXAMPLES.md        # 使用示例（可选）
    ├── scripts/           # 脚本目录
    │   └── *.py           # Python 脚本
    └── resources/         # 资源目录
        └── *.json         # 配置文件等
```

## 🚀 快速开始

### 创建 Skill

使用 CLI 创建新的 Skill：

```bash
# 创建基本 Skill
neuroflow skill create my-skill -d "技能描述"

# 创建完整 Skill（包含所有文件）
neuroflow skill create my-skill \
    -d "技能描述" \
    --with-framework \
    --with-examples \
    --with-scripts

# 使用高级模板
neuroflow skill create my-skill \
    -d "技能描述" \
    -t advanced \
    --category data-analysis
```

### Skill 命令

```bash
# 创建 Skill
neuroflow skill create <name> -d "描述"

# 列出所有 Skills
neuroflow skill list

# 验证 Skill 格式
neuroflow skill validate <name>

# 显示 Skill 详情
neuroflow skill show <name>

# 删除 Skill
neuroflow skill delete <name>
```

## 📋 SKILL.md 结构

SKILL.md 是 Skill 的核心定义文件，采用 YAML Front Matter + Markdown 格式：

### Front Matter

```yaml
---
name: technical-indicators
description: 提供加密货币交易技术分析指标计算
version: 1.0.0
author: Your Name
category: data-analysis
created: 2026-02-19
tags:
  - trading
  - indicators
  - analysis
trigger_words:
  - 计算指标
  - 技术分析
  - RSI
  - MACD
dependencies:
  - skill: other-skill-name  # 依赖其他 Skill
  - mcp: mcp-server-name     # 依赖 MCP 服务
tools_required:
  - python3
  - numpy
context: fork  # fork 或 shared
allowed_tools:
  - read
  - write
  - bash
assigned_agents:
  - trader
---
```

### 字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | Skill 唯一标识符 |
| `description` | string | ✅ | 技能描述（触发词和能力） |
| `version` | string | ✅ | 语义化版本号 |
| `author` | string | ✅ | 作者信息 |
| `category` | string | ✅ | 分类（data-analysis/code-review/documentation 等） |
| `created` | date | ✅ | 创建日期 |
| `tags` | list | ❌ | 标签列表 |
| `trigger_words` | list | ❌ | 触发此技能的关键词 |
| `dependencies` | list | ❌ | 依赖的 Skill 或 MCP 服务 |
| `tools_required` | list | ❌ | 需要的工具 |
| `context` | string | ❌ | 执行上下文（fork/shared） |
| `allowed_tools` | list | ❌ | 允许使用的工具 |
| `assigned_agents` | list | ❌ | 分配给哪些 Agent |

### 正文内容

```markdown
# SKILL NAME

## Overview
高级描述，说明技能的目的和价值

## Goals
### Primary Goal
主要目标

### Secondary Goals
- 次要目标 1
- 次要目标 2

## Prerequisites
### Knowledge Requirements
- 执行技能需要的知识

### Tool Requirements
- 需要的工具和访问权限

### Skill Dependencies
- 依赖的其他技能

## Workflow
### Phase 1: Discovery
1. **步骤名称**
   - 详细说明
   - 注意事项

### Phase 2: Analysis
2. **步骤名称**
   - 详细说明

### Phase 3: Execution
3. **步骤名称**
   - 详细说明

## Implementation
### 子功能 1
```python
# 实现代码
def function():
    pass
```

### 子功能 2
```python
# 实现代码
```

## Output Format
```json
{
  "field": "value"
}
```

## Examples
### 示例 1
```
输入：...
输出：...
```

## Quality Metrics
- **准确性**: 目标值
- **响应时间**: 目标值
- **其他指标**

## Troubleshooting
### 问题 1
**症状**: ...
**解决**: ...

## Related Skills
- skill-name-1
- skill-name-2

## Version History
- **1.0.0** (日期): Initial release
```

## 🔧 Skill 分类

NeuroFlow 支持以下 Skill 分类：

| 分类 | 说明 | 示例 |
|------|------|------|
| `data-analysis` | 数据分析 | 技术指标计算、统计分析 |
| `code-review` | 代码审查 | 代码质量检查、安全审计 |
| `documentation` | 文档生成 | API 文档、使用手册 |
| `testing` | 测试生成 | 单元测试、集成测试 |
| `security` | 安全分析 | 漏洞扫描、风险评估 |
| `performance` | 性能优化 | 性能分析、优化建议 |
| `general` | 通用 | 其他未分类技能 |

## 📦 使用 Skills

### 在 Agent 中使用

Agent 可以通过以下方式调用 Skills：

1. **自动触发**: 当用户消息包含 trigger_words 时自动触发
2. **显式调用**: Agent 主动调用特定 Skill
3. **组合使用**: 多个 Skills 组合完成复杂任务

### Skill 调用示例

```python
from neuroflow import SkillManager

# 初始化 Skill 管理器
skill_manager = SkillManager()

# 加载 Skills
await skill_manager.load_skill("technical-indicators")
await skill_manager.load_skill("trading-signals")

# 调用 Skill
result = await skill_manager.execute(
    skill_name="technical-indicators",
    function="calculate_rsi",
    params={"prices": [42000, 42100, 41900, ...], "period": 14}
)

print(result)
```

## 🎯 最佳实践

### 1. 设计原则

- **单一职责**: 每个 Skill 只做好一件事
- **可复用性**: 设计通用的接口和参数
- **可组合性**: Skills 之间可以互相调用
- **隔离性**: 使用 `context: fork` 确保执行隔离

### 2. 文档规范

- **清晰的触发词**: 帮助用户快速找到技能
- **详细的示例**: 提供多种使用场景
- **明确的输入输出**: 定义清晰的接口
- **完整的错误处理**: 说明可能的错误和解决方案

### 3. 测试验证

```bash
# 验证 Skill 格式
neuroflow skill validate <skill-name>

# 运行 Skill 测试
neuroflow skill test <skill-name>
```

### 4. 版本管理

- 使用语义化版本（SemVer）
- 在 Version History 中记录变更
- 保持向后兼容性
- 重大变更升级主版本号

## 🔍 Skill vs Tool

| 特性 | Skill | Tool |
|------|-------|------|
| **复杂度** | 高（多步骤工作流） | 低（单一功能） |
| **文档** | SKILL.md + FRAMEWORK.md + EXAMPLES.md | 简单描述 |
| **执行** | 多阶段工作流 | 单次函数调用 |
| **组合** | 可组合多个 Tools | 独立执行 |
| **上下文** | 支持 fork/shared | 无状态 |
| **适用场景** | 复杂任务、决策流程 | 简单计算、数据转换 |

## 📚 完整示例

### 技术指标分析 Skill

创建：
```bash
neuroflow skill create technical-indicators \
    -d "提供加密货币交易技术分析指标计算" \
    --category data-analysis \
    -t advanced \
    --with-framework \
    --with-examples
```

使用：
```python
# Agent 自动触发
用户：帮我分析 BTC 的技术指标

Agent: 正在调用 technical-indicators skill...
       计算 RSI: 65.5 (中性)
       计算 MACD: 金叉 (买入信号)
       布林带：价格在中轨附近
       综合建议：持仓观望
```

### 代码审查 Skill

创建：
```bash
neuroflow skill create code-review \
    -d "Python 代码质量审查和安全审计" \
    --category code-review \
    -t advanced
```

## 🤝 贡献 Skills

欢迎贡献 Skills！请遵循以下步骤：

1. **创建 Skill**: 使用 CLI 创建标准结构
2. **完善文档**: 填写 SKILL.md 所有内容
3. **添加示例**: 提供至少 3 个使用示例
4. **验证格式**: `neuroflow skill validate`
5. **提交 PR**: 提交到 NeuroFlow 仓库

## 📖 相关文档

- [Tools 系统](tools.md) - 基础工具定义
- [Agents 系统](agents.md) - Agent 如何使用 Skills
- [CLI 使用指南](../guides/cli.md) - CLI 命令参考
- [最佳实践](../best-practices/skill-design.md) - Skill 设计模式

---

**最后更新**: 2026-02-19  
**维护者**: NeuroFlow Team
