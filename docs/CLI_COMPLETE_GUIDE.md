# NeuroFlow CLI 完整使用指南

**版本**: v0.4.0  
**最后更新**: 2026-02-19

---

## 📦 安装

```bash
cd sdk
pip install -e .
```

验证安装：
```bash
neuroflow --version
```

---

## 🎯 快速开始

```bash
# 1. 查看帮助
neuroflow --help

# 2. 创建项目
neuroflow init my_project
cd my_project

# 3. 创建 Agent
neuroflow agent create assistant --description="智能助手"

# 4. 创建 Skill
neuroflow skill create data-analysis \
    --description="数据分析框架。触发词：数据分析、统计" \
    --category data-analysis \
    --with-scripts \
    --assign-to assistant

# 5. 创建 Tool
neuroflow tool create calculator --description="计算器"

# 6. 运行应用
neuroflow run app.py

# 7. 启动服务器
neuroflow serve --reload
```

---

## 📋 命令总览

| 命令 | 说明 | 用途 |
|------|------|------|
| `neuroflow init` | 创建项目 | 初始化新项目 |
| `neuroflow agent` | Agent 管理 | 创建、列出、运行 Agent |
| `neuroflow skill` | Skill 管理 | 创建、列出、验证 Skill |
| `neuroflow tool` | Tool 管理 | 创建、列出、测试 Tool |
| `neuroflow run` | 运行应用 | 运行一次性脚本 |
| `neuroflow serve` | 启动服务器 | 启动 Web 服务器 |

---

## 🔧 全局选项

```bash
neuroflow [OPTIONS] COMMAND [ARGS]...

选项:
  --version      显示版本号
  -v, --verbose  启用详细模式
  --help         显示帮助信息
```

---

## 📁 neuroflow init

创建新的 NeuroFlow 项目

### 用法

```bash
neuroflow init [OPTIONS] PROJECT_NAME
```

### 选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `-t, --template` | 模板类型 (minimal/standard/full) | minimal |
| `-n, --name` | 项目名称 | PROJECT_NAME |
| `-d, --description` | 项目描述 | "NeuroFlow Project" |
| `-f, --force` | 覆盖已存在的目录 | ❌ |

### 示例

```bash
# 创建最小项目
neuroflow init my_project

# 使用标准模板
neuroflow init my_project --template standard

# 完整配置
neuroflow init my_project \
    --template full \
    --name "My AI Assistant" \
    --description "智能助手项目"
```

### 模板说明

| 模板 | 包含内容 | 适用场景 |
|------|---------|----------|
| **minimal** | app.py, config, agents/, tools/ | 简单项目 |
| **standard** | + 示例代码，tests/ | 标准项目 |
| **full** | + skills/, docs/, scripts/ | 完整项目 |

---

## 🤖 neuroflow agent

Agent 管理命令组

### 子命令

| 命令 | 说明 |
|------|------|
| `create` | 创建新 Agent |
| `list` | 列出所有 Agent |
| `run` | 运行 Agent |
| `show` | 显示 Agent 详情 |

### neuroflow agent create

创建新的 Agent

```bash
neuroflow agent create AGENT_NAME [OPTIONS]
```

**选项**:
- `-d, --description` - Agent 描述
- `--llm-provider` - LLM 提供商 (openai/anthropic/ollama)
- `-m, --model` - LLM 模型
- `-o, --output-dir` - 输出目录 (默认：agents)
- `-f, --force` - 覆盖已存在的 Agent

**示例**:
```bash
# 基本创建
neuroflow agent create assistant

# 指定描述和提供商
neuroflow agent create analyst \
    --description="数据分析专家" \
    --llm-provider anthropic

# 指定模型
neuroflow agent create coder \
    --description="代码专家" \
    --llm-provider openai \
    --model "gpt-4"
```

### neuroflow agent list

列出所有 Agent

```bash
neuroflow agent list [OPTIONS]
```

**选项**:
- `-o, --output-dir` - Agent 目录
- `-f, --format` - 输出格式 (table/json/simple)

**示例**:
```bash
# 列出所有
neuroflow agent list

# JSON 格式
neuroflow agent list --format json
```

### neuroflow agent run

运行 Agent

```bash
neuroflow agent run AGENT_NAME [MESSAGE] [OPTIONS]
```

**选项**:
- `-o, --output-dir` - Agent 目录
- `-v, --verbose` - 详细模式

**示例**:
```bash
# 运行并发送消息
neuroflow agent run assistant "你好"

# 详细模式
neuroflow agent run assistant "分析数据" --verbose
```

### neuroflow agent show

显示 Agent 详情

```bash
neuroflow agent show AGENT_NAME [OPTIONS]
```

**选项**:
- `-o, --output-dir` - Agent 目录

**示例**:
```bash
neuroflow agent show assistant
```

---

## 🎓 neuroflow skill

Skill 管理命令组

### 子命令

| 命令 | 说明 |
|------|------|
| `create` | 创建新 Skill |
| `list` | 列出所有 Skill |
| `show` | 显示 Skill 详情 |
| `validate` | 验证 Skill 格式 |
| `assign` | 分配 Skill 到 Agent |

### neuroflow skill create

创建新的 Skill

```bash
neuroflow skill create SKILL_NAME [OPTIONS]
```

**选项**:
- `-d, --description` - Skill 描述 (必需)
- `-c, --category` - 分类 (data-analysis/code-review/documentation/testing/security/performance/general)
- `-t, --template` - 模板类型 (minimal/standard/advanced)
- `-o, --output-dir` - 输出目录
- `--with-framework` - 生成 FRAMEWORK.md
- `--with-examples` - 生成 EXAMPLES.md
- `--with-scripts` - 生成 scripts 目录
- `--with-resources` - 生成 resources 目录
- `-a, --assign-to` - 分配给 Agent (可多次)
- `--author` - 作者名
- `-f, --force` - 覆盖已存在的 Skill

**示例**:
```bash
# 简单 Skill
neuroflow skill create greet \
    --description="问候技能。触发词：问候、你好" \
    --template minimal

# 标准 Skill
neuroflow skill create data-analysis \
    --description="数据分析框架。触发词：数据分析、统计" \
    --category data-analysis \
    --template standard \
    --with-scripts \
    --assign-to assistant

# 完整 Skill
neuroflow skill create code-review \
    --description="代码审查框架。触发词：代码审查、review" \
    --category code-review \
    --template standard \
    --with-framework \
    --with-examples \
    --with-scripts \
    --assign-to reviewer \
    --assign-to senior-dev

# 高级 Skill
neuroflow skill create competitive-analysis \
    --description="竞争情报分析。触发词：竞争对手、竞争分析" \
    --category data-analysis \
    --template advanced
```

### neuroflow skill list

列出所有 Skill

```bash
neuroflow skill list [OPTIONS]
```

**选项**:
- `-c, --category` - 按分类筛选
- `-o, --output-dir` - Skill 目录
- `-f, --format` - 输出格式 (table/json/simple)

**示例**:
```bash
# 列出所有
neuroflow skill list

# 按分类筛选
neuroflow skill list --category data-analysis

# 简单格式
neuroflow skill list --format simple
```

### neuroflow skill show

显示 Skill 详情

```bash
neuroflow skill show SKILL_NAME [OPTIONS]
```

**选项**:
- `-o, --output-dir` - Skill 目录

**示例**:
```bash
neuroflow skill show data-analysis
```

### neuroflow skill validate

验证 Skill 格式

```bash
neuroflow skill validate SKILL_NAME [OPTIONS]
```

**选项**:
- `-o, --output-dir` - Skill 目录
- `--strict` - 严格模式 (警告视为错误)

**示例**:
```bash
# 基本验证
neuroflow skill validate data-analysis

# 严格模式
neuroflow skill validate data-analysis --strict
```

### neuroflow skill assign

分配 Skill 到 Agent

```bash
neuroflow skill assign SKILL_NAME AGENT_NAME [OPTIONS]
```

**选项**:
- `-o, --output-dir` - Skill 目录
- `-r, --remove` - 移除分配

**示例**:
```bash
# 分配
neuroflow skill assign data-analysis assistant

# 分配给多个 Agent
neuroflow skill assign data-analysis analyst
neuroflow skill assign data-analysis reporter

# 移除分配
neuroflow skill assign data-analysis assistant --remove
```

---

## 🛠️ neuroflow tool

Tool 管理命令组

### 子命令

| 命令 | 说明 |
|------|------|
| `create` | 创建新 Tool |
| `list` | 列出所有 Tool |
| `test` | 测试 Tool |

### neuroflow tool create

创建新的 Tool

```bash
neuroflow tool create TOOL_NAME [OPTIONS]
```

**选项**:
- `-d, --description` - Tool 描述
- `-o, --output-dir` - 输出目录
- `-f, --force` - 覆盖已存在的 Tool

**示例**:
```bash
# 基本创建
neuroflow tool create calculator

# 指定描述
neuroflow tool create web_search \
    --description="网络搜索工具"
```

### neuroflow tool list

列出所有 Tool

```bash
neuroflow tool list [OPTIONS]
```

**选项**:
- `-o, --output-dir` - Tool 目录
- `-f, --format` - 输出格式 (table/json/simple)

**示例**:
```bash
neuroflow tool list
neuroflow tool list --format json
```

### neuroflow tool test

测试 Tool

```bash
neuroflow tool test TOOL_NAME [OPTIONS]
```

**选项**:
- `-o, --output-dir` - Tool 目录
- `-v, --verbose` - 详细模式

**示例**:
```bash
neuroflow tool test calculator
neuroflow tool test calculator --verbose
```

---

## ▶️ neuroflow run

运行 NeuroFlow 应用

```bash
neuroflow run SCRIPT [OPTIONS]
```

**选项**:
- `-a, --args` - 传递给脚本的参数
- `-v, --verbose` - 详细模式
- `-p, --python-path` - 额外的 Python 路径

**示例**:
```bash
# 运行脚本
neuroflow run app.py

# 传递参数
neuroflow run script.py -a arg1 -a arg2

# 详细模式
neuroflow run app.py --verbose
```

**适用场景**:
- ✅ 测试单个 Agent
- ✅ 运行一次性任务
- ✅ 开发和调试
- ✅ CLI 工具
- ✅ 脚本自动化

**不适用场景**:
- ❌ 提供 HTTP API (使用 `neuroflow serve`)
- ❌ 持久化服务 (使用 `neuroflow serve`)

---

## 🌐 neuroflow serve

启动 NeuroFlow 服务器

```bash
neuroflow serve [OPTIONS]
```

**选项**:
- `-h, --host` - 服务器地址 (默认：127.0.0.1)
- `-p, --port` - 服务器端口 (默认：8000)
- `--reload` - 自动重载 (开发模式)
- `-w, --workers` - 工作进程数
- `-c, --config` - 配置文件
- `-a, --app` - FastAPI 应用路径
- `--log-level` - 日志级别

**示例**:
```bash
# 基本启动
neuroflow serve

# 自定义端口
neuroflow serve --port 8080

# 开发模式
neuroflow serve --reload

# 生产模式
neuroflow serve --workers 4

# 完整配置
neuroflow serve \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info
```

**访问地址**:
- 主地址：http://127.0.0.1:8000
- API 文档：http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

**适用场景**:
- ✅ 提供 HTTP API
- ✅ 生产环境部署
- ✅ Web 应用后端
- ✅ 多用户访问
- ✅ 持续运行的服务

**不适用场景**:
- ❌ 一次性脚本 (使用 `neuroflow run`)
- ❌ 快速测试 (使用 `neuroflow run`)

---

## 📊 命令对比

### run vs serve

| 特性 | run | serve |
|------|-----|-------|
| 用途 | 运行脚本 | 启动服务器 |
| 执行模式 | 一次性 | 持续运行 |
| HTTP 服务器 | ❌ | ✅ |
| 端口监听 | ❌ | ✅ |
| 自动重载 | ❌ | ✅ |
| 多进程 | ❌ | ✅ |
| 适用场景 | 测试、脚本 | API、生产 |

---

## 🎯 最佳实践

### 项目组织

```
my-project/
├── app.py              # 主应用
├── neuroflow.toml      # 配置
├── agents/             # Agent 定义
│   ├── assistant.py
│   └── analyst.py
├── skills/             # Skill 定义
│   ├── data-analysis/
│   └── code-review/
└── tools/              # Tool 定义
    └── calculator.py
```

### Skill 命名

```bash
# ✅ 好
neuroflow skill create data-analysis
neuroflow skill create code-review

# ❌ 避免
neuroflow skill create DataAnalysis
neuroflow skill create skill1
```

### Skill 描述

```bash
# ✅ 好的描述
--description="代码审查框架。用于审查代码质量、安全性。触发词：代码审查、review、代码质量"

# ❌ 差的描述
--description="一个很有用的技能"
```

### 开发流程

```bash
# 1. 创建项目
neuroflow init my-project --template standard

# 2. 创建 Agent
neuroflow agent create assistant --description="智能助手"

# 3. 创建 Skills
neuroflow skill create data-analysis \
    --description="数据分析框架。触发词：数据分析、统计" \
    --category data-analysis \
    --assign-to assistant

# 4. 测试
neuroflow agent run assistant "分析这个数据"

# 5. 启动服务器
neuroflow serve --reload
```

---

## 🔧 故障排除

### 命令未找到

```bash
# 确保已安装
pip install -e .

# 检查路径
which neuroflow
```

### 权限问题

```bash
# 使用 --user 安装
pip install --user -e .
```

### Skill 验证失败

```bash
# 查看详细错误
neuroflow skill validate my-skill --verbose

# 检查必需字段
# - name
# - description
```

---

## 📚 相关文档

- [Skills 使用指南](SKILLS_GUIDE.md)
- [Agent 开发指南](guides/building-agents.md)
- [工具开发指南](guides/developing-tools.md)
- [架构与迭代讨论](ARCHITECTURE_AND_ITERATION.md)

---

**版本**: v0.4.0  
**最后更新**: 2026-02-19
