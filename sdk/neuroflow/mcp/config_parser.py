"""
MCP Configuration Parser

MCP 配置解析器，解析 config.yaml 中的 MCP 配置
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """MCP 服务器配置"""
    name: str
    enabled: bool = True
    description: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPServerConfig':
        """从字典创建配置"""
        return cls(
            name=data.get('name', 'unknown'),
            enabled=data.get('enabled', True),
            description=data.get('description', ''),
            config=data.get('config', {}),
        )
    
    def validate(self) -> List[str]:
        """验证配置"""
        errors = []
        
        if not self.name or self.name == 'unknown':
            errors.append("Server name is required")
        
        # 特定服务器的验证
        if self.name == 'filesystem':
            allowed_paths = self.config.get('allowed_paths', [])
            if not allowed_paths:
                logger.warning(f"Filesystem MCP: No allowed_paths configured")
        
        elif self.name == 'memory':
            db_path = self.config.get('db_path', '')
            if not db_path:
                logger.warning(f"Memory MCP: No db_path configured")
        
        elif self.name == 'terminal':
            mode = self.config.get('mode', 'restricted')
            if mode not in ['restricted', 'permissive']:
                errors.append(f"Invalid terminal mode: {mode}")
        
        return errors


@dataclass
class MCPConfig:
    """MCP 总配置"""
    enabled: bool = True
    servers: List[MCPServerConfig] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPConfig':
        """从字典创建配置"""
        servers = []
        for server_data in data.get('servers', []):
            servers.append(MCPServerConfig.from_dict(server_data))
        
        return cls(
            enabled=data.get('enabled', True),
            servers=servers,
        )
    
    def get_enabled_servers(self) -> List[MCPServerConfig]:
        """获取启用的服务器"""
        return [s for s in self.servers if s.enabled]
    
    def get_server(self, name: str) -> Optional[MCPServerConfig]:
        """获取指定名称的服务器配置"""
        for server in self.servers:
            if server.name == name:
                return server
        return None
    
    def validate_all(self) -> Dict[str, List[str]]:
        """验证所有服务器配置"""
        errors = {}
        for server in self.servers:
            server_errors = server.validate()
            if server_errors:
                errors[server.name] = server_errors
        return errors


class MCPConfigParser:
    """
    MCP 配置解析器
    
    用法:
        parser = MCPConfigParser()
        config = parser.parse_from_file("config.yaml")
        
        # 获取启用的服务器
        enabled_servers = config.get_enabled_servers()
        
        # 验证配置
        errors = config.validate_all()
    """
    
    def __init__(self):
        self.config_cache: Dict[str, MCPConfig] = {}
    
    def parse_from_file(self, config_path: str) -> MCPConfig:
        """从文件解析 MCP 配置"""
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        # 检查缓存
        config_key = str(config_file.absolute())
        if config_key in self.config_cache:
            logger.debug(f"Using cached config for {config_key}")
            return self.config_cache[config_key]
        
        # 解析文件
        with open(config_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # 提取 MCP 配置
        mcp_data = data.get('mcp', {})
        
        if not mcp_data:
            logger.warning(f"No MCP configuration found in {config_path}")
            mcp_data = {'enabled': False}
        
        # 创建配置对象
        config = MCPConfig.from_dict(mcp_data)
        
        # 缓存
        self.config_cache[config_key] = config
        
        logger.info(f"Parsed MCP config: {len(config.servers)} servers, "
                   f"{len(config.get_enabled_servers())} enabled")
        
        # 验证
        errors = config.validate_all()
        if errors:
            for server_name, server_errors in errors.items():
                for error in server_errors:
                    logger.error(f"MCP config error [{server_name}]: {error}")
        
        return config
    
    def parse_from_dict(self, data: Dict[str, Any]) -> MCPConfig:
        """从字典解析配置"""
        mcp_data = data.get('mcp', {})
        return MCPConfig.from_dict(mcp_data)
    
    def clear_cache(self):
        """清除缓存"""
        self.config_cache.clear()
        logger.debug("MCP config cache cleared")


def load_mcp_config(config_path: str) -> MCPConfig:
    """便捷函数：加载 MCP 配置"""
    parser = MCPConfigParser()
    return parser.parse_from_file(config_path)


if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python config_parser.py <config.yaml>")
        sys.exit(1)
    
    config_path = sys.argv[1]
    
    try:
        config = load_mcp_config(config_path)
        
        print(f"MCP Enabled: {config.enabled}")
        print(f"Total Servers: {len(config.servers)}")
        print(f"Enabled Servers: {len(config.get_enabled_servers())}")
        print()
        
        for server in config.get_enabled_servers():
            print(f"  ✅ {server.name}: {server.description}")
            if server.config:
                print(f"     Config: {server.config}")
        
        # 验证
        errors = config.validate_all()
        if errors:
            print("\n⚠️  Validation errors:")
            for server_name, server_errors in errors.items():
                for error in server_errors:
                    print(f"  - [{server_name}] {error}")
        else:
            print("\n✅ Configuration is valid")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
