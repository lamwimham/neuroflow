"""
MCP Server Manager

MCP 服务器管理器，负责启动、停止和管理 MCP 服务器连接
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging
from pathlib import Path

from .config_parser import MCPConfig, MCPServerConfig

logger = logging.getLogger(__name__)


@dataclass
class MCPServerStatus:
    """MCP 服务器状态"""
    name: str
    connected: bool = False
    error: Optional[str] = None
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class MCPServerManager:
    """
    MCP 服务器管理器
    
    用法:
        manager = MCPServerManager()
        await manager.start_from_config(config)
        
        # 检查状态
        status = manager.get_status("filesystem")
        
        # 停止所有
        await manager.stop_all()
    """
    
    def __init__(self):
        self.servers: Dict[str, MCPServerStatus] = {}
        self._clients: Dict[str, Any] = {}
        self._config: Optional[MCPConfig] = None
    
    async def start_from_config(self, config: MCPConfig):
        """从配置启动 MCP 服务器"""
        self._config = config
        
        if not config.enabled:
            logger.info("MCP is disabled")
            return
        
        logger.info(f"Starting MCP servers: {len(config.get_enabled_servers())} enabled")
        
        for server_config in config.get_enabled_servers():
            try:
                await self._start_server(server_config)
            except Exception as e:
                logger.error(f"Failed to start MCP server '{server_config.name}': {e}")
                self.servers[server_config.name] = MCPServerStatus(
                    name=server_config.name,
                    connected=False,
                    error=str(e),
                )
    
    async def _start_server(self, config: MCPServerConfig):
        """启动单个 MCP 服务器"""
        logger.info(f"Starting MCP server: {config.name}")
        
        # 根据服务器类型启动
        if config.name == 'filesystem':
            await self._start_filesystem_server(config)
        elif config.name == 'memory':
            await self._start_memory_server(config)
        elif config.name == 'terminal':
            await self._start_terminal_server(config)
        else:
            logger.warning(f"Unknown MCP server type: {config.name}")
            self.servers[config.name] = MCPServerStatus(
                name=config.name,
                connected=False,
                error=f"Unknown server type: {config.name}",
            )
    
    async def _start_filesystem_server(self, config: MCPServerConfig):
        """启动文件系统 MCP 服务器"""
        # TODO: 实现实际的 MCP 客户端连接
        # 这里使用模拟实现
        
        allowed_paths = config.config.get('allowed_paths', [])
        
        # 验证路径
        for path in allowed_paths:
            path_obj = Path(path)
            if not path_obj.exists():
                logger.info(f"Creating filesystem path: {path}")
                path_obj.mkdir(parents=True, exist_ok=True)
        
        self.servers['filesystem'] = MCPServerStatus(
            name='filesystem',
            connected=True,
            metadata={
                'allowed_paths': allowed_paths,
                'type': 'filesystem',
            },
        )
        
        logger.info(f"✅ Filesystem MCP server started")
    
    async def _start_memory_server(self, config: MCPServerConfig):
        """启动记忆 MCP 服务器"""
        db_path = config.config.get('db_path', './memory.db')
        
        # 确保目录存在
        db_path_obj = Path(db_path)
        db_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        self.servers['memory'] = MCPServerStatus(
            name='memory',
            connected=True,
            metadata={
                'db_path': db_path,
                'max_memories': config.config.get('max_memories', 1000),
                'type': 'memory',
            },
        )
        
        logger.info(f"✅ Memory MCP server started")
    
    async def _start_terminal_server(self, config: MCPServerConfig):
        """启动 Terminal MCP 服务器"""
        mode = config.config.get('mode', 'restricted')
        
        self.servers['terminal'] = MCPServerStatus(
            name='terminal',
            connected=True,
            metadata={
                'mode': mode,
                'allowed_commands': config.config.get('allowed_commands', []),
                'type': 'terminal',
            },
        )
        
        logger.info(f"✅ Terminal MCP server started (mode: {mode})")
    
    def get_status(self, server_name: str) -> Optional[MCPServerStatus]:
        """获取服务器状态"""
        return self.servers.get(server_name)
    
    def get_all_statuses(self) -> Dict[str, MCPServerStatus]:
        """获取所有服务器状态"""
        return self.servers.copy()
    
    def is_connected(self, server_name: str) -> bool:
        """检查是否连接"""
        status = self.servers.get(server_name)
        return status.connected if status else False
    
    def get_connected_count(self) -> int:
        """获取连接的服务器数量"""
        return sum(1 for s in self.servers.values() if s.connected)
    
    async def stop_server(self, server_name: str):
        """停止单个服务器"""
        if server_name in self._clients:
            # TODO: 实际关闭连接
            del self._clients[server_name]
        
        if server_name in self.servers:
            self.servers[server_name].connected = False
        
        logger.info(f"Stopped MCP server: {server_name}")
    
    async def stop_all(self):
        """停止所有服务器"""
        for server_name in list(self.servers.keys()):
            await self.stop_server(server_name)
        
        logger.info("All MCP servers stopped")
    
    def get_client(self, server_name: str) -> Optional[Any]:
        """获取服务器客户端"""
        return self._clients.get(server_name)
    
    def list_servers(self) -> List[str]:
        """列出所有服务器名称"""
        return list(self.servers.keys())


async def create_mcp_manager_from_config(config_path: str) -> MCPServerManager:
    """便捷函数：从配置创建 MCP 管理器"""
    from .config_parser import MCPConfigParser
    
    parser = MCPConfigParser()
    config = parser.parse_from_file(config_path)
    
    manager = MCPServerManager()
    await manager.start_from_config(config)
    
    return manager


if __name__ == "__main__":
    # 测试代码
    import sys
    
    async def test():
        if len(sys.argv) < 2:
            print("Usage: python server_manager.py <config.yaml>")
            sys.exit(1)
        
        config_path = sys.argv[1]
        
        try:
            manager = await create_mcp_manager_from_config(config_path)
            
            print("\nMCP Server Status:")
            print("=" * 50)
            
            for name, status in manager.get_all_statuses().items():
                icon = "✅" if status.connected else "❌"
                print(f"{icon} {name}: {'Connected' if status.connected else 'Disconnected'}")
                if status.error:
                    print(f"   Error: {status.error}")
                if status.metadata:
                    print(f"   Metadata: {status.metadata}")
            
            print(f"\nTotal: {manager.get_connected_count()} connected")
            
            # 停止
            await manager.stop_all()
            
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
    
    asyncio.run(test())
