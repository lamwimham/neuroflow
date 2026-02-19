# 测试方法

本指南介绍如何测试 NeuroFlow Agent 和工具。

## 测试框架

### pytest 配置

创建 `pytest.ini`:

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --cov=sdk/neuroflow
    --cov-report=html
    --cov-report=term-missing
```

创建 `conftest.py`:

```python
import pytest
import asyncio
from neuroflow import NeuroFlowSDK

@pytest.fixture
async def sdk():
    """SDK  fixture"""
    sdk = await NeuroFlowSDK.create()
    yield sdk
    await sdk.shutdown()

@pytest.fixture
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

## 工具测试

### 基础测试

```python
import pytest
from neuroflow import tool

@tool(name="add")
async def add(a: int, b: int) -> int:
    return a + b

@tool(name="divide")
async def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Division by zero")
    return a / b

class TestMathTools:
    @pytest.mark.asyncio
    async def test_add_positive(self):
        """测试正数加法"""
        result = await add(2, 3)
        assert result == 5
    
    @pytest.mark.asyncio
    async def test_add_negative(self):
        """测试负数加法"""
        result = await add(-1, -1)
        assert result == -2
    
    @pytest.mark.asyncio
    async def test_add_zero(self):
        """测试零"""
        result = await add(0, 5)
        assert result == 5
    
    @pytest.mark.asyncio
    async def test_divide_normal(self):
        """测试正常除法"""
        result = await divide(10, 2)
        assert result == 5.0
    
    @pytest.mark.asyncio
    async def test_divide_by_zero(self):
        """测试除零错误"""
        with pytest.raises(ValueError, match="Division by zero"):
            await divide(10, 0)
```

### 参数化测试

```python
import pytest
from neuroflow import tool

@tool(name="multiply")
async def multiply(a: int, b: int) -> int:
    return a * b

class TestMultiply:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("a,b,expected", [
        (2, 3, 6),
        (0, 5, 0),
        (-2, 3, -6),
        (2, -3, -6),
        (-2, -3, 6),
    ])
    async def test_multiply_various(self, a, b, expected):
        """测试各种乘法场景"""
        result = await multiply(a, b)
        assert result == expected
```

## Agent 测试

### 基础测试

```python
import pytest
from neuroflow import agent, BaseAgent, NeuroFlowSDK

@agent(name="hello_agent")
class HelloAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        name = request.get("name", "World")
        return {"message": f"Hello, {name}!"}

class TestHelloAgent:
    @pytest.mark.asyncio
    async def test_hello_default(self, sdk):
        """测试默认问候"""
        agent = HelloAgent()
        result = await agent.handle({})
        
        assert result["message"] == "Hello, World!"
    
    @pytest.mark.asyncio
    async def test_hello_custom(self, sdk):
        """测试自定义问候"""
        agent = HelloAgent()
        result = await agent.handle({"name": "Alice"})
        
        assert result["message"] == "Hello, Alice!"
```

### 带工具的 Agent 测试

```python
import pytest
from neuroflow import agent, BaseAgent, tool

@tool(name="get_weather")
async def get_weather(city: str) -> str:
    weather_data = {
        "Beijing": "Sunny",
        "Shanghai": "Cloudy",
    }
    return weather_data.get(city, "Unknown")

@agent(name="weather_agent")
class WeatherAgent(BaseAgent):
    @tool(name="get_forecast")
    async def get_forecast(self, city: str) -> str:
        return f"Forecast for {city}"
    
    async def handle(self, request: dict) -> dict:
        city = request.get("city", "Beijing")
        action = request.get("action", "current")
        
        if action == "current":
            weather = await self.execute_tool("get_weather", city=city)
            return {"city": city, "weather": weather}
        elif action == "forecast":
            forecast = await self.execute_tool("get_forecast", city=city)
            return {"city": city, "forecast": forecast}
        else:
            return {"error": "Unknown action"}

class TestWeatherAgent:
    @pytest.mark.asyncio
    async def test_current_weather(self, sdk):
        """测试当前天气"""
        agent = WeatherAgent()
        result = await agent.handle({
            "city": "Beijing",
            "action": "current"
        })
        
        assert result["city"] == "Beijing"
        assert result["weather"] == "Sunny"
    
    @pytest.mark.asyncio
    async def test_forecast(self, sdk):
        """测试天气预报"""
        agent = WeatherAgent()
        result = await agent.handle({
            "city": "Shanghai",
            "action": "forecast"
        })
        
        assert result["city"] == "Shanghai"
        assert "Forecast" in result["forecast"]
    
    @pytest.mark.asyncio
    async def test_unknown_action(self, sdk):
        """测试未知操作"""
        agent = WeatherAgent()
        result = await agent.handle({
            "city": "Beijing",
            "action": "unknown"
        })
        
        assert "error" in result
```

### 带记忆的 Agent 测试

```python
import pytest
from neuroflow import agent, BaseAgent

@agent(name="memory_agent")
class MemoryAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        user_id = request.get("user_id")
        action = request.get("action")
        
        if action == "save":
            self.store_memory(
                key=f"user_{user_id}",
                value=request.get("value"),
                memory_type="long_term"
            )
            return {"status": "saved"}
        
        elif action == "load":
            value = self.retrieve_memory(f"user_{user_id}")
            return {"value": value}
        
        else:
            return {"error": "Unknown action"}

class TestMemoryAgent:
    @pytest.mark.asyncio
    async def test_save_and_load(self, sdk):
        """测试保存和加载记忆"""
        agent = MemoryAgent()
        
        # 保存
        save_result = await agent.handle({
            "user_id": "user1",
            "action": "save",
            "value": "test_value"
        })
        assert save_result["status"] == "saved"
        
        # 加载
        load_result = await agent.handle({
            "user_id": "user1",
            "action": "load"
        })
        assert load_result["value"] == "test_value"
```

## 集成测试

### 完整流程测试

```python
import pytest
from neuroflow import NeuroFlowSDK, agent, BaseAgent

@agent(name="processor_agent")
class ProcessorAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        data = request.get("data", [])
        
        # 处理数据
        processed = [item * 2 for item in data]
        
        return {
            "original": data,
            "processed": processed,
            "count": len(processed)
        }

class TestIntegration:
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流程"""
        sdk = await NeuroFlowSDK.create()
        
        try:
            # 1. 测试工具执行
            tool_result = await sdk.execute_tool("calculate", expression="2+2")
            assert tool_result == 4.0
            
            # 2. 注册 Agent
            sdk.register_agent("processor", ProcessorAgent)
            
            # 3. 测试 Agent
            agent_instance = ProcessorAgent()
            agent_result = await agent_instance.handle({
                "data": [1, 2, 3]
            })
            
            assert agent_result["processed"] == [2, 4, 6]
            assert agent_result["count"] == 3
            
            # 4. 测试记忆
            agent_instance.store_memory("test_key", "test_value", "short_term")
            retrieved = agent_instance.retrieve_memory("test_key")
            assert retrieved == "test_value"
            
        finally:
            await sdk.shutdown()
```

### A2A 通信测试

```python
import pytest
from neuroflow import agent, BaseAgent

@agent(name="helper_agent")
class HelperAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        task = request.get("task")
        return {"result": f"Completed: {task}"}

@agent(name="coordinator_agent")
class CoordinatorAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        task = request.get("task")
        
        # 请求协助
        result = await self.request_assistance(
            target_agent="helper_agent",
            task=task,
            params={}
        )
        
        return {"task": task, "helper_result": result}

class TestA2ACommunication:
    @pytest.mark.asyncio
    async def test_a2a_request(self, sdk):
        """测试 A2A 通信"""
        coordinator = CoordinatorAgent()
        
        # 注意：实际测试需要注册 helper_agent
        result = await coordinator.handle({
            "task": "test_task"
        })
        
        assert "task" in result
        assert "helper_result" in result
```

## 性能测试

### 基准测试

```python
import pytest
import time
from neuroflow import agent, BaseAgent

@agent(name="performance_agent")
class PerformanceAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        # 模拟处理
        await asyncio.sleep(0.01)
        return {"status": "ok"}

class TestPerformance:
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_response_time(self):
        """测试响应时间"""
        agent = PerformanceAgent()
        
        start = time.time()
        for _ in range(100):
            await agent.handle({})
        elapsed = time.time() - start
        
        avg_time = elapsed / 100
        assert avg_time < 0.1  # 平均响应时间 < 100ms
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_concurrent_execution(self):
        """测试并发执行"""
        agent = PerformanceAgent()
        
        start = time.time()
        
        # 并发执行 10 个请求
        tasks = [agent.handle({}) for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start
        
        assert len(results) == 10
        assert elapsed < 0.5  # 并发执行应该很快
```

### 负载测试

```python
import pytest
import asyncio
from locust import HttpUser, task, between

class NeuroFlowUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def invoke_agent(self):
        self.client.post(
            "/invoke",
            json={
                "agent": "hello_agent",
                "payload": {"name": "Test"}
            }
        )
    
    @task(1)
    def execute_tool(self):
        self.client.post(
            "/invoke",
            json={
                "agent": "calculator_agent",
                "payload": {"expression": "2+2"}
            }
        )
```

运行负载测试:

```bash
locust -f load_tests.py --host=http://localhost:8080
```

## 模拟和桩

### 模拟外部服务

```python
import pytest
from unittest.mock import AsyncMock, patch
from neuroflow import agent, BaseAgent

@agent(name="api_agent")
class APIAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        # 调用外部 API
        result = await self.call_external_api(request.get("param"))
        return {"result": result}
    
    async def call_external_api(self, param: str) -> str:
        # 实际实现会调用外部 API
        pass

class TestAPIAgent:
    @pytest.mark.asyncio
    async def test_with_mock(self):
        """使用模拟对象测试"""
        agent = APIAgent()
        
        # 模拟外部 API 调用
        agent.call_external_api = AsyncMock(return_value="mocked_result")
        
        result = await agent.handle({"param": "test"})
        
        assert result["result"] == "mocked_result"
        agent.call_external_api.assert_called_once_with("test")
```

### 桩记忆系统

```python
import pytest
from neuroflow import agent, BaseAgent

@agent(name="memory_agent")
class MemoryAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        self.store_memory("key", "value", "long_term")
        retrieved = self.retrieve_memory("key")
        return {"value": retrieved}

class TestMemoryAgent:
    @pytest.mark.asyncio
    async def test_with_mock_memory(self):
        """使用模拟记忆测试"""
        agent = MemoryAgent()
        
        # 模拟记忆系统
        mock_memory = {
            "key": "mocked_value"
        }
        
        agent.retrieve_memory = lambda k: mock_memory.get(k)
        
        result = await agent.handle({})
        
        assert result["value"] == "mocked_value"
```

## 测试覆盖率

### 生成覆盖率报告

```bash
# 运行测试并生成覆盖率
pytest --cov=sdk/neuroflow --cov-report=html

# 查看 HTML 报告
open htmlcov/index.html
```

### 覆盖率配置

创建 `.coveragerc`:

```ini
[run]
source = sdk/neuroflow
omit = 
    */tests/*
    */__pycache__/*
    */venv/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:

show_missing = True
precision = 2
```

## 持续集成

### GitHub Actions

创建 `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov
    
    - name: Run tests
      run: |
        pytest --cov=sdk/neuroflow --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## 最佳实践

### 1. 测试隔离

```python
# ✅ 每个测试使用独立的 SDK
@pytest.fixture
async def sdk():
    sdk = await NeuroFlowSDK.create()
    yield sdk
    await sdk.shutdown()

# ❌ 避免共享 SDK
@pytest.fixture(scope="module")
async def sdk():
    sdk = await NeuroFlowSDK.create()
    yield sdk
    await sdk.shutdown()
```

### 2. 测试数据准备

```python
@pytest.fixture
def test_data():
    return {
        "valid_request": {"name": "Test"},
        "invalid_request": {},
        "edge_case_request": {"name": ""},
    }

class TestAgent:
    @pytest.mark.asyncio
    async def test_valid_request(self, sdk, test_data):
        agent = MyAgent()
        result = await agent.handle(test_data["valid_request"])
        assert result["success"] is True
```

### 3. 清晰的断言

```python
# ✅ 清晰的断言
assert result["status"] == "success", "Agent should return success status"
assert len(result["data"]) > 0, "Result should contain data"

# ❌ 模糊的断言
assert result
assert result["data"]
```

---

**相关文档**:
- [调试技巧](debugging.md)
- [最佳实践](../best-practices/agent-design.md)
- [故障排除](../troubleshooting/faq.md)
