"""
${agent_name} Agent - Basic Template

${description}

最小化 Agent 模板，适合简单场景。
"""
import asyncio
from neuroflow import AINativeAgent, AINativeAgentConfig, LLMConfig


class ${agent_name.title().replace('_', '')}Agent(AINativeAgent):
    """${description}"""
    
    def __init__(self):
        super().__init__(
            AINativeAgentConfig(
                name="${agent_name}",
                description="${description}",
                llm_config=LLMConfig(
                    provider="${llm_provider}",
                    model="${llm_model}",
                ),
            )
        )
        
        # 注册基础工具
        self._register_tools()
    
    def _register_tools(self):
        """注册 Agent 专用工具"""
        
        @self.tool(name="greet", description="问候用户")
        async def greet(name: str) -> str:
            return f"你好，{name}! 我是${agent_name}。"
    
    async def handle_request(self, user_message: str) -> dict:
        """处理用户请求"""
        return await self.handle(user_message)


async def main():
    """测试 Agent"""
    agent = ${agent_name.title().replace('_', '')}Agent()
    
    print("=" * 50)
    print(f"Agent: {agent.config.name}")
    print(f"描述：{agent.config.description}")
    print("=" * 50)
    
    result = await agent.handle_request("你好")
    print(f"\n响应：{result['response']}")


if __name__ == "__main__":
    asyncio.run(main())
