# 基础示例

本页面包含 NeuroFlow 的基础示例代码。

## 最小示例

### Hello World Agent

```python
from neuroflow import agent, BaseAgent

@agent(name="hello_agent", description="Hello World Agent")
class HelloAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        name = request.get("name", "World")
        return {"message": f"Hello, {name}!"}

# 运行
if __name__ == "__main__":
    import asyncio
    from neuroflow import NeuroFlowSDK
    
    async def main():
        sdk = await NeuroFlowSDK.create()
        agent = HelloAgent()
        result = await agent.handle({"name": "NeuroFlow"})
        print(result)
        await sdk.shutdown()
    
    asyncio.run(main())
```

**输出**:
```
{'message': 'Hello, NeuroFlow!'}
```

---

## 工具示例

### 基础工具

```python
from neuroflow import tool

# 简单工具
@tool(name="greet", description="问候某人")
async def greet(name: str) -> str:
    return f"Hello, {name}!"

# 带默认参数
@tool(name="greet_with_time", description="带时间的问候")
async def greet_with_time(name: str, time_of_day: str = "day") -> str:
    return f"Good {time_of_day}, {name}!"

# 同步工具
@tool(name="get_current_time", description="获取当前时间")
def get_current_time() -> str:
    from datetime import datetime
    return datetime.now().isoformat()
```

### 数学工具

```python
from neuroflow import tool
from typing import Union

@tool(name="calculate", description="数学计算器")
async def calculate(expression: str) -> Union[float, str]:
    """
    计算数学表达式
    
    Args:
        expression: 数学表达式，如 "2+2"
    
    Returns:
        计算结果或错误信息
    """
    import re
    
    # 安全检查
    allowed = set('0123456789+-*/(). ')
    if not all(c in allowed for c in expression):
        return "Error: Invalid characters"
    
    try:
        return float(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"Error: {str(e)}"

@tool(name="calculate_bmi", description="计算 BMI")
async def calculate_bmi(weight_kg: float, height_m: float) -> float:
    """计算身体质量指数"""
    return weight_kg / (height_m ** 2)

@tool(name="calculate_percentage", description="计算百分比")
async def calculate_percentage(value: float, total: float) -> float:
    """计算百分比"""
    if total == 0:
        return 0.0
    return (value / total) * 100
```

### 字符串工具

```python
from neuroflow import tool
from typing import List

@tool(name="string_utils", description="字符串处理")
async def string_utils(text: str, operation: str) -> str:
    """
    字符串工具
    
    Args:
        text: 输入文本
        operation: 操作类型 (upper, lower, reverse, capitalize)
    """
    operations = {
        "upper": lambda s: s.upper(),
        "lower": lambda s: s.lower(),
        "reverse": lambda s: s[::-1],
        "capitalize": lambda s: s.capitalize(),
    }
    
    if operation not in operations:
        raise ValueError(f"Unknown operation: {operation}")
    
    return operations[operation](text)

@tool(name="word_count", description="统计词数")
async def word_count(text: str) -> dict:
    """统计文本的词数和字符数"""
    words = text.split()
    return {
        "word_count": len(words),
        "char_count": len(text),
        "char_count_no_spaces": len(text.replace(" ", ""))
    }

@tool(name="extract_hashtags", description="提取标签")
async def extract_hashtags(text: str) -> List[str]:
    """提取文本中的标签"""
    import re
    return re.findall(r'#\w+', text)
```

---

## Agent 示例

### 计算器 Agent

```python
from neuroflow import agent, BaseAgent

@agent(name="calculator_agent", description="计算器 Agent")
class CalculatorAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        expression = request.get("expression", "0")
        
        # 使用内置工具
        result = await self.execute_tool("calculate", expression=expression)
        
        return {
            "expression": expression,
            "result": result
        }

# 使用
async def main():
    from neuroflow import NeuroFlowSDK
    sdk = await NeuroFlowSDK.create()
    
    agent = CalculatorAgent()
    result = await agent.handle({"expression": "10 + 20 * 3"})
    print(result)  # {'expression': '10 + 20 * 3', 'result': 70.0}
    
    await sdk.shutdown()
```

### 天气 Agent

```python
from neuroflow import agent, BaseAgent

@agent(name="weather_agent", description="天气查询 Agent")
class WeatherAgent(BaseAgent):
    @tool(name="get_weather", description="获取天气")
    async def get_weather(self, city: str) -> str:
        """模拟天气查询"""
        # 实际应用中调用天气 API
        weather_data = {
            "Beijing": "Sunny, 25°C",
            "Shanghai": "Cloudy, 22°C",
            "Guangzhou": "Rainy, 28°C",
            "Shenzhen": "Sunny, 30°C",
        }
        return weather_data.get(city, f"Weather in {city} unavailable")
    
    async def handle(self, request: dict) -> dict:
        city = request.get("city", "Beijing")
        
        weather = await self.execute_tool("get_weather", city=city)
        
        return {
            "city": city,
            "weather": weather,
            "timestamp": "2024-01-01T12:00:00Z"
        }
```

### 数据处理 Agent

```python
from neuroflow import agent, BaseAgent
from typing import List, Dict

@agent(name="data_processor", description="数据处理 Agent")
class DataProcessorAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        data = request.get("data", [])
        operation = request.get("operation", "clean")
        
        if operation == "clean":
            result = await self.clean_data(data)
        elif operation == "transform":
            result = await self.transform_data(data)
        elif operation == "analyze":
            result = await self.analyze_data(data)
        else:
            return {"error": f"Unknown operation: {operation}"}
        
        return {
            "operation": operation,
            "result": result
        }
    
    async def clean_data(self, data: List[Dict]) -> List[Dict]:
        """清洗数据：移除空值"""
        return [
            {k: v for k, v in item.items() if v is not None}
            for item in data
        ]
    
    async def transform_data(self, data: List[Dict]) -> List[Dict]:
        """转换数据：添加处理标记"""
        return [
            {**item, "processed": True}
            for item in data
        ]
    
    async def analyze_data(self, data: List[Dict]) -> Dict:
        """分析数据：统计信息"""
        if not data:
            return {"count": 0}
        
        return {
            "count": len(data),
            "fields": list(data[0].keys()),
            "sample": data[0]
        }
```

### 对话 Agent

```python
from neuroflow import agent, BaseAgent

@agent(name="chat_agent", description="对话 Agent")
class ChatAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        user_id = request.get("user_id", "default")
        message = request.get("message", "")
        
        # 获取对话历史
        history_key = f"chat_history_{user_id}"
        history = self.retrieve_memory(history_key) or []
        
        # 生成回复
        response = await self.generate_response(message, history)
        
        # 更新历史
        history.append({"user": message, "bot": response})
        if len(history) > 10:  # 保留最近 10 轮
            history = history[-10:]
        self.store_memory(history_key, history, "long_term")
        
        return {
            "response": response,
            "conversation_id": user_id
        }
    
    async def generate_response(self, message: str, history: list) -> str:
        """生成回复"""
        message_lower = message.lower()
        
        # 简单规则
        if any(word in message_lower for word in ["hello", "hi", "hey"]):
            return "Hello! How can I help you today?"
        elif "help" in message_lower:
            return "I'm here to help! What do you need assistance with?"
        elif "bye" in message_lower:
            return "Goodbye! Have a great day!"
        else:
            return "I understand. Tell me more."
```

---

## 组合示例

### 工具链

```python
from neuroflow import agent, BaseAgent

@agent(name="pipeline_agent", description="数据处理管道 Agent")
class PipelineAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        data = request.get("data")
        
        # 工具链：清洗 → 转换 → 分析
        cleaned = await self.execute_tool("clean_data", data=data)
        transformed = await self.execute_tool("transform_data", data=cleaned)
        analyzed = await self.execute_tool("analyze_data", data=transformed)
        
        return {
            "original": data,
            "cleaned": cleaned,
            "transformed": transformed,
            "analysis": analyzed
        }
```

### 并行执行

```python
import asyncio
from neuroflow import agent, BaseAgent

@agent(name="parallel_agent", description="并行处理 Agent")
class ParallelAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        tasks = request.get("tasks", [])
        
        # 并行执行多个任务
        results = await asyncio.gather(*[
            self.process_task(task) for task in tasks
        ])
        
        return {
            "results": results,
            "total": len(results),
            "success": sum(1 for r in results if r.get("success"))
        }
    
    async def process_task(self, task: dict) -> dict:
        """处理单个任务"""
        try:
            # 模拟处理
            await asyncio.sleep(0.1)
            return {"success": True, "data": task}
        except Exception as e:
            return {"success": False, "error": str(e)}
```

### A2A 协作

```python
from neuroflow import agent, BaseAgent

@agent(name="coordinator_agent", description="协调 Agent")
class CoordinatorAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        task = request.get("task")
        data = request.get("data")
        
        if task == "analyze":
            # 请求分析 Agent 协助
            result = await self.request_assistance(
                target_agent="analyst_agent",
                task="analyze_data",
                params={"data": data}
            )
        
        elif task == "report":
            # 请求报告 Agent 协助
            result = await self.request_assistance(
                target_agent="reporter_agent",
                task="generate_report",
                params={"analysis": data}
            )
        
        else:
            return {"error": f"Unknown task: {task}"}
        
        return {
            "task": task,
            "result": result
        }
```

---

## 测试示例

### 单元测试

```python
import pytest
from neuroflow import NeuroFlowSDK

@pytest.mark.asyncio
async def test_hello_agent():
    sdk = await NeuroFlowSDK.create()
    agent = HelloAgent()
    
    result = await agent.handle({"name": "Test"})
    
    assert result["message"] == "Hello, Test!"
    await sdk.shutdown()

@pytest.mark.asyncio
async def test_calculator_agent():
    sdk = await NeuroFlowSDK.create()
    agent = CalculatorAgent()
    
    result = await agent.handle({"expression": "2+2"})
    
    assert result["result"] == 4.0
    await sdk.shutdown()
```

### 集成测试

```python
import pytest
from neuroflow import NeuroFlowSDK

@pytest.mark.asyncio
async def test_full_workflow():
    sdk = await NeuroFlowSDK.create()
    
    # 1. 执行工具
    tool_result = await sdk.execute_tool("calculate", expression="10*10")
    assert tool_result == 100.0
    
    # 2. 创建和执行 Agent
    agent = DataProcessorAgent()
    agent_result = await agent.handle({
        "data": [{"value": 1}, {"value": 2}],
        "operation": "clean"
    })
    assert agent_result["result"] is not None
    
    # 3. 测试记忆
    agent.store_memory("test_key", "test_value", "short_term")
    retrieved = agent.retrieve_memory("test_key")
    assert retrieved == "test_value"
    
    await sdk.shutdown()
```

---

## 运行示例

### 使用 CLI

```bash
# 创建项目
neuroflow new my-project

# 进入项目
cd my-project

# 运行 Agent
neuroflow run

# 测试 Agent
curl -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{"agent": "hello_agent", "payload": {"name": "World"}}'
```

### 使用 Python

```bash
# 直接运行 Python 文件
python my_agent.py
```

---

**下一步**:
- [进阶示例](advanced.md) - 更复杂的示例
- [构建 Agent](../guides/building-agents.md) - 开发指南
- [API 参考](../api-reference/python/index.md) - 完整 API
