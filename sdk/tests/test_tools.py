"""
NeuroFlow Python SDK - Tool Protocol Tests

测试统一工具协议层
"""

import pytest
import asyncio
from neuroflow.tools import (
    ToolSource,
    ToolExecutionMode,
    ToolParameter,
    ToolDefinition,
    ToolCall,
    ToolResult,
    UnifiedToolRegistry,
    LocalFunctionExecutor,
)


class TestToolDefinition:
    """测试工具定义"""
    
    def test_create_tool_definition(self):
        """创建工具定义"""
        tool = ToolDefinition(
            id="test-1",
            name="calculator",
            description="数学计算器",
            source=ToolSource.LOCAL_FUNCTION,
            parameters=[
                ToolParameter(
                    name="expression",
                    parameter_type="string",
                    description="数学表达式",
                    required=True,
                ),
            ],
        )
        
        assert tool.name == "calculator"
        assert tool.source == ToolSource.LOCAL_FUNCTION
        assert len(tool.parameters) == 1
    
    def test_tool_to_llm_schema(self):
        """测试转换为 LLM Schema"""
        tool = ToolDefinition(
            id="test-2",
            name="greet",
            description="问候某人",
            source=ToolSource.LOCAL_FUNCTION,
            parameters=[
                ToolParameter(
                    name="name",
                    parameter_type="string",
                    description="人名",
                    required=True,
                    default_value="World",
                ),
            ],
        )
        
        schema = tool.to_llm_schema()
        
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "greet"
        assert "parameters" in schema["function"]
        assert "name" in schema["function"]["parameters"]["properties"]


class TestToolCall:
    """测试工具调用"""
    
    def test_create_tool_call(self):
        """创建工具调用"""
        call = ToolCall(
            tool_id="test-1",
            tool_name="calculator",
            arguments={"expression": "1+1"},
        )
        
        assert call.tool_name == "calculator"
        assert call.arguments == {"expression": "1+1"}
        assert call.call_id is not None
    
    def test_tool_call_default_timeout(self):
        """测试默认超时"""
        call = ToolCall(
            tool_id="test-2",
            tool_name="test",
            arguments={},
        )
        
        assert call.timeout_ms == 30000


class TestToolResult:
    """测试工具结果"""
    
    def test_success_result(self):
        """测试成功结果"""
        result = ToolResult(
            call_id="call-1",
            success=True,
            result={"value": 42},
        )
        
        assert result.success is True
        assert result.result["value"] == 42
        assert result.error is None
    
    def test_error_result(self):
        """测试错误结果"""
        result = ToolResult(
            call_id="call-2",
            success=False,
            result=None,
            error="Something went wrong",
        )
        
        assert result.success is False
        assert result.error == "Something went wrong"
    
    def test_to_llm_message(self):
        """测试转换为 LLM 消息"""
        result = ToolResult(
            call_id="call-3",
            success=True,
            result="Hello",
        )
        
        message = result.to_llm_message()
        
        assert message["role"] == "tool"
        assert message["tool_call_id"] == "call-3"


class TestUnifiedToolRegistry:
    """测试统一工具注册表"""
    
    def test_register_tool(self):
        """测试注册工具"""
        registry = UnifiedToolRegistry()
        
        tool = ToolDefinition(
            id="test-1",
            name="echo",
            description="回显输入",
            source=ToolSource.LOCAL_FUNCTION,
            parameters=[],
        )
        
        registry.register_tool(tool)
        
        assert registry.count() == 1
        assert registry.get_tool("echo") is not None
    
    def test_list_tools(self):
        """测试列出工具"""
        registry = UnifiedToolRegistry()
        
        for i in range(3):
            tool = ToolDefinition(
                id=f"test-{i}",
                name=f"tool_{i}",
                description=f"工具 {i}",
                source=ToolSource.LOCAL_FUNCTION,
                parameters=[],
            )
            registry.register_tool(tool)
        
        tools = registry.list_tools()
        assert len(tools) == 3
    
    def test_get_all_llm_schemas(self):
        """测试获取所有 LLM Schema"""
        registry = UnifiedToolRegistry()
        
        tool = ToolDefinition(
            id="test-1",
            name="test",
            description="测试工具",
            source=ToolSource.LOCAL_FUNCTION,
            parameters=[],
        )
        registry.register_tool(tool)
        
        schemas = registry.get_all_llm_schemas()
        assert len(schemas) == 1
        assert schemas[0]["function"]["name"] == "test"


class TestLocalFunctionExecutor:
    """测试本地函数执行器"""
    
    @pytest.mark.asyncio
    async def test_execute_sync_function(self):
        """测试执行同步函数"""
        executor = LocalFunctionExecutor()
        
        # 注册同步函数
        def add(a: int, b: int) -> int:
            return a + b
        
        tool = ToolDefinition(
            id="test-add",
            name="add",
            description="加法",
            source=ToolSource.LOCAL_FUNCTION,
            parameters=[],
        )
        executor.register_function(add, tool)
        
        # 执行
        call = ToolCall(
            tool_id="test-add",
            tool_name="add",
            arguments={"a": 10, "b": 20},
        )
        
        result = await executor.execute(call)
        
        assert result.success is True
        assert result.result == 30
    
    @pytest.mark.asyncio
    async def test_execute_async_function(self):
        """测试执行异步函数"""
        executor = LocalFunctionExecutor()
        
        # 注册异步函数
        async def greet(name: str) -> str:
            await asyncio.sleep(0.01)  # 模拟异步操作
            return f"Hello, {name}!"
        
        tool = ToolDefinition(
            id="test-greet",
            name="greet",
            description="问候",
            source=ToolSource.LOCAL_FUNCTION,
            parameters=[],
        )
        executor.register_function(greet, tool)
        
        # 执行
        call = ToolCall(
            tool_id="test-greet",
            tool_name="greet",
            arguments={"name": "World"},
        )
        
        result = await executor.execute(call)
        
        assert result.success is True
        assert "Hello" in result.result
    
    @pytest.mark.asyncio
    async def test_execute_not_found(self):
        """测试执行不存在的工具"""
        executor = LocalFunctionExecutor()
        
        call = ToolCall(
            tool_id="test",
            tool_name="nonexistent",
            arguments={},
        )
        
        result = await executor.execute(call)
        
        assert result.success is False
        assert "not found" in result.error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
