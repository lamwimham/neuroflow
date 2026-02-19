"""
NeuroFlow 集成测试
测试完整的 Agent 工作流程
"""
import pytest
import asyncio
import time
from neuroflow import NeuroFlowSDK, agent, tool


class TestIntegrationAgentWorkflow:
    """Agent 工作流集成测试"""

    @pytest.mark.asyncio
    async def test_complete_agent_lifecycle(self):
        """测试完整的 Agent 生命周期"""
        # 创建 SDK
        sdk = await NeuroFlowSDK.create()
        
        # 定义工具
        @sdk.get_tool_manager().register_tool(
            name="process_data",
            description="处理数据"
        )
        async def process_data(data: str) -> str:
            return f"Processed: {data}"
        
        # 定义 Agent
        class DataProcessorAgent:
            def __init__(self, sdk):
                self.sdk = sdk
                self.name = "data_processor"
            
            async def handle(self, request: dict) -> dict:
                data = request.get("data", "")
                result = await self.sdk.execute_tool("process_data", data=data)
                return {"result": result, "agent": self.name}
        
        # 创建 Agent 实例
        agent_instance = DataProcessorAgent(sdk)
        
        # 处理请求
        result = await agent_instance.handle({"data": "test_data"})
        
        assert result["result"] == "Processed: test_data"
        assert result["agent"] == "data_processor"
        
        await sdk.shutdown()

    @pytest.mark.asyncio
    async def test_multi_agent_collaboration(self):
        """测试多 Agent 协作"""
        sdk = await NeuroFlowSDK.create()
        
        # 创建多个工具
        @sdk.get_tool_manager().register_tool(name="analyze")
        async def analyze(text: str) -> str:
            return f"Analyzed: {text}"
        
        @sdk.get_tool_manager().register_tool(name="summarize")
        async def summarize(text: str) -> str:
            return f"Summary: {text[:20]}..."
        
        # Agent 1: 分析器
        class AnalyzerAgent:
            def __init__(self, sdk):
                self.sdk = sdk
            
            async def analyze(self, text: str) -> str:
                return await self.sdk.execute_tool("analyze", text=text)
        
        # Agent 2: 总结器
        class SummarizerAgent:
            def __init__(self, sdk):
                self.sdk = sdk
            
            async def summarize(self, text: str) -> str:
                return await self.sdk.execute_tool("summarize", text=text)
        
        # 协作流程
        analyzer = AnalyzerAgent(sdk)
        summarizer = SummarizerAgent(sdk)
        
        text = "This is a long text that needs analysis and summarization"
        
        # 先分析
        analysis = await analyzer.analyze(text)
        
        # 再总结
        summary = await summarizer.summarize(analysis)
        
        assert "Analyzed:" in analysis
        assert "Summary:" in summary
        
        await sdk.shutdown()

    @pytest.mark.asyncio
    async def test_tool_chaining(self):
        """测试工具链"""
        sdk = await NeuroFlowSDK.create()
        
        # 创建工具链
        @sdk.get_tool_manager().register_tool(name="step1")
        async def step1(input: str) -> str:
            return f"Step1({input})"
        
        @sdk.get_tool_manager().register_tool(name="step2")
        async def step2(input: str) -> str:
            return f"Step2({input})"
        
        @sdk.get_tool_manager().register_tool(name="step3")
        async def step3(input: str) -> str:
            return f"Step3({input})"
        
        # 执行工具链
        result1 = await sdk.execute_tool("step1", input="start")
        result2 = await sdk.execute_tool("step2", input=result1)
        result3 = await sdk.execute_tool("step3", input=result2)
        
        assert result3 == "Step3(Step2(Step1(start)))"
        
        await sdk.shutdown()


class TestIntegrationPerformance:
    """性能集成测试"""

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """测试并发请求处理"""
        sdk = await NeuroFlowSDK.create()
        
        # 创建 100 个并发请求
        async def make_request(i: int) -> dict:
            result = await sdk.execute_tool("echo", message=f"Request {i}")
            return {"index": i, "result": result}
        
        tasks = [make_request(i) for i in range(100)]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time
        
        # 验证所有请求都成功
        assert len(results) == 100
        for i, result in enumerate(results):
            assert result["result"] == f"Request {i}"
        
        # 性能检查：100 个请求应在 5 秒内完成
        assert elapsed < 5.0, f"Too slow: {elapsed:.2f}s"
        
        await sdk.shutdown()

    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """测试内存使用"""
        import tracemalloc
        tracemalloc.start()
        
        sdk = await NeuroFlowSDK.create()
        
        # 执行多次工具调用
        for _ in range(50):
            await sdk.execute_tool("calculate", expression="1 + 1")
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # 内存使用应小于 50MB
        assert peak < 50 * 1024 * 1024, f"Peak memory too high: {peak / 1024 / 1024:.2f}MB"
        
        await sdk.shutdown()

    @pytest.mark.asyncio
    async def test_sandbox_isolation(self):
        """测试沙箱隔离"""
        sdk = await NeuroFlowSDK.create()
        
        # 创建两个独立的执行上下文
        @sdk.get_tool_manager().register_tool(name="set_var")
        async def set_var(name: str, value: str) -> str:
            # 模拟设置变量
            return f"{name}={value}"
        
        @sdk.get_tool_manager().register_tool(name="get_var")
        async def get_var(name: str) -> str:
            # 模拟获取变量
            return f"{name}?"
        
        # 设置变量
        await sdk.execute_tool("set_var", name="x", value="10")
        
        # 获取变量 (应该不受影响)
        result = await sdk.execute_tool("get_var", name="x")
        
        # 验证隔离
        assert result == "x?"  # 不应该是 "10"
        
        await sdk.shutdown()


class TestIntegrationErrorHandling:
    """错误处理集成测试"""

    @pytest.mark.asyncio
    async def test_tool_exception_handling(self):
        """测试工具异常处理"""
        sdk = await NeuroFlowSDK.create()
        
        @sdk.get_tool_manager().register_tool(name="failing_tool")
        async def failing_tool() -> str:
            raise ValueError("Intentional failure")
        
        with pytest.raises(RuntimeError, match="Error executing tool"):
            await sdk.execute_tool("failing_tool")
        
        # 验证 SDK 仍然可用
        result = await sdk.execute_tool("echo", message="Still working")
        assert result == "Still working"
        
        await sdk.shutdown()

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """测试超时处理"""
        sdk = await NeuroFlowSDK.create()
        
        @sdk.get_tool_manager().register_tool(name="slow_tool")
        async def slow_tool() -> str:
            await asyncio.sleep(10)  # 故意很慢
            return "Done"
        
        # 设置超时
        try:
            await asyncio.wait_for(
                sdk.execute_tool("slow_tool"),
                timeout=2.0
            )
            assert False, "Should have timed out"
        except asyncio.TimeoutError:
            pass  # 预期
        
        # 验证 SDK 仍然可用
        result = await sdk.execute_tool("echo", message="Recovery")
        assert result == "Recovery"
        
        await sdk.shutdown()


class TestIntegrationRealWorldScenarios:
    """真实场景集成测试"""

    @pytest.mark.asyncio
    async def test_data_processing_pipeline(self):
        """测试数据处理流水线"""
        sdk = await NeuroFlowSDK.create()
        
        # 定义流水线工具
        @sdk.get_tool_manager().register_tool(name="extract")
        async def extract(data: str) -> list:
            return data.split(",")
        
        @sdk.get_tool_manager().register_tool(name="transform")
        async def transform(items: list) -> list:
            return [item.strip().upper() for item in items]
        
        @sdk.get_tool_manager().register_tool(name="load")
        async def load(items: list) -> str:
            return "\n".join(items)
        
        # ETL 流水线
        raw_data = "apple, banana, cherry, date"
        
        extracted = await sdk.execute_tool("extract", data=raw_data)
        transformed = await sdk.execute_tool("transform", items=extracted)
        loaded = await sdk.execute_tool("load", items=transformed)
        
        assert "APPLE" in loaded
        assert "BANANA" in loaded
        
        await sdk.shutdown()

    @pytest.mark.asyncio
    async def test_math_agent(self):
        """测试数学计算 Agent"""
        sdk = await NeuroFlowSDK.create()
        
        # 定义数学工具
        @sdk.get_tool_manager().register_tool(name="add")
        async def add(a: float, b: float) -> float:
            return a + b
        
        @sdk.get_tool_manager().register_tool(name="multiply")
        async def multiply(a: float, b: float) -> float:
            return a * b
        
        @sdk.get_tool_manager().register_tool(name="average")
        async def average(numbers: list) -> float:
            return sum(numbers) / len(numbers)
        
        # 复杂计算
        result1 = await sdk.execute_tool("add", a=10, b=20)
        result2 = await sdk.execute_tool("multiply", a=result1, b=2)
        
        # 计算平均
        numbers = [result1, result2, 50]
        avg = await sdk.execute_tool("average", numbers=numbers)
        
        assert result1 == 30
        assert result2 == 60
        assert avg == (30 + 60 + 50) / 3
        
        await sdk.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
