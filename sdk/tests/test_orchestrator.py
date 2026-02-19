"""
NeuroFlow Python SDK - Orchestrator Tests

测试 LLM 编排器
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from neuroflow.orchestrator import (
    LLMConfig,
    LLMClient,
    Message,
    LLMOrchestrator,
    OrchestratorConfig,
)
from neuroflow.tools import (
    UnifiedToolRegistry,
    ToolDefinition,
    ToolParameter,
    ToolSource,
    LocalFunctionExecutor,
)


class TestLLMClient:
    """测试 LLM 客户端"""
    
    def test_create_llm_config(self):
        """测试创建 LLM 配置"""
        config = LLMConfig(
            provider="openai",
            model="gpt-4",
            temperature=0.5,
        )
        
        assert config.provider.value == "openai"
        assert config.model == "gpt-4"
        assert config.temperature == 0.5
    
    def test_message_creation(self):
        """测试消息创建"""
        msg = Message.user("Hello")
        
        assert msg.role == "user"
        assert msg.content == "Hello"
    
    def test_message_to_dict(self):
        """测试消息转换为字典"""
        msg = Message.assistant("Hi there!")
        
        d = msg.to_dict()
        
        assert d["role"] == "assistant"
        assert d["content"] == "Hi there!"


class TestLLMOrchestrator:
    """测试 LLM 编排器"""
    
    @pytest.fixture
    def mock_llm_client(self):
        """创建模拟 LLM 客户端"""
        client = MagicMock(spec=LLMClient)
        client.config = LLMConfig(provider="openai")
        return client
    
    @pytest.fixture
    def tool_registry(self):
        """创建工具注册表"""
        registry = UnifiedToolRegistry()
        
        # 注册测试工具
        tool = ToolDefinition(
            id="test-add",
            name="add",
            description="加法计算器",
            source=ToolSource.LOCAL_FUNCTION,
            parameters=[
                ToolParameter(
                    name="a",
                    parameter_type="number",
                    description="第一个数",
                    required=True,
                ),
                ToolParameter(
                    name="b",
                    parameter_type="number",
                    description="第二个数",
                    required=True,
                ),
            ],
        )
        registry.register_tool(tool)
        
        # 注册执行器
        executor = LocalFunctionExecutor()
        executor.register_function(
            lambda a, b: a + b,
            tool,
        )
        registry.register_executor(ToolSource.LOCAL_FUNCTION, executor)
        
        return registry
    
    @pytest.mark.asyncio
    async def test_create_orchestrator(self, mock_llm_client, tool_registry):
        """测试创建编排器"""
        orchestrator = LLMOrchestrator(
            llm_client=mock_llm_client,
            tool_registry=tool_registry,
        )
        
        assert orchestrator.llm == mock_llm_client
        assert orchestrator.registry == tool_registry
    
    @pytest.mark.asyncio
    async def test_generate_tools_description(self, mock_llm_client, tool_registry):
        """测试生成工具描述"""
        orchestrator = LLMOrchestrator(
            llm_client=mock_llm_client,
            tool_registry=tool_registry,
            config=OrchestratorConfig(mode="no_tool"),
        )
        
        desc = orchestrator._generate_tools_description()
        
        assert "add" in desc
        assert "加法计算器" in desc
    
    @pytest.mark.asyncio
    async def test_build_messages(self, mock_llm_client, tool_registry):
        """测试构建消息列表"""
        orchestrator = LLMOrchestrator(
            llm_client=mock_llm_client,
            tool_registry=tool_registry,
            config=OrchestratorConfig(mode="no_tool"),
        )
        
        messages = orchestrator._build_messages(
            user_message="Hello",
            history=None,
            system_prompt=None,
        )
        
        assert len(messages) >= 2  # 系统消息 + 用户消息
        assert messages[-1].role == "user"
        assert messages[-1].content == "Hello"
    
    @pytest.mark.asyncio
    async def test_execute_no_tool_calls(
        self, 
        mock_llm_client, 
        tool_registry,
    ):
        """测试执行 without 工具调用"""
        # 模拟 LLM 响应
        from neuroflow.orchestrator import LLMResponse
        
        mock_response = LLMResponse(
            content="Hello! How can I help you?",
            model="gpt-3.5-turbo",
            tool_calls=None,
        )
        mock_llm_client.chat = AsyncMock(return_value=mock_response)
        
        orchestrator = LLMOrchestrator(
            llm_client=mock_llm_client,
            tool_registry=tool_registry,
        )
        
        result = await orchestrator.execute("Hello")
        
        assert result.final_response == "Hello! How can I help you?"
        assert len(result.tool_results) == 0
        assert result.turns_taken == 1


class TestToolIntegration:
    """测试工具集成"""
    
    @pytest.mark.asyncio
    async def test_full_tool_execution(self):
        """测试完整的工具执行流程"""
        # 创建注册表
        registry = UnifiedToolRegistry()
        
        # 创建并注册工具
        tool = ToolDefinition(
            id="test-multiply",
            name="multiply",
            description="乘法计算器",
            source=ToolSource.LOCAL_FUNCTION,
            parameters=[
                ToolParameter("a", "number", "第一个数", required=True),
                ToolParameter("b", "number", "第二个数", required=True),
            ],
        )
        registry.register_tool(tool)
        
        # 创建并注册执行器
        executor = LocalFunctionExecutor()
        executor.register_function(
            lambda a, b: a * b,
            tool,
        )
        registry.register_executor(ToolSource.LOCAL_FUNCTION, executor)
        
        # 执行工具
        from neuroflow.tools import ToolCall
        
        call = ToolCall(
            tool_id="test-multiply",
            tool_name="multiply",
            arguments={"a": 6, "b": 7},
        )
        
        result = await registry.execute(call)
        
        assert result.success is True
        assert result.result == 42


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
