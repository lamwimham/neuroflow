# Agent 基础

Agent (智能体) 是 NeuroFlow 框架中的核心业务单元，负责处理请求、执行逻辑并返回响应。

## 什么是 Agent?

Agent 是一个封装了业务逻辑、工具和记忆的独立实体，具有以下特征:

- 🧠 **自主性**: 能够独立处理请求并做出决策
- 🛠️ **工具使用**: 可以调用各种工具完成任务
- 💬 **通信能力**: 支持与其他 Agent 通信 (A2A)
- 🧩 **可组合**: 可以组合多个工具实现复杂功能
- 📝 **记忆能力**: 能够存储和检索信息

## Agent 生命周期

```
创建 → 注册 → 初始化 → 执行 → 销毁
```

### 1. 创建 Agent

使用 `@agent` 装饰器定义 Agent 类:

```python
from neuroflow import agent, BaseAgent

@agent(name="hello_agent", description="简单的问候 Agent")
class HelloAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        """处理请求的入口方法"""
        name = request.get("name", "World")
        return {"message": f"Hello, {name}!"}
```

### 2. 注册 Agent

装饰器会自动注册 Agent 到全局注册表:

```python
# 自动注册到 _global_agents_registry
# 可以通过装饰器参数控制
@agent(name="my_agent", description="我的 Agent")
class MyAgent(BaseAgent):
    pass
```

### 3. 初始化

创建 Agent 实例时自动初始化:

```python
from neuroflow import NeuroFlowSDK

sdk = await NeuroFlowSDK.create()

# 创建 Agent 实例
agent = MyAgent(name="my_agent", description="我的 Agent")

# 初始化完成，可以使用
```

### 4. 执行

通过 SDK 或直接调用执行 Agent:

```python
# 方式 1: 通过 SDK 执行
result = await sdk.execute_agent("my_agent", {"input": "data"})

# 方式 2: 直接调用
agent_instance = MyAgent()
result = await agent_instance.handle({"input": "data"})
```

### 5. 销毁

清理资源和上下文:

```python
# SDK 关闭时自动清理
await sdk.shutdown()

# 或手动清理
await agent.cleanup()
```

## 定义 Agent

### 基础示例

```python
from neuroflow import agent, BaseAgent

@agent(name="calculator_agent", description="数学计算 Agent")
class CalculatorAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        expression = request.get("expression", "0")
        
        # 执行计算工具
        result = await self.execute_tool("calculate", expression=expression)
        
        return {
            "expression": expression,
            "result": result
        }
```

### 带工具的 Agent

```python
from neuroflow import agent, BaseAgent, tool

@agent(name="weather_agent", description="天气查询 Agent")
class WeatherAgent(BaseAgent):
    # 定义工具
    @tool(name="get_weather", description="获取天气")
    async def get_weather(self, city: str) -> str:
        # 实现天气查询逻辑
        return f"Sunny in {city}"
    
    async def handle(self, request: dict) -> dict:
        city = request.get("city", "Beijing")
        weather = await self.execute_tool("get_weather", city=city)
        
        return {"city": city, "weather": weather}
```

### 带记忆的 Agent

```python
from neuroflow import agent, BaseAgent

@agent(name="preference_agent", description="用户偏好 Agent")
class PreferenceAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        user_id = request.get("user_id")
        
        # 检索用户偏好
        preference = self.retrieve_memory(f"user_{user_id}_preference")
        
        if not preference:
            # 存储新偏好
            preference = request.get("preference", "default")
            self.store_memory(
                key=f"user_{user_id}_preference",
                value=preference,
                memory_type="long_term",
                tags=["user", "preference"]
            )
        
        return {"preference": preference}
```

### 支持 A2A 通信的 Agent

```python
from neuroflow import agent, BaseAgent

@agent(name="coordinator_agent", description="协调 Agent")
class CoordinatorAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        task = request.get("task")
        
        # 请求其他 Agent 协助
        result = await self.request_assistance(
            target_agent="specialist_agent",
            task=task,
            params={"data": request.get("data")}
        )
        
        return {"result": result}
```

### 使用 MCP 的 Agent

```python
from neuroflow import agent, BaseAgent

@agent(name="ai_assistant_agent", description="AI 助手 Agent")
class AIAssistantAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        prompt = request.get("prompt")
        
        # 使用 MCP 生成文本
        response = await self.generate_text(
            prompt=prompt,
            model="gpt-3.5-turbo",
            params={"temperature": 0.7}
        )
        
        return {"response": response}
```

## Agent 方法详解

### handle(request: dict) -> dict

**核心方法**: 处理请求的入口点

```python
async def handle(self, request: dict) -> dict:
    """
    Args:
        request: 请求字典，包含输入参数
    
    Returns:
        响应字典，包含处理结果
    """
    # 1. 解析请求
    input_data = request.get("input")
    
    # 2. 执行逻辑
    result = await self.process(input_data)
    
    # 3. 返回响应
    return {"result": result}
```

### execute_tool(tool_name: str, **kwargs) -> Any

**执行工具**: 调用已注册的工具

```python
async def handle(self, request: dict) -> dict:
    # 执行单个工具
    result = await self.execute_tool(
        "calculate",
        expression="2+2"
    )
    
    return {"result": result}
```

### store_memory(key, value, memory_type, tags, importance, ttl_seconds)

**存储记忆**: 保存信息到记忆系统

```python
async def handle(self, request: dict) -> dict:
    user_id = request.get("user_id")
    preference = request.get("preference")
    
    # 存储长期记忆
    self.store_memory(
        key=f"user_{user_id}",
        value=preference,
        memory_type="long_term",      # short_term, long_term, working
        tags=["user", "preference"],
        importance=0.8,               # 0.0 - 1.0
        ttl_seconds=3600              # 仅用于短期记忆
    )
    
    return {"status": "saved"}
```

### retrieve_memory(key: str) -> Optional[Any]

**检索记忆**: 获取存储的信息

```python
async def handle(self, request: dict) -> dict:
    user_id = request.get("user_id")
    
    # 检索记忆
    preference = self.retrieve_memory(f"user_{user_id}")
    
    return {"preference": preference}
```

### search_memories_by_tags(tags: List[str]) -> List[Any]

**搜索记忆**: 根据标签搜索

```python
async def handle(self, request: dict) -> dict:
    # 搜索所有用户相关记忆
    memories = self.search_memories_by_tags(["user"])
    
    return {"memories": memories}
```

### request_assistance(target_agent, task, params) -> dict

**A2A 通信**: 请求其他 Agent 协助

```python
async def handle(self, request: dict) -> dict:
    # 请求数据 Agent 协助
    data_result = await self.request_assistance(
        target_agent="data_agent",
        task="analyze_data",
        params={"data": request.get("data")}
    )
    
    return {"analysis": data_result}
```

### get_embeddings(texts, model) -> List[List[float]]

**获取嵌入**: 使用 MCP 获取文本向量

```python
async def handle(self, request: dict) -> dict:
    texts = request.get("texts", [])
    
    # 获取嵌入向量
    embeddings = await self.get_embeddings(
        texts=texts,
        model="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    return {"embeddings": embeddings}
```

### generate_text(prompt, model, params) -> str

**文本生成**: 使用 MCP 生成文本

```python
async def handle(self, request: dict) -> dict:
    prompt = request.get("prompt")
    
    # 生成回复
    response = await self.generate_text(
        prompt=prompt,
        model="gpt-3.5-turbo",
        params={"temperature": 0.7, "max_tokens": 100}
    )
    
    return {"response": response}
```

### learn_new_skill(skill_description, examples) -> str

**学习技能**: 让 Agent 学习新能力

```python
async def handle(self, request: dict) -> dict:
    skill_desc = "将中文翻译成英文"
    examples = [
        {"input": "你好", "expected_output": "Hello"},
        {"input": "谢谢", "expected_output": "Thank you"}
    ]
    
    skill_id = await self.learn_new_skill(skill_desc, examples)
    
    return {"skill_id": skill_id}
```

### adapt_to_context(context_description) -> List[str]

**上下文适应**: 根据上下文推荐技能

```python
async def handle(self, request: dict) -> dict:
    context = request.get("context", "math calculation")
    
    # 获取推荐的技能
    recommended = await self.adapt_to_context(context)
    
    return {"recommended_skills": recommended}
```

### improve_existing_skill(skill_name, feedback) -> bool

**改进技能**: 根据反馈优化技能

```python
async def handle(self, request: dict) -> dict:
    skill_name = "translation"
    feedback = {
        "quality": "good",
        "suggestions": ["improve formal tone"]
    }
    
    success = await self.improve_existing_skill(skill_name, feedback)
    
    return {"improved": success}
```

## Agent 模式

### 1. 单一职责模式

每个 Agent 只负责一个明确的功能:

```python
@agent(name="email_sender", description="发送邮件 Agent")
class EmailSenderAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        to = request.get("to")
        subject = request.get("subject")
        body = request.get("body")
        
        # 只负责发送邮件
        await self.execute_tool("send_email", to=to, subject=subject, body=body)
        
        return {"status": "sent"}
```

### 2. 编排器模式

协调多个 Agent 完成复杂任务:

```python
@agent(name="orchestrator", description="任务编排 Agent")
class OrchestratorAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        task = request.get("task")
        
        # 分解任务并协调其他 Agent
        if task == "process_order":
            # 1. 验证订单
            validation = await self.request_assistance(
                "validator_agent", "validate_order", {"order": request}
            )
            
            # 2. 处理支付
            payment = await self.request_assistance(
                "payment_agent", "process_payment", {"amount": request["amount"]}
            )
            
            # 3. 安排发货
            shipping = await self.request_assistance(
                "shipping_agent", "arrange_shipping", {"address": request["address"]}
            )
            
            return {
                "validation": validation,
                "payment": payment,
                "shipping": shipping
            }
```

### 3. 专家模式

专注于特定领域的深度处理:

```python
@agent(name="legal_expert", description="法律专家 Agent")
class LegalExpertAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        document = request.get("document")
        
        # 使用专业工具分析法律文档
        analysis = await self.execute_tool("analyze_legal_document", document=document)
        risk_assessment = await self.execute_tool("assess_legal_risk", document=document)
        
        return {
            "analysis": analysis,
            "risk_assessment": risk_assessment,
            "recommendations": self.generate_recommendations(analysis, risk_assessment)
        }
```

### 4. 流水线模式

多个 Agent 顺序处理数据:

```python
# Agent 1: 数据清洗
@agent(name="data_cleaner")
class DataCleanerAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        raw_data = request.get("data")
        cleaned = await self.execute_tool("clean_data", data=raw_data)
        return {"cleaned_data": cleaned}

# Agent 2: 数据分析
@agent(name="data_analyzer")
class DataAnalyzerAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        data = request.get("cleaned_data")
        analysis = await self.execute_tool("analyze_data", data=data)
        return {"analysis": analysis}

# Agent 3: 报告生成
@agent(name="report_generator")
class ReportGeneratorAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        analysis = request.get("analysis")
        report = await self.generate_text(
            prompt=f"Generate report from: {analysis}"
        )
        return {"report": report}
```

## 最佳实践

### 1. 保持 Agent 简洁

```python
# ❌ 避免：过于复杂的 Agent
@agent(name="do_everything_agent")
class DoEverythingAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        # 1000 行代码...
        pass

# ✅ 推荐：职责单一的 Agent
@agent(name="data_validator")
class DataValidatorAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        return await self.execute_tool("validate", data=request.get("data"))
```

### 2. 使用类型注解

```python
from typing import Dict, List, Optional

@agent(name="typed_agent")
class TypedAgent(BaseAgent):
    async def handle(self, request: Dict[str, any]) -> Dict[str, any]:
        name: str = request.get("name", "Unknown")
        items: List[str] = request.get("items", [])
        
        return {
            "processed": True,
            "count": len(items)
        }
```

### 3. 错误处理

```python
@agent(name="robust_agent")
class RobustAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        try:
            result = await self.execute_tool("risky_operation")
            return {"success": True, "result": result}
        except Exception as e:
            # 记录错误并返回友好响应
            self.context.logger.error(f"Operation failed: {e}")
            return {"success": False, "error": str(e)}
```

### 4. 日志记录

```python
@agent(name="logged_agent")
class LoggedAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        self.context.logger.info(f"Processing request: {request}")
        
        result = await self.execute_tool("process", data=request)
        
        self.context.logger.info(f"Result: {result}")
        
        return result
```

## 调试 Agent

### 1. 打印调试

```python
@agent(name="debug_agent")
class DebugAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        print(f"Request: {request}")
        
        result = await self.execute_tool("test")
        
        print(f"Result: {result}")
        
        return result
```

### 2. 使用调试器

```bash
# 启动调试模式
neuroflow debug

# 在 Python REPL 中测试
>>> from neuroflow import get_sdk
>>> sdk = await get_sdk()
>>> agent = MyAgent()
>>> result = await agent.handle({"test": "data"})
```

### 3. 查看日志

```bash
# 设置日志级别
export NEUROFLOW_LOG_LEVEL=debug

# 运行 Agent
neuroflow run
```

## 测试 Agent

```python
import pytest
from neuroflow import NeuroFlowSDK

@pytest.mark.asyncio
async def test_hello_agent():
    sdk = await NeuroFlowSDK.create()
    agent = HelloAgent(name="test_agent")
    
    result = await agent.handle({"name": "Test"})
    
    assert result["message"] == "Hello, Test!"
    
    await sdk.shutdown()
```

## 下一步

- 🛠️ **[开发工具](../guides/developing-tools.md)** - 学习创建工具
- 💬 **[A2A 通信](../guides/using-mcp.md)** - Agent 间通信
- 🧠 **[记忆系统](../concepts/sandbox.md)** - 深入理解记忆
- 📖 **[最佳实践](../best-practices/agent-design.md)** - Agent 设计模式

---

**参考资源**:
- [NeuroFlow SDK API](../api-reference/python/index.md)
- [示例代码](../examples/basic.md)
- [故障排除](../troubleshooting/faq.md)
