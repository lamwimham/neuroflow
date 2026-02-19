# Agent 设计最佳实践

本文档总结了设计和开发 NeuroFlow Agent 的最佳实践。

## 设计原则

### 1. 单一职责原则 (SRP)

每个 Agent 只负责一个明确的功能领域。

```python
# ❌ 避免：过于复杂的 Agent
@agent(name="do_everything_agent")
class DoEverythingAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        # 处理用户认证
        # 处理数据清洗
        # 处理数据分析
        # 生成报告
        # 发送邮件
        pass

# ✅ 推荐：职责单一的 Agent
@agent(name="data_cleaner")
class DataCleanerAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        return {"cleaned_data": await self.clean(request.get("data"))}

@agent(name="data_analyzer")
class DataAnalyzerAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        return {"analysis": await self.analyze(request.get("data"))}

@agent(name="report_generator")
class ReportGeneratorAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        return {"report": await self.generate(request.get("analysis"))}
```

**优势**:
- 🎯 更容易理解和维护
- 🧪 更容易测试
- 🔄 更容易复用
- 🐛 更容易调试

### 2. 开闭原则 (OCP)

Agent 应该对扩展开放，对修改关闭。

```python
# ✅ 推荐：支持扩展的 Agent
@agent(name="processor")
class ProcessorAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        processor_type = request.get("type", "default")
        
        # 使用策略模式
        processor = self.get_processor(processor_type)
        return await processor.process(request)
    
    def get_processor(self, processor_type: str):
        processors = {
            "text": TextProcessor(),
            "image": ImageProcessor(),
            "audio": AudioProcessor(),
        }
        return processors.get(processor_type, DefaultProcessor())

# 添加新处理器不需要修改现有代码
class VideoProcessor:
    async def process(self, request: dict) -> dict:
        # 处理视频
        pass
```

### 3. 依赖倒置原则 (DIP)

依赖抽象而非具体实现。

```python
from abc import ABC, abstractmethod

# ✅ 推荐：依赖抽象
class StorageInterface(ABC):
    @abstractmethod
    async def save(self, key: str, value: any):
        pass

class DatabaseStorage(StorageInterface):
    async def save(self, key: str, value: any):
        # 保存到数据库
        pass

class CacheStorage(StorageInterface):
    async def save(self, key: str, value: any):
        # 保存到缓存
        pass

@agent(name="storage_agent")
class StorageAgent(BaseAgent):
    def __init__(self, storage: StorageInterface):
        self.storage = storage  # 依赖抽象
    
    async def handle(self, request: dict) -> dict:
        await self.storage.save(request["key"], request["value"])
        return {"status": "saved"}
```

## 代码组织

### 1. 清晰的目录结构

```
project/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py      # 基础 Agent 类
│   ├── data_agent.py      # 数据处理 Agent
│   └── api_agent.py       # API 集成 Agent
├── tools/
│   ├── __init__.py
│   ├── data_tools.py      # 数据工具
│   └── api_tools.py       # API 工具
├── utils/
│   ├── __init__.py
│   └── helpers.py         # 辅助函数
├── config/
│   └── settings.py        # 配置
├── tests/
│   ├── test_agents.py
│   └── test_tools.py
└── main.py
```

### 2. 模块化设计

```python
# agents/__init__.py
from .data_agent import DataAgent
from .api_agent import APIAgent

__all__ = ["DataAgent", "APIAgent"]

# tools/__init__.py
from .data_tools import clean_data, analyze_data
from .api_tools import http_get, http_post

__all__ = ["clean_data", "analyze_data", "http_get", "http_post"]
```

### 3. 配置分离

```python
# config/settings.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    log_level: str = "info"
    server_url: str = "http://localhost:8080"
    max_retries: int = 3
    timeout_secs: int = 30
    
    class Config:
        env_prefix = "NEUROFLOW_"

settings = Settings()
```

## 错误处理

### 1. 分层错误处理

```python
class AgentError(Exception):
    """Agent 基础错误"""
    pass

class ValidationError(AgentError):
    """验证错误"""
    pass

class ProcessingError(AgentError):
    """处理错误"""
    pass

class ExternalServiceError(AgentError):
    """外部服务错误"""
    pass

@agent(name="robust_agent")
class RobustAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        try:
            self._validate_request(request)  # 可能抛出 ValidationError
            result = await self._process(request)  # 可能抛出 ProcessingError
            return {"success": True, "data": result}
        
        except ValidationError as e:
            self.context.logger.warning(f"Validation failed: {e}")
            return {"success": False, "error": "validation_error", "message": str(e)}
        
        except ProcessingError as e:
            self.context.logger.error(f"Processing failed: {e}")
            return {"success": False, "error": "processing_error", "message": str(e)}
        
        except ExternalServiceError as e:
            self.context.logger.error(f"External service failed: {e}")
            return {"success": False, "error": "service_unavailable"}
        
        except Exception as e:
            self.context.logger.exception(f"Unexpected error: {e}")
            return {"success": False, "error": "internal_error"}
```

### 2. 重试机制

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@agent(name="retry_agent")
class RetryAgent(BaseAgent):
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def unreliable_operation(self, param: str) -> str:
        # 可能失败的操作
        pass
    
    async def handle(self, request: dict) -> dict:
        try:
            result = await self.unreliable_operation(request.get("param"))
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
```

### 3. 降级策略

```python
@agent(name="fallback_agent")
class FallbackAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        try:
            # 尝试主要服务
            result = await self.call_primary_service(request)
            return {"source": "primary", "data": result}
        
        except Exception as e:
            self.context.logger.warning(f"Primary service failed: {e}")
            
            # 降级到备用服务
            result = await self.call_fallback_service(request)
            return {"source": "fallback", "data": result}
```

## 性能优化

### 1. 并发执行

```python
import asyncio

@agent(name="concurrent_agent")
class ConcurrentAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        tasks = request.get("tasks", [])
        
        # 并发执行
        results = await asyncio.gather(*[
            self.process_task(task) for task in tasks
        ], return_exceptions=True)
        
        # 处理结果
        success_results = [r for r in results if not isinstance(r, Exception)]
        errors = [str(r) for r in results if isinstance(r, Exception)]
        
        return {
            "results": success_results,
            "errors": errors,
            "success_count": len(success_results),
            "error_count": len(errors)
        }
```

### 2. 缓存策略

```python
from functools import lru_cache
import hashlib

@agent(name="cached_agent")
class CachedAgent(BaseAgent):
    @lru_cache(maxsize=100)
    async def expensive_operation(self, param: str) -> str:
        # 耗时操作
        return f"Result for {param}"
    
    async def handle(self, request: dict) -> dict:
        param = request.get("param")
        
        # 使用缓存
        result = await self.expensive_operation(param)
        
        return {"result": result, "cached": True}
```

### 3. 批量处理

```python
@agent(name="batch_agent")
class BatchAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        items = request.get("items", [])
        batch_size = request.get("batch_size", 10)
        
        # 分批处理
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_result = await self.process_batch(batch)
            results.extend(batch_result)
        
        return {"results": results, "total": len(results)}
    
    async def process_batch(self, batch: list) -> list:
        # 批量处理逻辑
        return [item * 2 for item in batch]
```

## 日志和监控

### 1. 结构化日志

```python
import json

@agent(name="logged_agent")
class LoggedAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        # 记录请求
        self.context.logger.info(
            "Request received",
            extra={
                "agent": self.name,
                "request_id": request.get("request_id"),
                "action": request.get("action")
            }
        )
        
        # 处理逻辑
        result = await self.process(request)
        
        # 记录响应
        self.context.logger.info(
            "Request processed",
            extra={
                "agent": self.name,
                "request_id": request.get("request_id"),
                "result_size": len(str(result))
            }
        )
        
        return result
```

### 2. 性能监控

```python
import time
from functools import wraps

def timed(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        try:
            return await func(*args, **kwargs)
        finally:
            elapsed = time.time() - start
            func_name = func.__name__
            print(f"{func_name} took {elapsed:.3f}s")
    return wrapper

@agent(name="monitored_agent")
class MonitoredAgent(BaseAgent):
    @timed
    async def handle(self, request: dict) -> dict:
        return await self.process(request)
```

### 3. 指标收集

```python
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter('agent_requests_total', 'Total requests')
REQUEST_DURATION = Histogram('agent_request_duration_seconds', 'Request duration')

@agent(name="metrics_agent")
class MetricsAgent(BaseAgent):
    @REQUEST_DURATION.time()
    async def handle(self, request: dict) -> dict:
        REQUEST_COUNT.inc()
        return await self.process(request)
```

## 测试策略

### 1. 单元测试

```python
import pytest
from neuroflow import NeuroFlowSDK

@pytest.mark.asyncio
async def test_agent_basic():
    sdk = await NeuroFlowSDK.create()
    agent = MyAgent(name="test")
    
    result = await agent.handle({"input": "test"})
    
    assert result["success"] is True
    assert "data" in result
    
    await sdk.shutdown()
```

### 2. 集成测试

```python
@pytest.mark.asyncio
async def test_agent_integration():
    sdk = await NeuroFlowSDK.create()
    
    # 注册 Agent
    agent = MyAgent(name="test")
    sdk.register_agent("test", MyAgent)
    
    # 测试工具调用
    tool_result = await sdk.execute_tool("test_tool", param="value")
    assert tool_result is not None
    
    # 测试 Agent 执行
    agent_result = await agent.handle({"test": "data"})
    assert agent_result["success"] is True
    
    await sdk.shutdown()
```

### 3. 性能测试

```python
import pytest
import time

@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_agent_performance():
    agent = MyAgent(name="benchmark")
    
    start = time.time()
    for _ in range(100):
        await agent.handle({"input": "test"})
    elapsed = time.time() - start
    
    avg_time = elapsed / 100
    assert avg_time < 0.1  # 平均响应时间 < 100ms
```

## 安全实践

### 1. 输入验证

```python
from pydantic import BaseModel, validator

class RequestModel(BaseModel):
    user_id: str
    action: str
    data: dict
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not v or len(v) > 100:
            raise ValueError("Invalid user_id")
        return v
    
    @validator('action')
    def validate_action(cls, v):
        allowed_actions = ["create", "read", "update", "delete"]
        if v not in allowed_actions:
            raise ValueError(f"Action must be one of {allowed_actions}")
        return v

@agent(name="validated_agent")
class ValidatedAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        # 验证输入
        try:
            validated = RequestModel(**request)
        except ValueError as e:
            return {"success": False, "error": str(e)}
        
        # 处理验证后的请求
        return await self.process(validated)
```

### 2. 权限检查

```python
from neuroflow import PermissionLevel

@agent(name="secure_agent")
class SecureAgent(BaseAgent):
    async def handle(self, request: dict) -> dict:
        user_permissions = request.get("permissions", [])
        
        # 检查权限
        required_permission = PermissionLevel.WRITE
        if not self.has_permission(user_permissions, required_permission):
            return {"success": False, "error": "Permission denied"}
        
        # 执行操作
        return await self.process(request)
    
    def has_permission(self, user_perms: list, required: PermissionLevel) -> bool:
        # 权限检查逻辑
        return required in user_perms or PermissionLevel.ADMIN in user_perms
```

### 3. 敏感数据保护

```python
import os
from cryptography.fernet import Fernet

@agent(name="secure_storage_agent")
class SecureStorageAgent(BaseAgent):
    def __init__(self):
        self.encryption_key = os.getenv("ENCRYPTION_KEY")
        self.cipher = Fernet(self.encryption_key) if self.encryption_key else None
    
    async def handle(self, request: dict) -> dict:
        sensitive_data = request.get("sensitive_data")
        
        # 加密敏感数据
        if sensitive_data and self.cipher:
            encrypted = self.cipher.encrypt(sensitive_data.encode())
            self.store_memory("encrypted_data", encrypted, "long_term")
        
        return {"success": True}
```

## 文档规范

### 1. Agent 文档

```python
@agent(name="documented_agent", description="数据处理 Agent")
class DocumentedAgent(BaseAgent):
    """
    数据处理 Agent
    
    功能:
    - 数据清洗
    - 数据转换
    - 数据分析
    
    输入格式:
    {
        "data": List[Dict],  # 输入数据
        "operation": str,     # 操作类型
        "options": Dict       # 可选配置
    }
    
    输出格式:
    {
        "success": bool,      # 是否成功
        "result": Dict,       # 处理结果
        "error": str          # 错误信息 (如果失败)
    }
    
    示例:
    >>> agent = DocumentedAgent()
    >>> result = await agent.handle({
    ...     "data": [{"value": 1}],
    ...     "operation": "clean"
    ... })
    """
    
    async def handle(self, request: dict) -> dict:
        """
        处理请求
        
        Args:
            request: 请求字典
        
        Returns:
            响应字典
        
        Raises:
            ValueError: 当输入无效时
            ProcessingError: 当处理失败时
        """
        pass
```

---

**相关文档**:
- [构建 Agent](../guides/building-agents.md)
- [性能优化](performance.md)
- [安全实践](security.md)
