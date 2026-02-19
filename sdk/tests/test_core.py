"""
NeuroFlow SDK 单元测试套件
"""
import pytest
import asyncio
from neuroflow import NeuroFlowSDK, SDKConfig, get_sdk
from neuroflow.core import agent, tool


class TestNeuroFlowSDK:
    """NeuroFlowSDK 核心类测试"""

    @pytest.mark.asyncio
    async def test_sdk_creation(self):
        """测试 SDK 创建"""
        sdk = await NeuroFlowSDK.create()
        assert sdk.is_initialized
        assert sdk.get_tool_manager() is not None
        await sdk.shutdown()
        assert not sdk.is_initialized

    @pytest.mark.asyncio
    async def test_sdk_initialization_failure(self):
        """测试重复初始化失败"""
        sdk = await NeuroFlowSDK.create()
        with pytest.raises(RuntimeError, match="already initialized"):
            await sdk.initialize()
        await sdk.shutdown()

    @pytest.mark.asyncio
    async def test_sdk_config(self):
        """测试 SDK 配置"""
        config = SDKConfig(
            log_level="debug",
            enable_tracing=False,
            enable_metrics=False
        )
        sdk = await NeuroFlowSDK.create(config)
        assert sdk.config.log_level == "debug"
        assert not sdk.config.enable_tracing
        await sdk.shutdown()

    @pytest.mark.asyncio
    async def test_global_sdk(self):
        """测试全局 SDK 实例"""
        sdk1 = await get_sdk()
        sdk2 = await get_sdk()
        assert sdk1 is sdk2
        await sdk1.shutdown()

    @pytest.mark.asyncio
    async def test_tool_execution(self):
        """测试工具执行"""
        sdk = await NeuroFlowSDK.create()
        
        # 测试内置工具
        result = await sdk.execute_tool("calculate", expression="2 + 3 * 4")
        assert result == 14.0
        
        result = await sdk.execute_tool("echo", message="Hello")
        assert result == "Hello"
        
        await sdk.shutdown()

    @pytest.mark.asyncio
    async def test_custom_tool_registration(self):
        """测试自定义工具注册"""
        sdk = await NeuroFlowSDK.create()
        
        # 注册新工具
        @sdk.get_tool_manager().register_tool(
            name="add",
            description="加法器",
            category="math"
        )
        async def add(a: int, b: int) -> int:
            return a + b
        
        # 执行工具
        result = await sdk.execute_tool("add", a=10, b=20)
        assert result == 30
        
        await sdk.shutdown()

    @pytest.mark.asyncio
    async def test_tool_not_found(self):
        """测试工具未找到错误"""
        sdk = await NeuroFlowSDK.create()
        
        with pytest.raises(ValueError, match="not found"):
            await sdk.execute_tool("nonexistent_tool")
        
        await sdk.shutdown()

    @pytest.mark.asyncio
    async def test_agent_registration(self):
        """测试 Agent 注册"""
        sdk = await NeuroFlowSDK.create()
        
        class TestAgent:
            def __init__(self):
                self.name = "test_agent"
        
        sdk.register_agent("test_agent", TestAgent)
        
        agent_class = sdk.get_agent("test_agent")
        assert agent_class is TestAgent
        
        await sdk.shutdown()

    @pytest.mark.asyncio
    async def test_agent_not_found(self):
        """测试 Agent 未找到错误"""
        sdk = await NeuroFlowSDK.create()
        
        with pytest.raises(KeyError, match="not found"):
            sdk.get_agent("nonexistent_agent")
        
        await sdk.shutdown()


class TestDecorators:
    """装饰器测试"""

    @pytest.mark.asyncio
    async def test_tool_decorator(self):
        """测试 tool 装饰器"""
        sdk = await NeuroFlowSDK.create()
        
        @tool(name="test_tool", description="测试工具")
        async def test_func(value: str) -> str:
            return f"Result: {value}"
        
        # 装饰器应该在 SDK 初始化后注册工具
        # 这里需要手动注册，因为装饰器在 SDK 之前定义
        sdk.get_tool_manager().register_function(
            func=test_func,
            name="test_tool",
            description="测试工具"
        )
        
        result = await sdk.execute_tool("test_tool", value="test")
        assert result == "Result: test"
        
        await sdk.shutdown()

    @pytest.mark.asyncio
    async def test_agent_decorator(self):
        """测试 agent 装饰器"""
        # 注意：agent 装饰器需要 SDK 支持
        # 这里测试基本功能
        from neuroflow.core import agent
        
        @agent(name="decorated_agent", description="测试 Agent")
        class DecoratedAgent:
            def __init__(self):
                self.name = "decorated_agent"
        
        assert DecoratedAgent.name == "decorated_agent"


class TestToolManager:
    """工具管理器测试"""

    @pytest.mark.asyncio
    async def test_tool_manager_creation(self):
        """测试工具管理器创建"""
        from neuroflow.tools import ToolManager
        
        manager = ToolManager()
        assert manager is not None

    @pytest.mark.asyncio
    async def test_tool_registration(self):
        """测试工具注册"""
        from neuroflow.tools import ToolManager
        
        manager = ToolManager()
        
        @manager.register_tool(name="test", description="测试")
        async def test_func():
            return "test"
        
        tools = manager.list_tools()
        assert "test" in tools

    @pytest.mark.asyncio
    async def test_tool_execution_async(self):
        """测试异步工具执行"""
        from neuroflow.tools import ToolManager
        
        manager = ToolManager()
        
        @manager.register_tool(name="async_test")
        async def async_test(value: int) -> int:
            await asyncio.sleep(0.01)
            return value * 2
        
        result = await manager.execute_tool_async("async_test", value=21)
        assert result == 42

    @pytest.mark.asyncio
    async def test_tool_execution_sync(self):
        """测试同步工具执行"""
        from neuroflow.tools import ToolManager
        
        manager = ToolManager()
        
        @manager.register_tool(name="sync_test")
        def sync_test(value: int) -> int:
            return value * 2
        
        result = await manager.execute_tool_async("sync_test", value=21)
        assert result == 42


class TestContext:
    """上下文测试"""

    def test_get_context(self):
        """测试获取上下文"""
        from neuroflow.context import get_context
        
        context = get_context()
        assert context is not None

    def test_context_memory(self):
        """测试上下文记忆"""
        from neuroflow.context import get_context, MemoryType
        
        context = get_context()
        
        # 存储记忆
        context.memory.store(
            key="test_key",
            value="test_value",
            memory_type=MemoryType.SHORT_TERM
        )
        
        # 检索记忆
        value = context.memory.retrieve("test_key")
        assert value == "test_value"


@pytest.mark.asyncio
async def test_concurrent_execution():
    """测试并发执行"""
    sdk = await NeuroFlowSDK.create()
    
    # 并发执行多个工具
    tasks = [
        sdk.execute_tool("calculate", expression=f"{i} + {i}")
        for i in range(10)
    ]
    
    results = await asyncio.gather(*tasks)
    
    for i, result in enumerate(results):
        assert result == i + i
    
    await sdk.shutdown()


@pytest.mark.asyncio
async def test_error_handling():
    """测试错误处理"""
    sdk = await NeuroFlowSDK.create()
    
    # 测试无效表达式
    with pytest.raises(ValueError):
        await sdk.execute_tool("calculate", expression="invalid")
    
    await sdk.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=neuroflow", "--cov-report=html"])
