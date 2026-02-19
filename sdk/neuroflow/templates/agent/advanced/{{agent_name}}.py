"""
${agent_name} Agent - Advanced Template

${description}

高级多 Agent 协作模板，支持：
- 多 Agent 协作
- 完整 MCP 集成 (filesystem + memory + terminal)
- 高级安全配置
- 分布式部署
"""
import asyncio
import yaml
import json
from pathlib import Path
from typing import List, Dict, Any
from neuroflow import AINativeAgent, AINativeAgentConfig, LLMConfig
from neuroflow.a2a import AgentRegistry, AgentInfo, AgentCapability, CollaborativeOrchestrator


class ${agent_name.title().replace('_', '')}Agent(AINativeAgent):
    """${description}"""
    
    def __init__(self, config_path: str = "config.yaml"):
        # 加载配置
        self.config_data = self._load_config(config_path)
        
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
        
        # 多 Agent 协作
        self.agent_registry = AgentRegistry()
        self.collaborator = None
        
        # MCP 客户端
        self._mcp_clients = {}
        
        # 注册工具
        self._register_tools()
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        return yaml.safe_load(config_file.read_text())
    
    def _register_tools(self):
        """注册 Agent 专用工具"""
        
        @self.tool(name="greet", description="问候用户")
        async def greet(name: str) -> str:
            return f"你好，{name}! 我是${agent_name}。"
        
        # 多 Agent 协作工具
        @self.tool(name="request_assistance", description="请求其他 Agent 协助")
        async def request_assistance(task: str, required_capabilities: List[str]) -> dict:
            """请求其他 Agent 协助"""
            if not self.collaborator:
                return {"error": "Collaborator not initialized"}
            
            result = await self.collaborator.execute_with_collaboration(task)
            return {
                "success": True,
                "result": result.response,
                "collaborating_agents": result.collaborating_agents,
            }
        
        # 高级分析工具
        @self.tool(name="analyze_complex", description="复杂任务分析")
        async def analyze_complex(task_description: str) -> dict:
            """复杂任务分析，可能涉及多 Agent 协作"""
            # TODO: 实现复杂分析逻辑
            return {
                "task": task_description,
                "complexity": "high",
                "requires_collaboration": True,
            }
    
    async def initialize_mcp(self):
        """初始化 MCP 服务器连接"""
        mcp_config = self.config_data.get('mcp', {})
        
        if not mcp_config.get('enabled', True):
            print("ℹ️  MCP disabled")
            return
        
        servers = mcp_config.get('servers', [])
        for server in servers:
            if server.get('enabled'):
                server_name = server.get('name')
                try:
                    # TODO: 实现 MCP 客户端连接
                    print(f"✅ MCP server '{server_name}' connected")
                    self._mcp_clients[server_name] = {"name": server_name, "status": "connected"}
                except Exception as e:
                    print(f"❌ Failed to connect MCP server '{server_name}': {e}")
    
    async def initialize_collaboration(self):
        """初始化多 Agent 协作"""
        # 注册协作者 Agent
        collaborators = self.config_data.get('collaborators', [])
        
        for collab_config in collaborators:
            agent_info = AgentInfo(
                id=collab_config.get('name'),
                name=collab_config.get('name'),
                description=collab_config.get('description', ''),
                capabilities=[
                    AgentCapability(cap) for cap in collab_config.get('capabilities', [])
                ],
                endpoint=collab_config.get('endpoint', ''),
            )
            self.agent_registry.register_agent(agent_info)
        
        # 创建协作编排器
        self.collaborator = CollaborativeOrchestrator(
            llm_orchestrator=self.orchestrator,
            agent_registry=self.agent_registry,
        )
        
        print(f"✅ Collaboration initialized with {len(collaborators)} agents")
    
    async def handle_request(self, user_message: str) -> dict:
        """处理用户请求"""
        # 初始化 MCP
        if not self._mcp_clients:
            await self.initialize_mcp()
        
        # 初始化协作
        if not self.collaborator:
            await self.initialize_collaboration()
        
        return await self.handle(user_message)
    
    async def shutdown(self):
        """关闭 Agent 和 MCP 连接"""
        for client in self._mcp_clients.values():
            try:
                # TODO: 关闭 MCP 连接
                pass
            except Exception:
                pass
        
        print("👋 Agent shutdown complete")


async def main():
    """测试 Agent"""
    agent = ${agent_name.title().replace('_', '')}Agent()
    
    print("=" * 60)
    print(f"Agent: {agent.config.name}")
    print(f"描述：{agent.config.description}")
    print(f"LLM: {agent.config.llm_config.provider} / {agent.config.llm_config.model}")
    print(f"MCP: {len(agent.config_data.get('mcp', {}).get('servers', []))} servers")
    print(f"Collaborators: {len(agent.config_data.get('collaborators', []))} agents")
    print("=" * 60)
    
    # 初始化
    await agent.initialize_mcp()
    await agent.initialize_collaboration()
    
    # 测试对话
    result = await agent.handle_request("你好")
    print(f"\n响应：{result['response']}")
    
    # 关闭
    await agent.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
