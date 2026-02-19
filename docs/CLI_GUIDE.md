# NeuroFlow CLI 使用指南

## 安装

```bash
cd sdk
pip install -e .
```

验证安装：
```bash
neuroflow --version
```

---

## 快速开始

### 1. 创建项目

```bash
# 创建新项目
neuroflow init my_project

# 使用完整模板
neuroflow init my_project --template full
```

### 2. 创建 Agent

```bash
# 创建 Agent
neuroflow agent create assistant --description="智能助手"

# 指定 LLM 提供商
neuroflow agent create assistant --llm-provider anthropic
```

### 3. 创建工具

```bash
# 创建工具
neuroflow tool create calculator --description="计算器"
```

### 4. 运行应用

```bash
# 运行应用
neuroflow run app.py

# 详细模式
neuroflow run app.py --verbose
```

### 5. 启动服务器

```bash
# 启动服务器
neuroflow serve

# 自定义端口
neuroflow serve --port 8080

# 自动重载
neuroflow serve --reload
```

---

## 命令参考

### neuroflow init

创建新的 NeuroFlow 项目。

```bash
neuroflow init <project_name> [options]
```

**选项**:
- `--template, -t <template>` - 项目模板 (minimal|full)

**示例**:
```bash
neuroflow init my_project
neuroflow init my_project --template full
```

---

### neuroflow agent

管理 Agent。

#### create

创建新的 Agent。

```bash
neuroflow agent create <agent_name> [options]
```

**选项**:
- `--description, -d <description>` - Agent 描述
- `--llm-provider <provider>` - LLM 提供商 (openai|anthropic|ollama)

**示例**:
```bash
neuroflow agent create assistant
neuroflow agent create data_analyst --description="数据分析专家"
neuroflow agent create translator --llm-provider anthropic
```

#### list

列出所有 Agent。

```bash
neuroflow agent list
```

#### run

运行 Agent。

```bash
neuroflow agent run <agent_name> <message>
```

**示例**:
```bash
neuroflow agent run assistant "你好"
```

---

### neuroflow tool

管理工具。

#### create

创建新的工具。

```bash
neuroflow tool create <tool_name> [options]
```

**选项**:
- `--description, -d <description>` - 工具描述
- `--output-dir, -o <directory>` - 输出目录

**示例**:
```bash
neuroflow tool create calculator
neuroflow tool create web_search --description="网络搜索"
neuroflow tool create my_tool --output-dir custom_tools
```

#### list

列出所有工具。

```bash
neuroflow tool list
```

**选项**:
- `--output-dir, -o <directory>` - 工具目录

#### test

测试工具。

```bash
neuroflow tool test <tool_name>
```

**示例**:
```bash
neuroflow tool test calculator
```

---

### neuroflow run

运行 NeuroFlow 应用。

```bash
neuroflow run <script> [options]
```

**选项**:
- `--args, -a <args>` - 传递给脚本的参数
- `--verbose, -v` - 详细模式

**示例**:
```bash
neuroflow run app.py
neuroflow run app.py --verbose
neuroflow run app.py -a arg1 -a arg2
```

---

### neuroflow serve

启动 NeuroFlow 服务器。

```bash
neuroflow serve [options]
```

**选项**:
- `--host, -h <host>` - 服务器主机
- `--port, -p <port>` - 服务器端口
- `--reload` - 自动重载
- `--workers, -w <workers>` - 工作进程数
- `--config, -c <config>` - 配置文件

**示例**:
```bash
neuroflow serve
neuroflow serve --port 8080
neuroflow serve --reload
neuroflow serve --workers 4
```

---

## 项目结构

### 最小模板

```
my_project/
├── app.py                 # 主应用
├── neuroflow.toml         # 配置文件
├── requirements.txt       # 依赖
└── README.md             # 说明文档
```

### 完整模板

```
my_project/
├── app.py                 # 主应用
├── neuroflow.toml         # 配置文件
├── requirements.txt       # 依赖
├── README.md             # 说明文档
├── agents/
│   └── example.py        # Agent 示例
├── tools/
│   └── example.py        # 工具示例
└── tests/
    └── __init__.py       # 测试
```

---

## 配置文件

`neuroflow.toml` 配置文件：

```toml
[agent]
name = "assistant"
llm_provider = "openai"
llm_model = "gpt-4"

[tool]
max_execution_time_ms = 30000
max_parallel_calls = 5

[observability]
tracing_enabled = true
metrics_enabled = true
logs_level = "INFO"
```

---

## 最佳实践

### 1. 项目组织

```
my_project/
├── app.py                 # 应用入口
├── agents/                # Agent 定义
│   ├── assistant.py
│   └── analyst.py
├── tools/                 # 工具定义
│   ├── calculator.py
│   └── search.py
├── tests/                 # 测试
│   ├── test_agents.py
│   └── test_tools.py
└── config/                # 配置
    └── neuroflow.toml
```

### 2. Agent 命名

- 使用小写字母和下划线
- 描述性名称
- 避免保留字

```bash
# 好
neuroflow agent create data_analyst
neuroflow agent create customer_support

# 避免
neuroflow agent create Agent1
neuroflow agent create test
```

### 3. 工具设计

- 单一职责
- 清晰描述
- 完善文档

```python
"""
search_web Tool

搜索互联网获取信息
"""
async def search_web(query: str) -> dict:
    """
    搜索互联网
    
    Args:
        query: 搜索关键词
        
    Returns:
        搜索结果
    """
    # 实现
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

### 权限问题

```bash
# macOS/Linux
sudo pip install -e .

# 或使用用户安装
pip install --user -e .
```

### 导入错误

```bash
# 确保在正确的目录
cd sdk
pip install -e .
```

---

## 更多信息

- [Phase 4 完成报告](PHASE4_COMPLETE.md)
- [开发者指南](DEVELOPER_GUIDE.md)
- [API 参考](API_REFERENCE.md)
