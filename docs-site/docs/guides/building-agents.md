# 构建 Agent

本指南将带你深入了解如何构建实用、可靠的 AI Agent。

## 快速开始

### 最小 Agent

```python
from neuroflow import agent, BaseAgent

@agent(name="minimal_agent", description="最小 Agent 示例")
class MinimalAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        return {"message": "Hello from Agent!"}
```

### 完整示例

```python
from neuroflow import agent, BaseAgent, tool

@agent(name="weather_bot", description="天气查询机器人")
class WeatherBot(BaseAgent):
    """天气查询机器人"""
    
    @tool(name="get_weather", description="获取天气信息")
    async def get_weather(self, city: str) -> str:
        """获取指定城市的天气"""
        # 实际应用中调用天气 API
        return f"Sunny in {city}"
    
    @tool(name="get_forecast", description="获取天气预报")
    async def get_forecast(self, city: str, days: int = 3) -> list:
        """获取天气预报"""
        return [f"Day {i}: Sunny" for i in range(1, days + 1)]
    
    async def handle(self, request: dict) -> dict:
        city = request.get("city", "Beijing")
        action = request.get("action", "current")
        
        if action == "current":
            weather = await self.execute_tool("get_weather", city=city)
            return {"city": city, "weather": weather}
        
        elif action == "forecast":
            days = request.get("days", 3)
            forecast = await self.execute_tool("get_forecast", city=city, days=days)
            return {"city": city, "forecast": forecast}
        
        else:
            return {"error": "Unknown action"}
```

## Agent 结构

### 基本组成部分

```python
from neuroflow import agent, BaseAgent, tool
from typing import Dict, List, Optional

@agent(name="complete_agent", description="完整 Agent 示例")
class CompleteAgent(BaseAgent):
    """
    完整 Agent 示例
    
    Attributes:
        name: Agent 名称
        description: Agent 描述
    """
    
    # 1. 工具定义
    @tool(name="tool1", description="工具 1")
    async def tool1(self, param: str) -> str:
        """工具 1 实现"""
        return f"Processed: {param}"
    
    # 2. 辅助方法
    def _validate_request(self, request: dict) -> bool:
        """验证请求"""
        return "input" in request
    
    def _format_response(self, data: any) -> dict:
        """格式化响应"""
        return {"data": data, "status": "success"}
    
    # 3. 主处理方法
    async def handle(self, request: dict) -> dict:
        """
        处理请求的入口方法
        
        Args:
            request: 请求字典
        
        Returns:
            响应字典
        """
        # 验证请求
        if not self._validate_request(request):
            return {"error": "Invalid request", "status": "error"}
        
        # 处理逻辑
        input_data = request.get("input")
        result = await self.execute_tool("tool1", param=input_data)
        
        # 返回响应
        return self._format_response(result)
```

## 实用 Agent 模式

### 1. 数据管道 Agent

处理数据转换和分析:

```python
from neuroflow import agent, BaseAgent

@agent(name="data_pipeline", description="数据处理管道")
class DataPipelineAgent(BaseAgent):
    """数据管道 Agent"""
    
    async def handle(self, request: dict) -> dict:
        raw_data = request.get("data")
        
        # 步骤 1: 数据清洗
        cleaned = await self._clean_data(raw_data)
        
        # 步骤 2: 数据转换
        transformed = await self._transform_data(cleaned)
        
        # 步骤 3: 数据分析
        analysis = await self._analyze_data(transformed)
        
        # 步骤 4: 生成报告
        report = await self._generate_report(analysis)
        
        return {
            "original": raw_data,
            "cleaned": cleaned,
            "transformed": transformed,
            "analysis": analysis,
            "report": report
        }
    
    async def _clean_data(self, data: list) -> list:
        """清洗数据"""
        # 实现清洗逻辑
        return [item for item in data if item is not None]
    
    async def _transform_data(self, data: list) -> list:
        """转换数据"""
        # 实现转换逻辑
        return [{"value": item * 2} for item in data]
    
    async def _analyze_data(self, data: list) -> dict:
        """分析数据"""
        # 实现分析逻辑
        return {
            "count": len(data),
            "average": sum(d.get("value", 0) for d in data) / len(data) if data else 0
        }
    
    async def _generate_report(self, analysis: dict) -> str:
        """生成报告"""
        return f"Analysis Report: Count={analysis['count']}, Avg={analysis['average']:.2f}"
```

### 2. API 集成 Agent

集成外部 API 服务:

```python
from neuroflow import agent, BaseAgent
import aiohttp

@agent(name="api_integration", description="API 集成 Agent")
class APIIntegrationAgent(BaseAgent):
    """API 集成 Agent"""
    
    async def handle(self, request: dict) -> dict:
        endpoint = request.get("endpoint")
        params = request.get("params", {})
        
        async with aiohttp.ClientSession() as session:
            # 调用外部 API
            async with session.get(endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"data": data, "status": "success"}
                else:
                    return {
                        "error": f"API error: {response.status}",
                        "status": "error"
                    }
```

### 3. 决策 Agent

基于规则或 AI 做决策:

```python
from neuroflow import agent, BaseAgent

@agent(name="decision_maker", description="决策 Agent")
class DecisionMakerAgent(BaseAgent):
    """决策 Agent"""
    
    async def handle(self, request: dict) -> dict:
        context = request.get("context", {})
        
        # 收集信息
        info = await self._gather_information(context)
        
        # 分析选项
        options = await self._analyze_options(info)
        
        # 评估风险
        risks = await self._evaluate_risks(options)
        
        # 做出决策
        decision = self._make_decision(options, risks)
        
        return {
            "decision": decision,
            "options": options,
            "risks": risks,
            "reasoning": self._explain_reasoning(decision)
        }
    
    async def _gather_information(self, context: dict) -> dict:
        """收集信息"""
        # 从记忆或外部源收集信息
        return {"context": context}
    
    async def _analyze_options(self, info: dict) -> list:
        """分析选项"""
        # 生成可能的选项
        return ["option1", "option2", "option3"]
    
    async def _evaluate_risks(self, options: list) -> list:
        """评估风险"""
        # 评估每个选项的风险
        return [{"option": opt, "risk": "low"} for opt in options]
    
    def _make_decision(self, options: list, risks: list) -> str:
        """做出决策"""
        # 基于风险评估选择最佳选项
        return options[0]
    
    def _explain_reasoning(self, decision: str) -> str:
        """解释推理过程"""
        return f"Selected {decision} based on risk assessment"
```

### 4. 对话 Agent

处理多轮对话:

```python
from neuroflow import agent, BaseAgent

@agent(name="chat_bot", description="对话机器人")
class ChatBotAgent(BaseAgent):
    """对话机器人 Agent"""
    
    async def handle(self, request: dict) -> dict:
        user_id = request.get("user_id")
        message = request.get("message")
        
        # 获取对话历史
        history = self._get_conversation_history(user_id)
        
        # 理解意图
        intent = await self._understand_intent(message, history)
        
        # 生成回复
        response = await self._generate_response(intent, history)
        
        # 更新历史
        self._update_conversation_history(user_id, message, response)
        
        return {
            "response": response,
            "intent": intent,
            "conversation_id": user_id
        }
    
    def _get_conversation_history(self, user_id: str) -> list:
        """获取对话历史"""
        key = f"conversation_{user_id}"
        return self.retrieve_memory(key) or []
    
    def _update_conversation_history(self, user_id: str, user_msg: str, bot_resp: str):
        """更新对话历史"""
        key = f"conversation_{user_id}"
        history = self._get_conversation_history(user_id)
        history.append({"user": user_msg, "bot": bot_resp})
        
        # 只保留最近 10 轮
        if len(history) > 10:
            history = history[-10:]
        
        self.store_memory(key, history, "long_term")
    
    async def _understand_intent(self, message: str, history: list) -> str:
        """理解意图"""
        # 使用 AI 或规则识别意图
        message_lower = message.lower()
        
        if "hello" in message_lower or "hi" in message_lower:
            return "greeting"
        elif "help" in message_lower:
            return "help_request"
        else:
            return "general"
    
    async def _generate_response(self, intent: str, history: list) -> str:
        """生成回复"""
        if intent == "greeting":
            return "Hello! How can I help you today?"
        elif intent == "help_request":
            return "I'm here to help! What do you need assistance with?"
        else:
            return "I understand. Tell me more."
```

### 5. 任务编排 Agent

协调多个 Agent 完成任务:

```python
from neuroflow import agent, BaseAgent

@agent(name="orchestrator", description="任务编排 Agent")
class OrchestratorAgent(BaseAgent):
    """任务编排 Agent"""
    
    async def handle(self, request: dict) -> dict:
        task = request.get("task")
        data = request.get("data")
        
        if task == "process_order":
            return await self._process_order(data)
        elif task == "generate_report":
            return await self._generate_report(data)
        else:
            return {"error": "Unknown task"}
    
    async def _process_order(self, order: dict) -> dict:
        """处理订单"""
        # 1. 验证订单
        validation = await self.request_assistance(
            target_agent="validator_agent",
            task="validate_order",
            params={"order": order}
        )
        
        if not validation.get("valid"):
            return {"error": "Order validation failed"}
        
        # 2. 处理支付
        payment = await self.request_assistance(
            target_agent="payment_agent",
            task="process_payment",
            params={"amount": order["amount"]}
        )
        
        # 3. 安排发货
        shipping = await self.request_assistance(
            target_agent="shipping_agent",
            task="arrange_shipping",
            params={"address": order["shipping_address"]}
        )
        
        return {
            "status": "success",
            "order_id": order.get("id"),
            "validation": validation,
            "payment": payment,
            "shipping": shipping
        }
    
    async def _generate_report(self, data: dict) -> dict:
        """生成报告"""
        # 1. 收集数据
        collected = await self.request_assistance(
            target_agent="data_collector",
            task="collect_data",
            params=data
        )
        
        # 2. 分析数据
        analysis = await self.request_assistance(
            target_agent="analyst_agent",
            task="analyze_data",
            params={"data": collected}
        )
        
        # 3. 生成报告
        report = await self.generate_text(
            prompt=f"Generate a comprehensive report from: {analysis}"
        )
        
        return {
            "status": "success",
            "report": report,
            "analysis": analysis
        }
```

## 使用记忆系统

### 短期记忆

```python
@agent(name="session_agent")
class SessionAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        session_id = request.get("session_id")
        
        # 存储短期记忆 (临时数据)
        self.store_memory(
            key=f"session_{session_id}",
            value=request.get("data"),
            memory_type="short_term",
            ttl_seconds=3600  # 1 小时后过期
        )
        
        return {"status": "saved"}
```

### 长期记忆

```python
@agent(name="preference_agent")
class PreferenceAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        user_id = request.get("user_id")
        
        # 存储长期记忆 (持久化数据)
        self.store_memory(
            key=f"user_{user_id}_preferences",
            value=request.get("preferences"),
            memory_type="long_term",
            tags=["user", "preferences"],
            importance=0.9
        )
        
        return {"status": "saved"}
```

### 记忆搜索

```python
@agent(name="memory_searcher")
class MemorySearcherAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        query_tags = request.get("tags", [])
        
        # 搜索记忆
        memories = self.search_memories_by_tags(query_tags)
        
        # 按类型搜索
        long_term_memories = self.search_memories_by_type("long_term")
        
        return {
            "memories": memories,
            "long_term_count": len(long_term_memories)
        }
```

## 错误处理

### 基础错误处理

```python
@agent(name="error_handler")
class ErrorHandlerAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        try:
            result = await self.execute_tool("risky_operation")
            return {"success": True, "result": result}
        except Exception as e:
            self.context.logger.error(f"Operation failed: {e}")
            return {"success": False, "error": str(e)}
```

### 详细错误处理

```python
from typing import Optional

class AgentError(Exception):
    """Agent 自定义错误"""
    pass

class ValidationError(AgentError):
    """验证错误"""
    pass

class ProcessingError(AgentError):
    """处理错误"""
    pass

@agent(name="robust_agent")
class RobustAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        try:
            # 验证阶段
            self._validate_request(request)
            
            # 处理阶段
            result = await self._process(request)
            
            return {"success": True, "data": result}
        
        except ValidationError as e:
            self.context.logger.warning(f"Validation failed: {e}")
            return {"success": False, "error": "validation_error", "message": str(e)}
        
        except ProcessingError as e:
            self.context.logger.error(f"Processing failed: {e}")
            return {"success": False, "error": "processing_error", "message": str(e)}
        
        except Exception as e:
            self.context.logger.exception(f"Unexpected error: {e}")
            return {"success": False, "error": "internal_error"}
    
    def _validate_request(self, request: dict):
        """验证请求"""
        if "required_field" not in request:
            raise ValidationError("Missing required field")
    
    async def _process(self, request: dict) -> any:
        """处理请求"""
        # 实现处理逻辑
        pass
```

## 性能优化

### 1. 缓存结果

```python
from functools import lru_cache

@agent(name="cached_agent")
class CachedAgent(BaseAgent):
    @lru_cache(maxsize=100)
    async def expensive_operation(self, param: str) -> str:
        # 耗时操作
        return f"Result for {param}"
    
    async def handle(self, request: dict) -> dict:
        param = request.get("param")
        result = await self.expensive_operation(param)
        return {"result": result}
```

### 2. 批量处理

```python
import asyncio

@agent(name="batch_agent")
class BatchAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        items = request.get("items", [])
        
        # 批量处理 (并发)
        results = await asyncio.gather(*[
            self._process_item(item) for item in items
        ])
        
        return {"results": results}
    
    async def _process_item(self, item: any) -> any:
        """处理单个物品"""
        # 实现处理逻辑
        return item
```

### 3. 流式处理

```python
@agent(name="streaming_agent")
class StreamingAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        data_stream = request.get("stream")
        
        results = []
        async for item in data_stream:
            result = await self._process_item(item)
            results.append(result)
            
            # 可以实时返回部分结果
            if len(results) >= 10:
                yield {"partial": results}
                results = []
        
        return {"final": results}
```

## 测试 Agent

### 单元测试

```python
import pytest
from neuroflow import NeuroFlowSDK

@pytest.mark.asyncio
async def test_weather_agent():
    sdk = await NeuroFlowSDK.create()
    agent = WeatherBot(name="test_weather")
    
    # 测试当前天气
    result = await agent.handle({
        "city": "Beijing",
        "action": "current"
    })
    
    assert result["city"] == "Beijing"
    assert "weather" in result
    
    # 测试天气预报
    result = await agent.handle({
        "city": "Shanghai",
        "action": "forecast",
        "days": 5
    })
    
    assert len(result["forecast"]) == 5
    
    await sdk.shutdown()
```

### 集成测试

```python
@pytest.mark.asyncio
async def test_orchestrator_integration():
    sdk = await NeuroFlowSDK.create()
    
    # 注册所有相关 Agent
    orchestrator = OrchestratorAgent(name="orchestrator")
    
    # 测试完整流程
    result = await orchestrator.handle({
        "task": "process_order",
        "data": {
            "id": "order_123",
            "amount": 100,
            "shipping_address": "123 Main St"
        }
    })
    
    assert result["status"] == "success"
    assert "order_id" in result
    
    await sdk.shutdown()
```

## 调试技巧

### 1. 日志记录

```python
import logging

@agent(name="debuggable_agent")
class DebuggableAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        self.context.logger.debug(f"Request received: {request}")
        
        result = await self._process(request)
        
        self.context.logger.info(f"Result: {result}")
        
        return result
    
    async def _process(self, request: dict):
        self.context.logger.debug("Processing started")
        # 处理逻辑
        self.context.logger.debug("Processing completed")
```

### 2. 追踪执行

```python
@agent(name="traced_agent")
class TracedAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        trace_id = self.context.trace_id
        
        self.context.logger.info(f"Trace ID: {trace_id}")
        
        # 在 Jaeger/Zipkin 中查看完整追踪
        result = await self.execute_tool("operation")
        
        return {"trace_id": trace_id, "result": result}
```

## 下一步

- 🛠️ **[开发工具](developing-tools.md)** - 创建自定义工具
- 💬 **[A2A 通信](using-mcp.md)** - Agent 间协作
- 🧪 **[测试方法](testing.md)** - 测试策略
- 📖 **[最佳实践](../best-practices/agent-design.md)** - 设计模式

---

**参考资源**:
- [Agent API 参考](../api-reference/python/index.md#baseagent)
- [示例代码](../examples/basic.md)
- [故障排除](../troubleshooting/faq.md)
