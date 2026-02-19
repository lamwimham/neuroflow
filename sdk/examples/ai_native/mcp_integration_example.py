"""
MCP (Model Context Protocol) 集成示例

展示如何集成 MCP 服务:
1. 发现 MCP 工具
2. 调用 MCP 工具
3. 结合本地工具和 MCP 工具

运行:
    python examples/ai_native/mcp_integration_example.py
"""

import asyncio
import os
from neuroflow import AINativeAgent, LLMConfig, MCPToolExecutor, UnifiedToolRegistry, ToolSource


async def demo_mcp_discovery():
    """演示 MCP 工具发现"""
    print("\n" + "="*60)
    print("示例 1: MCP 工具发现")
    print("="*60 + "\n")
    
    # 创建 MCP 执行器
    mcp_executor = MCPToolExecutor(
        mcp_endpoint=os.getenv("MCP_ENDPOINT", "http://localhost:8081")
    )
    
    print(f"MCP 服务端点：{mcp_executor._mcp_endpoint}")
    
    # 尝试发现工具
    try:
        tools = await mcp_executor.discover_tools()
        print(f"发现 {len(tools)} 个 MCP 工具:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
    except Exception as e:
        print(f"⚠️  无法连接到 MCP 服务器：{e}")
        print("请确保 MCP 服务器正在运行")
        
        # 创建模拟工具用于演示
        from neuroflow import ToolDefinition, ToolParameter
        
        mock_tools = [
            ToolDefinition(
                id="mcp:embedding",
                name="get_embeddings",
                description="获取文本嵌入向量",
                source=ToolSource.MCP_SERVER,
                parameters=[
                    ToolParameter(
                        name="texts",
                        parameter_type="array",
                        description="文本列表",
                        required=True,
                    ),
                    ToolParameter(
                        name="model",
                        parameter_type="string",
                        description="嵌入模型",
                        required=False,
                        default_value="sentence-transformers/all-MiniLM-L6-v2",
                    ),
                ],
                metadata={"server_url": "http://localhost:8081"},
            ),
            ToolDefinition(
                id="mcp:generate",
                name="generate_text",
                description="生成文本",
                source=ToolSource.MCP_SERVER,
                parameters=[
                    ToolParameter(
                        name="prompt",
                        parameter_type="string",
                        description="提示词",
                        required=True,
                    ),
                    ToolParameter(
                        name="max_length",
                        parameter_type="number",
                        description="最大长度",
                        required=False,
                        default_value=100,
                    ),
                ],
                metadata={"server_url": "http://localhost:8081"},
            ),
        ]
        
        print(f"\n使用 {len(mock_tools)} 个模拟 MCP 工具进行演示:")
        for tool in mock_tools:
            print(f"  - {tool.name}: {tool.description}")
        
        return mock_tools
    
    return tools


async def demo_mixed_tools():
    """演示混合使用本地工具和 MCP 工具"""
    print("\n" + "="*60)
    print("示例 2: 混合工具使用")
    print("="*60 + "\n")
    
    # 创建 Agent
    agent = AINativeAgent(
        name="hybrid_assistant",
        description="混合助手",
        llm_config=LLMConfig(
            provider="openai",
            model="gpt-4",
        ) if os.getenv("OPENAI_API_KEY") else None,
    )
    
    # 注册本地工具
    @agent.tool(name="process_locally", description="本地处理数据")
    async def process_locally(data: str) -> dict:
        """本地数据处理"""
        return {
            "processed": True,
            "length": len(data),
            "uppercase": data.upper(),
        }
    
    # 尝试添加 MCP 工具
    mcp_tools = await demo_mcp_discovery()
    
    # 手动注册模拟 MCP 工具到注册表
    for tool_def in mcp_tools:
        agent.tool_registry.register_tool(tool_def)
    
    print(f"\n总可用工具：{agent.list_available_tools()}")
    
    if os.getenv("OPENAI_API_KEY"):
        # 测试：让 LLM 决定使用哪个工具
        result = await agent.handle(
            "请处理这段文本：'Hello World'"
        )
        print(f"\n用户：请处理这段文本：'Hello World'")
        print(f"助手：{result['response']}")
        print(f"使用的工具：{len(result['tool_results'])} 个")
    else:
        print("\n⚠️  需要 OPENAI_API_KEY 才能运行完整示例")
        
        # 演示本地工具调用
        result = await agent.execute_tool("process_locally", data="Hello World")
        print(f"\n本地工具结果：{result}")


async def demo_mcp_embedding():
    """演示 MCP 嵌入服务"""
    print("\n" + "="*60)
    print("示例 3: 文本嵌入")
    print("="*60 + "\n")
    
    # 创建 Agent
    agent = AINativeAgent(
        name="embedding_assistant",
        description="嵌入助手",
    )
    
    # 添加模拟嵌入工具
    @agent.tool(name="embed_texts", description="将文本转换为向量")
    async def embed_texts(texts: list, model: str = "demo") -> list:
        """模拟文本嵌入"""
        import random
        # 生成随机向量 (模拟)
        return [
            [random.random() for _ in range(128)]
            for _ in texts
        ]
    
    @agent.tool(name="calculate_similarity", description="计算向量相似度")
    async def calculate_similarity(vec1: list, vec2: list) -> float:
        """计算余弦相似度"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)
    
    # 测试
    texts = ["Hello World", "Hi there", "Goodbye"]
    
    print(f"文本：{texts}")
    
    embeddings = await agent.execute_tool("embed_texts", texts=texts)
    print(f"\n生成的嵌入向量：{len(embeddings)} 个")
    print(f"每个向量维度：{len(embeddings[0])}")
    
    # 计算相似度
    similarity = await agent.execute_tool(
        "calculate_similarity",
        vec1=embeddings[0],
        vec2=embeddings[1]
    )
    print(f"\n'Hello World' 和 'Hi there' 的相似度：{similarity:.4f}")
    
    similarity2 = await agent.execute_tool(
        "calculate_similarity",
        vec1=embeddings[0],
        vec2=embeddings[2]
    )
    print(f"'Hello World' 和 'Goodbye' 的相似度：{similarity2:.4f}")


async def main():
    """运行所有示例"""
    print("🔌 MCP 集成示例")
    print("="*60)
    
    if not os.getenv("MCP_ENDPOINT"):
        print("⚠️  未设置 MCP_ENDPOINT 环境变量")
        print("使用默认端点：http://localhost:8081")
        print("设置方法：export MCP_ENDPOINT=http://your-mcp-server:8081")
        print("="*60)
    
    try:
        await demo_mcp_discovery()
    except Exception as e:
        print(f"MCP 发现示例失败：{e}")
    
    try:
        await demo_mixed_tools()
    except Exception as e:
        print(f"混合工具示例失败：{e}")
    
    try:
        await demo_mcp_embedding()
    except Exception as e:
        print(f"嵌入示例失败：{e}")
    
    print("\n" + "="*60)
    print("所有示例运行完成！")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
