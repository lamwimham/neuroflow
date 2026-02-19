"""
AI Native Agent 高级示例

展示高级功能:
1. 多工具协作
2. 记忆管理
3. 对话历史
4. 复杂任务处理

运行:
    python examples/ai_native/advanced_example.py
"""

import asyncio
import os
from neuroflow import AINativeAgent, LLMConfig


async def demo_multi_tool():
    """演示多工具协作"""
    print("\n" + "="*60)
    print("示例 1: 多工具协作")
    print("="*60 + "\n")
    
    agent = AINativeAgent(
        name="data_processor",
        description="数据处理助手",
        llm_config=LLMConfig(
            provider="openai",
            model="gpt-4",
        ) if os.getenv("OPENAI_API_KEY") else None,
    )
    
    @agent.tool(name="fetch_data", description="获取模拟数据")
    async def fetch_data(source: str) -> dict:
        """从数据源获取数据"""
        return {
            "source": source,
            "data": [1, 2, 3, 4, 5],
            "timestamp": "2024-01-01",
        }
    
    @agent.tool(name="calculate_stats", description="计算统计数据")
    async def calculate_stats(numbers: list) -> dict:
        """计算统计数据"""
        if not numbers:
            return {"error": "Empty list"}
        return {
            "count": len(numbers),
            "sum": sum(numbers),
            "average": sum(numbers) / len(numbers),
            "min": min(numbers),
            "max": max(numbers),
        }
    
    @agent.tool(name="format_report", description="格式化报告")
    async def format_report(title: str, data: dict) -> str:
        """格式化报告"""
        lines = [f"# {title}", ""]
        for key, value in data.items():
            lines.append(f"- **{key}**: {value}")
        return "\n".join(lines)
    
    print(f"已注册工具：{agent.list_available_tools()}")
    
    # 测试：处理数据并生成报告
    if os.getenv("OPENAI_API_KEY"):
        result = await agent.handle(
            "请帮我获取 data_source_A 的数据，计算统计信息，然后生成一份报告"
        )
        print(f"\n用户：请帮我获取 data_source_A 的数据，计算统计信息，然后生成一份报告")
        print(f"\n助手：{result['response']}")
        print(f"\n使用的工具：{len(result['tool_results'])} 个")
        for tr in result['tool_results']:
            print(f"  - {tr['tool']}: {'✓' if tr['success'] else '✗'}")
    else:
        print("⚠️  需要 OPENAI_API_KEY 才能运行此示例")
        # 演示手动调用
        data = await agent.execute_tool("fetch_data", source="data_source_A")
        print(f"\nfetch_data 结果：{data}")
        
        stats = await agent.execute_tool("calculate_stats", numbers=data["data"])
        print(f"calculate_stats 结果：{stats}")
        
        report = await agent.execute_tool(
            "format_report", 
            title="数据统计报告",
            data=stats
        )
        print(f"\n生成的报告:\n{report}")


async def demo_memory():
    """演示记忆管理"""
    print("\n" + "="*60)
    print("示例 2: 记忆管理")
    print("="*60 + "\n")
    
    agent = AINativeAgent(
        name="memory_assistant",
        description="记忆助手",
        llm_config=LLMConfig(
            provider="openai",
            model="gpt-4",
        ) if os.getenv("OPENAI_API_KEY") else None,
    )
    
    # 存储记忆
    agent.store_memory("user_name", "张三", tags=["user", "profile"])
    agent.store_memory("user_preference", "喜欢简洁的回答", tags=["user", "preference"])
    agent.store_memory("project_name", "NeuroFlow", tags=["project"])
    
    print("已存储记忆:")
    print(f"  - user_name: {agent.retrieve_memory('user_name')}")
    print(f"  - user_preference: {agent.retrieve_memory('user_preference')}")
    print(f"  - project_name: {agent.retrieve_memory('project_name')}")
    
    # 搜索记忆
    user_memories = agent.search_memories(tags=["user"])
    print(f"\n用户相关记忆：{user_memories}")
    
    # 在对话中使用记忆
    if os.getenv("OPENAI_API_KEY"):
        result = await agent.handle("你还记得我的名字吗？")
        print(f"\n用户：你还记得我的名字吗？")
        print(f"助手：{result['response']}")
    else:
        print(f"\n⚠️  需要 OPENAI_API_KEY 才能运行对话示例")
        print(f"用户名字记忆：{agent.retrieve_memory('user_name')}")


async def demo_conversation():
    """演示多轮对话"""
    print("\n" + "="*60)
    print("示例 3: 多轮对话")
    print("="*60 + "\n")
    
    agent = AINativeAgent(
        name="conversation_partner",
        description="对话伙伴",
        llm_config=LLMConfig(
            provider="openai",
            model="gpt-4",
        ) if os.getenv("OPENAI_API_KEY") else None,
    )
    
    @agent.tool(name="get_weather", description="获取天气")
    async def get_weather(city: str) -> dict:
        """获取城市天气"""
        # 模拟天气数据
        import random
        conditions = ["晴", "多云", "小雨", "大雨"]
        return {
            "city": city,
            "temperature": random.randint(15, 30),
            "condition": random.choice(conditions),
        }
    
    if os.getenv("OPENAI_API_KEY"):
        # 第一轮对话
        result1 = await agent.handle("北京今天天气怎么样？")
        print(f"用户：北京今天天气怎么样？")
        print(f"助手：{result1['response']}")
        
        # 第二轮对话 (有上下文)
        result2 = await agent.handle("那上海呢？")
        print(f"\n用户：那上海呢？")
        print(f"助手：{result2['response']}")
        
        # 第三轮对话
        result3 = await agent.handle("我应该带伞吗？")
        print(f"\n用户：我应该带伞吗？")
        print(f"助手：{result3['response']}")
    else:
        print("⚠️  需要 OPENAI_API_KEY 才能运行此示例")
        
        # 演示工具调用
        beijing_weather = await agent.execute_tool("get_weather", city="北京")
        print(f"北京天气：{beijing_weather}")
        
        shanghai_weather = await agent.execute_tool("get_weather", city="上海")
        print(f"上海天气：{shanghai_weather}")


async def demo_custom_system_prompt():
    """演示自定义系统提示词"""
    print("\n" + "="*60)
    print("示例 4: 自定义系统提示词")
    print("="*60 + "\n")
    
    agent = AINativeAgent(
        name="code_reviewer",
        description="代码审查助手",
        llm_config=LLMConfig(
            provider="openai",
            model="gpt-4",
        ) if os.getenv("OPENAI_API_KEY") else None,
    )
    
    # 设置自定义系统提示词
    agent.set_system_prompt("""你是一个专业的代码审查专家。
你的任务是:
1. 审查代码质量和最佳实践
2. 指出潜在的问题和 bug
3. 提供改进建议
4. 保持友好和建设性的语气""")
    
    @agent.tool(name="check_syntax", description="检查语法错误")
    async def check_syntax(code: str) -> dict:
        """检查代码语法"""
        try:
            compile(code, '<string>', 'exec')
            return {"valid": True, "errors": []}
        except SyntaxError as e:
            return {"valid": False, "errors": [str(e)]}
    
    if os.getenv("OPENAI_API_KEY"):
        code = """
def calculate_average(numbers):
    total = sum(numbers)
    return total / len(numbers)

result = calculate_average([1, 2, 3, 4, 5])
print(result)
"""
        result = await agent.handle(f"请审查这段代码:\n{code}")
        print(f"用户：请审查这段代码")
        print(f"助手：{result['response']}")
    else:
        print("⚠️  需要 OPENAI_API_KEY 才能运行此示例")
        
        code = "print('Hello, World!')"
        syntax_result = await agent.execute_tool("check_syntax", code=code)
        print(f"语法检查：{syntax_result}")


async def main():
    """运行所有示例"""
    print("🚀 AI Native Agent 高级示例")
    print("="*60)
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  未设置 OPENAI_API_KEY 环境变量")
        print("部分示例将使用模拟模式运行")
        print("设置方法：export OPENAI_API_KEY=your-api-key")
        print("="*60)
    
    try:
        await demo_multi_tool()
    except Exception as e:
        print(f"多工具协作示例失败：{e}")
    
    try:
        await demo_memory()
    except Exception as e:
        print(f"记忆管理示例失败：{e}")
    
    try:
        await demo_conversation()
    except Exception as e:
        print(f"多轮对话示例失败：{e}")
    
    try:
        await demo_custom_system_prompt()
    except Exception as e:
        print(f"自定义系统提示词示例失败：{e}")
    
    print("\n" + "="*60)
    print("所有示例运行完成！")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
