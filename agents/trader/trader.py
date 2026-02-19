"""
trader Agent

一个专注于加密货币市场的交易员

此 Agent 使用 MCP 服务器提供文件系统和记忆功能。
Terminal 功能默认禁用以确保安全。
"""
import asyncio
import yaml
from pathlib import Path
from neuroflow import AINativeAgent, AINativeAgentConfig, LLMConfig


class TraderAgent(AINativeAgent):
    """
    一个专注于加密货币市场的交易员
    """

    def __init__(self, config_path: str = "config.yaml"):
        # 加载配置
        self.config_data = self._load_config(config_path)

        super().__init__(
            AINativeAgentConfig(
                name="trader",
                description="一个专注于加密货币市场的交易员",
                llm_config=LLMConfig(
                    provider="openai",
                    model="deepseek",
                ),
            )
        )
        
        # 初始化 MCP 服务器
        self._mcp_clients = {}
        
        # 注册工具
        self._register_tools()
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _register_tools(self):
        """注册 Agent 专用工具"""
        
        @self.tool(name="greet", description="问候用户")
        async def greet(name: str) -> str:
            """问候用户"""
            return f"你好，{name}! 我是trader，很高兴为你服务。"
        
        # TODO: 添加更多领域特定工具
        # 示例：
        # @self.tool(name="analyze", description="数据分析")
        # async def analyze(data: str) -> dict:
        #     numbers = [float(x) for x in data.split(',')]
        #     return {
        #         "count": len(numbers),
        #         "sum": sum(numbers),
        #         "average": sum(numbers) / len(numbers),
        #     }
    
    async def initialize_mcp(self):
        """初始化 MCP 服务器连接"""
        mcp_config = self.config_data.get('mcp', {})
        servers = mcp_config.get('servers', [])
        
        for server in servers:
            if server.get('enabled', True):
                server_name = server.get('name')
                try:
                    # TODO: 实现 MCP 客户端连接
                    # self._mcp_clients[server_name] = await connect_mcp_server(server)
                    print(f"✅ MCP server '{server_name}' connected")
                except Exception as e:
                    print(f"❌ Failed to connect MCP server '{server_name}': {e}")
    
    async def handle_request(self, user_message: str) -> dict:
        """
        处理用户请求
        
        Args:
            user_message: 用户消息
            
        Returns:
            响应字典
        """
        # 确保 MCP 已初始化
        if not self._mcp_clients:
            await self.initialize_mcp()
        
        return await self.handle(user_message)
    
    async def shutdown(self):
        """关闭 Agent 和 MCP 连接"""
        # 关闭 MCP 连接
        for client in self._mcp_clients.values():
            try:
                await client.close()
            except Exception:
                pass
        
        print("👋 Agent shutdown complete")


async def main():
    """测试 Agent"""
    agent = ${agent_name.title().replace('_', '')}Agent()
    
    # 测试
    print("=" * 50)
    print(f"Agent: {agent.config.name}")
    print(f"描述：{agent.config.description}")
    print(f"LLM: {agent.config.llm_config.provider} / {agent.config.llm_config.model}")
    print("=" * 50)
    
    # 初始化 MCP
    await agent.initialize_mcp()
    
    # 测试对话
    result = await agent.handle_request("你好")
    print(f"\n响应：{result['response']}")
    
    # 关闭
    await agent.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
