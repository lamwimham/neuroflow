# 如何正确创建 Agent

**版本**: v0.4.0  
**最后更新**: 2026-02-19

---

## ✅ 推荐方式：使用 CLI 创建

**最佳实践**是使用 `neuroflow agent create` 命令创建 Agent，这会自动生成正确的代码模板。

### 基本用法

```bash
# 创建基本 Agent
neuroflow agent create assistant --description="智能助手"
```

这会创建 `agents/assistant.py` 文件，包含正确的代码结构。

### 完整示例

```bash
# 创建 Agent
neuroflow agent create analyst \
    --description="数据分析专家" \
    --llm-provider openai \
    --model "gpt-4"

# 查看创建的 Agent
neuroflow agent list

# 运行 Agent
neuroflow agent run analyst "分析这个数据：1, 2, 3, 4, 5"
```

### 生成的代码结构

```python
"""
analyst Agent

数据分析专家
"""
import asyncio
from neuroflow import AINativeAgent, AINativeAgentConfig, LLMConfig


class AnalystAgent(AINativeAgent):
    """数据分析专家"""
    
    def __init__(self):
        super().__init__(
            AINativeAgentConfig(
                name="analyst",              # ✅ 自动设置
                description="数据分析专家",   # ✅ 自动设置
                llm_config=LLMConfig(
                    provider="openai",       # ✅ 自动设置
                    model="gpt-4",           # ✅ 自动设置
                ),
            )
        )
        
        # 注册工具
        self._register_tools()
    
    def _register_tools(self):
        """注册 Agent 专用工具"""
        
        @self.tool(name="greet", description="问候用户")
        async def greet(name: str) -> str:
            """问候用户"""
            return f"你好，{name}! 我是 analyst，很高兴为你服务。"
    
    async def handle_request(self, user_message: str) -> dict:
        """处理用户请求"""
        return await self.handle(user_message)


async def main():
    """测试 Agent"""
    agent = AnalystAgent()
    
    # 测试
    print("=" * 50)
    print(f"测试：{agent.config.description}")
    print("=" * 50)
    
    result = await agent.handle_request("你好")
    print(f"响应：{result['response']}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## ❌ 错误方式：手动创建

手动创建 Agent 容易出错，特别是缺少必需的参数。

### 常见错误

```python
# ❌ 错误示例 1: 缺少 name 参数
class MyAgent(AINativeAgent):
    def __init__(self):
        super().__init__(AINativeAgentConfig())  # ❌ 错误：缺少 name

# ❌ 错误示例 2: 参数位置错误
class MyAgent(AINativeAgent):
    def __init__(self):
        super().__init__("my_agent")  # ❌ 错误：应该使用配置对象

# ❌ 错误示例 3: 忘记调用父类构造函数
class MyAgent(AINativeAgent):
    def __init__(self):
        # ❌ 错误：忘记调用 super().__init__()
        self.tools = []
```

### 正确方式

```python
# ✅ 正确示例
class MyAgent(AINativeAgent):
    def __init__(self):
        super().__init__(
            AINativeAgentConfig(
                name="my_agent",              # ✅ 必需
                description="我的 Agent",      # ✅ 推荐
                llm_config=LLMConfig(         # ✅ 可选
                    provider="openai",
                    model="gpt-4",
                ),
            )
        )
```

---

## 🔧 修复已存在的错误 Agent

如果你的 Agent 文件有错误，可以使用以下方法修复：

### 方法 1: 使用修复脚本

```bash
# 进入 SDK 目录
cd sdk

# 运行修复脚本
python3 scripts/fix_agent.py agents/first_agent.py
```

### 方法 2: 手动修复

编辑你的 Agent 文件，确保 `__init__` 方法正确：

```python
# 修改前（错误）
class FirstAgent(AINativeAgent):
    def __init__(self):
        # ❌ 错误：缺少 name 参数
        super().__init__(AINativeAgentConfig())

# 修改后（正确）
class FirstAgent(AINativeAgent):
    def __init__(self):
        # ✅ 正确：提供所有必需参数
        super().__init__(
            AINativeAgentConfig(
                name="first_agent",
                description="第一个 Agent",
                llm_config=LLMConfig(
                    provider="openai",
                    model="gpt-4",
                ),
            )
        )
```

### 方法 3: 重新创建

```bash
# 删除错误的 Agent
rm agents/first_agent.py

# 重新创建
neuroflow agent create first_agent --description="第一个 Agent"
```

---

## 📋 完整工作流

### 1. 创建项目

```bash
neuroflow init my-project
cd my-project
```

### 2. 创建 Agent

```bash
neuroflow agent create assistant \
    --description="智能助手" \
    --llm-provider openai \
    --model "gpt-4"
```

### 3. 设置环境变量

```bash
export OPENAI_API_KEY="your-api-key"
```

### 4. 运行 Agent

```bash
# 方式 1: 使用 CLI 运行
neuroflow agent run assistant "你好"

# 方式 2: 直接运行 Python 脚本
python3 agents/assistant.py
```

### 5. 查看结果

```
🤖 运行 Agent: assistant
💬 消息：你好
📁 文件：agents/assistant.py

==================================================
响应:
==================================================
你好！我是 assistant，很高兴为你服务。

🛠️  使用的工具：1 个
   ✅ greet
```

---

## 🎯 最佳实践

### 1. 使用 CLI 创建

始终使用 `neuroflow agent create` 创建 Agent，避免手动错误。

### 2. 有意义的命名

```bash
# ✅ 好
neuroflow agent create data-analyst
neuroflow agent create customer-support

# ❌ 避免
neuroflow agent create agent1
neuroflow agent create test
```

### 3. 清晰的描述

```bash
# ✅ 好
--description="数据分析专家，擅长统计分析和可视化"

# ❌ 差
--description="一个 Agent"
```

### 4. 选择合适的模型

```bash
# 简单任务
neuroflow agent create assistant \
    --llm-provider openai \
    --model "gpt-3.5-turbo"

# 复杂任务
neuroflow agent create analyst \
    --llm-provider openai \
    --model "gpt-4"
```

### 5. 添加自定义工具

编辑生成的 Agent 文件，添加领域特定的工具：

```python
def _register_tools(self):
    """注册 Agent 专用工具"""
    
    @self.tool(name="analyze", description="数据分析")
    async def analyze(data: str) -> dict:
        """分析数据"""
        numbers = [float(x) for x in data.split(',')]
        return {
            "count": len(numbers),
            "sum": sum(numbers),
            "average": sum(numbers) / len(numbers),
        }
```

---

## 📚 相关文档

- [CLI 完整使用指南](CLI_COMPLETE_GUIDE.md)
- [故障排除指南](TROUBLESHOOTING.md)
- [架构与迭代讨论](ARCHITECTURE_AND_ITERATION.md)

---

## 🆘 常见问题

### Q: 创建 Agent 后如何修改？

A: 直接编辑 `agents/<agent_name>.py` 文件即可。

### Q: 如何删除 Agent？

A: 直接删除文件：`rm agents/<agent_name>.py`

### Q: 如何查看 Agent 详情？

A: 使用命令：`neuroflow agent show <agent_name>`

### Q: 如何测试 Agent？

A: 使用命令：`neuroflow agent run <agent_name> "测试消息"`

---

**版本**: v0.4.0  
**最后更新**: 2026-02-19
