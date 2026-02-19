# 30 分钟快速入门 NeuroFlow

本教程将带你从零开始，在 30 分钟内创建并运行第一个 AI Agent。

## 📋 前提条件

- Python 3.9+
- 基础 Python 编程知识
- 终端/命令行使用经验

## ⏱️ 时间安排

- **安装**: 5 分钟
- **创建项目**: 5 分钟
- **理解概念**: 5 分钟
- **创建 Agent**: 10 分钟
- **运行和调试**: 5 分钟

## 步骤 1: 安装 NeuroFlow (5 分钟)

### 1.1 创建虚拟环境 (推荐)

```bash
# 创建项目目录
mkdir -p ~/projects/neuroflow-demo
cd ~/projects/neuroflow-demo

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# macOS/Linux
source venv/bin/activate

# Windows
# venv\Scripts\activate
```

### 1.2 安装 NeuroFlow SDK

```bash
# 安装 SDK (包含 CLI 工具)
pip install neuroflow

# 验证安装
neuroflow --version
```

**预期输出**:
```
neuroflow, version 0.3.0
```

✅ **检查点**: 看到版本号表示安装成功！

## 步骤 2: 创建第一个项目 (5 分钟)

### 2.1 生成项目脚手架

```bash
# 创建新项目
neuroflow new hello-agent

# 进入项目目录
cd hello-agent
```

**生成的项目结构**:
```
hello-agent/
├── agents/              # Agent 定义
│   ├── __init__.py
│   └── hello_agent.py   # 问候 Agent 示例
├── tools/               # 工具定义
│   ├── __init__.py
│   └── basic_tools.py   # 基础工具示例
├── config/              # 配置文件
│   └── neuroflow.yaml
├── tests/               # 测试文件
│   ├── __init__.py
│   └── test_agents.py
├── requirements.txt     # 依赖
└── README.md           # 项目说明
```

### 2.2 安装项目依赖

```bash
# 安装项目依赖
pip install -r requirements.txt
```

✅ **检查点**: 项目创建成功，看到目录结构！

## 步骤 3: 理解核心概念 (5 分钟)

### 3.1 Agent 是什么？

Agent 是 NeuroFlow 中的基本业务单元，负责处理请求并返回响应。

```python
from neuroflow import agent

@agent(name="hello_agent", description="简单的问候 Agent")
class HelloAgent:
    async def handle(self, request: dict) -> dict:
        """处理请求"""
        name = request.get("name", "World")
        return {"message": f"Hello, {name}!"}
```

### 3.2 工具 (Tool) 是什么？

工具是可复用的功能单元，可以被 Agent 调用。

```python
from neuroflow import tool

@tool(name="greet", description="问候某人")
async def greet(name: str) -> str:
    """问候工具"""
    return f"Hello, {name}!"
```

### 3.3 SDK 是什么？

SDK 提供统一的 API 来管理 Agent 和工具。

```python
from neuroflow import NeuroFlowSDK

sdk = await NeuroFlowSDK.create()
result = await sdk.execute_tool("greet", name="Alice")
```

✅ **检查点**: 理解 Agent、工具和 SDK 的关系！

## 步骤 4: 创建你的第一个 Agent (10 分钟)

### 4.1 查看示例 Agent

打开 `agents/hello_agent.py`:

```python
"""问候 Agent 示例"""
from neuroflow import agent, tool

@tool(name="greet", description="问候某人")
async def greet(name: str) -> str:
    """问候工具"""
    return f"Hello, {name}!"

@agent(name="hello_agent", description="简单的问候 Agent")
class HelloAgent:
    async def handle(self, request: dict) -> dict:
        """处理请求"""
        from neuroflow import NeuroFlowSDK
        sdk = await NeuroFlowSDK.create()
        
        name = request.get("name", "World")
        greeting = await sdk.execute_tool("greet", name=name)
        
        await sdk.shutdown()
        return {"greeting": greeting}
```

### 4.2 运行 Agent

```bash
# 启动开发服务器
neuroflow run
```

**预期输出**:
```
🚀 启动 NeuroFlow 开发服务器
端口：8080
热重载：禁用
日志级别：info

访问：http://localhost:8080
按 Ctrl+C 停止服务器
```

### 4.3 测试 Agent

打开浏览器访问 `http://localhost:8080`，或使用 curl:

```bash
# 发送测试请求
curl -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{"agent": "hello_agent", "payload": {"name": "Alice"}}'
```

**预期响应**:
```json
{
  "success": true,
  "data": {
    "greeting": "Hello, Alice!"
  },
  "trace_id": "xxx-xxx-xxx"
}
```

✅ **检查点**: Agent 成功运行并返回响应！

### 4.4 自定义 Agent

让我们创建一个个性化的问候 Agent。

创建 `agents/custom_greeting.py`:

```python
"""自定义问候 Agent"""
from neuroflow import agent, tool
import random

@tool(name="creative_greet", description="创意问候")
async def creative_greet(name: str) -> str:
    """创意问候工具"""
    greetings = [
        f"👋 Hello, {name}! Welcome to NeuroFlow!",
        f"🎉 Hi, {name}! Great to see you!",
        f"✨ Hey, {name}! Ready to build amazing things?",
        f"🚀 Greetings, {name}! Let's create AI agents!",
    ]
    return random.choice(greetings)

@agent(name="custom_greeting_agent", description="创意问候 Agent")
class CustomGreetingAgent:
    async def handle(self, request: dict) -> dict:
        """处理请求"""
        from neuroflow import NeuroFlowSDK
        sdk = await NeuroFlowSDK.create()
        
        name = request.get("name", "Developer")
        greeting = await sdk.execute_tool("creative_greet", name=name)
        
        await sdk.shutdown()
        return {
            "greeting": greeting,
            "agent": "custom_greeting_agent"
        }
```

测试新 Agent:

```bash
curl -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{"agent": "custom_greeting_agent", "payload": {"name": "Bob"}}'
```

✅ **检查点**: 成功创建并运行自定义 Agent！

## 步骤 5: 运行和调试 (5 分钟)

### 5.1 使用调试器

```bash
# 启动交互式调试器
neuroflow debug
```

**进入 Python REPL**:
```python
>>> from neuroflow import NeuroFlowSDK
>>> sdk = await NeuroFlowSDK.create()
>>> result = await sdk.execute_tool("greet", name="Debug")
>>> print(result)
'Hello, Debug!'
```

### 5.2 查看工具列表

```bash
# 列出所有工具
neuroflow tools list
```

**预期输出**:
```
📦 可用工具

名称                 分类            描述
-----------------------------------------------------------------
calculate            utility         数学计算器
echo                 utility         回显工具
greet                utility         问候工具

共 3 个工具
```

### 5.3 查看 Agent 列表

```bash
# 列出所有 Agent
neuroflow agents list
```

**预期输出**:
```
🤖 可用 Agent

名称                      描述
-------------------------------------------------------
hello_agent              简单的问候 Agent
custom_greeting_agent    创意问候 Agent

共 2 个 Agent
```

✅ **检查点**: 掌握基本调试命令！

## 🎉 恭喜完成！

你已经成功:
- ✅ 安装 NeuroFlow SDK
- ✅ 创建第一个项目
- ✅ 理解核心概念
- ✅ 创建和运行 Agent
- ✅ 使用调试工具

## 📚 下一步

### 深入学习

1. **[创建第一个 Agent](first-agent.md)** - 更详细的 Agent 开发指南
2. **[工具系统](../concepts/tools.md)** - 学习开发高级工具
3. **[MCP 服务集成](../guides/using-mcp.md)** - 集成外部服务

### 实战示例

1. **数学计算器 Agent**
   ```bash
   neuroflow new math-agent --template basic
   ```

2. **数据处理 Agent**
   ```bash
   neuroflow new data-agent --template data-processing
   ```

3. **交易 Agent**
   ```bash
   neuroflow new trading-agent --template trading
   ```

### 参与社区

- 💬 [加入 Discord 社区](https://discord.gg/neuroflow)
- 🐛 [报告问题](https://github.com/lamWimHam/neuroflow/issues)
- ⭐ [给项目加星](https://github.com/lamWimHam/neuroflow)

## ❓ 常见问题

### Q: 安装失败怎么办？

**A**: 尝试以下命令:
```bash
# 升级 pip
pip install --upgrade pip

# 清除缓存重装
pip cache purge
pip install neuroflow --no-cache-dir
```

### Q: neuroflow 命令找不到？

**A**: 检查虚拟环境是否激活，或者尝试:
```bash
# 使用完整路径
python -m neuroflow.cli.main --help

# 或者重新安装
pip install -e .
```

### Q: Agent 无法启动？

**A**: 检查以下几点:
1. 依赖是否安装：`pip install -r requirements.txt`
2. 端口是否被占用：`lsof -i :8080`
3. 查看错误日志：`neuroflow run --log-level debug`

### Q: 如何修改 Agent 代码？

**A**: 编辑 `agents/` 目录下的文件，然后重启服务器:
```bash
# 编辑文件
vim agents/hello_agent.py

# 重启服务器 (Ctrl+C 停止，然后重新运行)
neuroflow run --reload  # 热重载模式 (开发中)
```

## 📞 获取帮助

- 📖 [完整文档](../index.md)
- 💬 [Discord 社区](https://discord.gg/neuroflow)
- 🐛 [GitHub Issues](https://github.com/lamWimHam/neuroflow/issues)

---

**继续学习**: [创建第一个 Agent](first-agent.md) →
