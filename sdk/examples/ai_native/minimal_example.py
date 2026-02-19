"""
AI Native Agent 最小示例

展示如何使用新的 AI Native Agent:
1. 创建 Agent
2. 注册工具
3. 处理请求 - LLM 自主决定是否使用工具

运行:
    python examples/ai_native/minimal_example.py
"""

import asyncio
import os
from neuroflow import AINativeAgent, AINativeAgentConfig, LLMConfig


async def main():
    # 检查 API Key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  未设置 OPENAI_API_KEY 环境变量")
        print("请设置：export OPENAI_API_KEY=your-api-key")
        print("\n使用模拟模式运行...\n")
        
        # 创建不使用 LLM 的示例
        await demo_without_llm()
        return
    
    print("🚀 创建 AI Native Agent...\n")
    
    # 创建 Agent
    agent = AINativeAgent(
        AINativeAgentConfig(
            name="assistant",
            description="一个智能助手",
            llm_config=LLMConfig(
                provider="openai",
                model="gpt-3.5-turbo",
            ),
        )
    )
    
    # 注册工具
    @agent.tool(name="greet", description="问候某人")
    async def greet(name: str) -> str:
        return f"Hello, {name}! Welcome to NeuroFlow!"
    
    @agent.tool(name="calculate", description="简单的数学计算器")
    async def calculate(expression: str) -> float:
        """计算数学表达式"""
        allowed = set('0123456789+-*/(). ')
        if not all(c in allowed for c in expression):
            raise ValueError("Invalid characters in expression")
        return float(eval(expression, {"__builtins__": {}}, {}))
    
    print(f"✓ 已注册工具：{agent.list_available_tools()}\n")
    
    # 测试 1: 需要工具调用的请求
    print("=" * 50)
    print("测试 1: 需要工具调用")
    print("=" * 50)
    
    result = await agent.handle("帮我问候张三")
    print(f"用户：帮我问候张三")
    print(f"助手：{result['response']}")
    print(f"使用的工具：{len(result['tool_results'])} 个")
    print()
    
    # 测试 2: 需要工具调用的请求
    print("=" * 50)
    print("测试 2: 数学计算")
    print("=" * 50)
    
    result = await agent.handle("计算 123 + 456 等于多少？")
    print(f"用户：计算 123 + 456 等于多少？")
    print(f"助手：{result['response']}")
    print(f"使用的工具：{len(result['tool_results'])} 个")
    print()
    
    # 测试 3: 不需要工具调用的请求
    print("=" * 50)
    print("测试 3: 普通对话")
    print("=" * 50)
    
    result = await agent.handle("你好，请介绍一下你自己")
    print(f"用户：你好，请介绍一下你自己")
    print(f"助手：{result['response']}")
    print(f"使用的工具：{len(result['tool_results'])} 个")
    print()


async def demo_without_llm():
    """不使用 LLM 的演示模式"""
    print("创建 Agent (无 LLM 配置)...")
    
    agent = AINativeAgent(
        AINativeAgentConfig(
            name="demo_agent",
            description="演示 Agent",
        )
    )
    
    # 注册工具
    @agent.tool(name="greet", description="问候某人")
    async def greet(name: str) -> str:
        return f"Hello, {name}! Welcome to NeuroFlow!"
    
    @agent.tool(name="calculate", description="简单的数学计算器")
    async def calculate(expression: str) -> float:
        allowed = set('0123456789+-*/(). ')
        if not all(c in allowed for c in expression):
            raise ValueError("Invalid characters in expression")
        return float(eval(expression, {"__builtins__": {}}, {}))
    
    print(f"✓ 已注册工具：{agent.list_available_tools()}")
    print("\n提示：设置 OPENAI_API_KEY 环境变量以启用完整的 AI Native 功能")
    
    # 直接调用工具
    print("\n直接调用工具演示:")
    result = await agent.execute_tool("greet", name="开发者")
    print(f"greet('开发者') = {result}")
    
    result = await agent.execute_tool("calculate", expression="123+456")
    print(f"calculate('123+456') = {result}")


if __name__ == "__main__":
    asyncio.run(main())
