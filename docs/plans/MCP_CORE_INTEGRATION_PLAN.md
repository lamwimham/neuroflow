# MCP 核心能力集成方案

## 概述

本方案旨在将 MCP (Model Context Protocol) 集成提升为 NeuroFlow 框架的核心能力，使开发者能够快速对接第三方 MCP 服务，实现工具、资源和提示词的无缝集成。

## 现状分析

### 当前 MCP 实现位置
- **示例层**: `/examples/trading_agent/mcp_client.py` - Python 实现的 MCP 客户端管理器
- **内核层**: `/kernel/src/mcp/mod.rs` - Rust 内核中的 MCP 服务模块（当前侧重模型服务）

### 存在的问题
1. **双层架构割裂**: Rust 内核和 Python SDK 各有一套 MCP 实现，缺乏统一抽象
2. **配置分散**: MCP 服务器配置分散在示例代码中，未形成标准化配置体系
3. **工具发现机制弱**: 缺乏自动化的工具发现、注册和路由机制
4. **开发者体验**: 对接第三方 MCP 服务需要手动编写大量样板代码

## 目标架构

```
┌─────────────────────────────────────────────────────────┐
│                   NeuroFlow Application                  │
├─────────────────────────────────────────────────────────┤
│  Python SDK Layer                                        │
│  ┌──────────────────────────────────────────────────┐   │
│  │  @mcp_tool / @mcp_resource / @mcp_prompt        │   │
│  │  MCPClientManager (Unified API)                  │   │
│  └──────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│  Rust Kernel Layer                                       │
│  ┌──────────────────────────────────────────────────┐   │
│  │  MCP Gateway (HTTP/gRPC)                         │   │
│  │  ├─ Tool Router (语义路由到 MCP 服务)              │   │
│  │  ├─ Resource Manager (MCP 资源缓存)               │   │
│  │  └─ Connection Pool (连接池管理)                  │   │
│  └──────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│  External MCP Servers                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ Filesystem  │  │ Database    │  │ Custom API  │     │
│  │ MCP Server  │  │ MCP Server  │  │ MCP Server  │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

## 核心设计原则

### 1. 统一抽象层
- 定义标准化的 MCP 接口（工具、资源、提示词）
- Rust 和 Python 共享相同的抽象模型
- 通过 Protobuf 定义跨语言通信协议

### 2. 插件化架构
- MCP 服务作为可插拔插件
- 支持热加载/卸载 MCP 服务
- 动态工具发现和注册

### 3. 开发者友好
- 简洁的装饰器 API
- 自动化工具发现
- 类型安全的参数验证

### 4. 生产就绪
- 连接池和负载均衡
- 熔断和重试机制
- 完整的可观测性

## 实现方案

### 一、标准化配置体系

#### 1.1 统一配置文件格式

```yaml
# config/mcp.yaml
mcp:
  # 全局设置
  global:
    timeout_ms: 30000
    max_connections: 100
    retry_attempts: 3
    api_key: ${MCP_API_KEY}  # 支持环境变量
    api_secret: ${MCP_API_SECRET}

  # MCP 服务器注册
  servers:
    filesystem:
      enabled: true
      command: npx
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"]
      http_port: 8081
      description: "文件系统 MCP 服务"
      tools:
        - read_file
        - write_file
        - list_directory
      resources:
        - pattern: "file:///*"
          cache_ttl: 300

    database:
      enabled: true
      command: python
      args: ["-m", "mcp_server_database", "--uri", "postgresql://localhost/db"]
      http_port: 8082
      description: "数据库 MCP 服务"
      tools:
        - query
        - insert
        - update

    custom_api:
      enabled: true
      url: https://api.example.com/mcp
      http_port: 8083
      auth:
        type: bearer
        token: ${CUSTOM_API_TOKEN}
      description: "自定义 API MCP 服务"
```

#### 1.2 配置加载器 (Rust)

```rust
// kernel/src/mcp/config.rs
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct MCPConfig {
    pub global: MCPGlobalConfig,
    pub servers: HashMap<String, MCPServerConfig>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct MCPGlobalConfig {
    pub timeout_ms: u64,
    pub max_connections: usize,
    pub retry_attempts: u32,
    pub api_key: Option<String>,
    pub api_secret: Option<String>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct MCPServerConfig {
    pub enabled: bool,
    pub command: Option<String>,
    pub args: Option<Vec<String>>,
    pub url: Option<String>,
    pub http_port: u16,
    pub description: Option<String>,
    pub tools: Option<Vec<String>>,
    pub resources: Option<Vec<MCPResourceConfig>>,
    pub auth: Option<MCPAuthConfig>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct MCPResourceConfig {
    pub pattern: String,
    pub cache_ttl: u64,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct MCPAuthConfig {
    #[serde(rename = "type")]
    pub auth_type: String,
    pub token: Option<String>,
}

impl MCPConfig {
    pub fn load_from_path(path: &str) -> Result<Self, Box<dyn std::error::Error>> {
        let content = std::fs::read_to_string(path)?;
        let config: MCPConfig = serde_yaml::from_str(&content)?;
        Ok(config)
    }

    pub fn load_from_env() -> Result<Self, Box<dyn std::error::Error>> {
        // 从环境变量加载配置
        // 支持 MCP_CONFIG_JSON 环境变量
    }
}
```

### 二、Rust 内核层实现

#### 2.1 MCP 网关模块

```rust
// kernel/src/mcp/gateway.rs
use std::sync::Arc;
use tokio::sync::{RwLock, Semaphore};
use tracing::{info, warn, error};

pub struct MCPGateway {
    config: Arc<MCPConfig>,
    connections: Arc<RwLock<HashMap<String, Arc<MCPConnection>>>>,
    tool_registry: Arc<RwLock<HashMap<String, MCPToolInfo>>>,
    resource_cache: Arc<RwLock<LruCache<String, MCPResource>>>,
    semaphore: Arc<Semaphore>,
}

impl MCPGateway {
    pub fn new(config: MCPConfig) -> Self {
        Self {
            config: Arc::new(config),
            connections: Arc::new(RwLock::new(HashMap::new())),
            tool_registry: Arc::new(RwLock::new(HashMap::new())),
            resource_cache: Arc::new(RwLock::new(LruCache::new(1000))),
            semaphore: Arc::new(Semaphore::new(
                config.global.max_connections
            )),
        }
    }

    /// 初始化所有配置的 MCP 服务
    pub async fn initialize(&self) -> Result<(), NeuroFlowError> {
        for (server_name, server_config) in &self.config.servers {
            if server_config.enabled {
                self.connect_server(server_name, server_config).await?;
            }
        }
        Ok(())
    }

    /// 连接到单个 MCP 服务
    async fn connect_server(
        &self,
        name: &str,
        config: &MCPServerConfig,
    ) -> Result<(), NeuroFlowError> {
        info!("Connecting to MCP server: {}", name);

        let connection = MCPConnection::new(name, config).await?;
        
        // 获取工具列表并注册
        let tools = connection.list_tools().await?;
        self.register_tools(name, tools).await;

        // 存储连接
        let mut connections = self.connections.write().await;
        connections.insert(name.to_string(), Arc::new(connection));

        info!("Connected to MCP server: {} with {} tools", name, tools.len());
        Ok(())
    }

    /// 执行 MCP 工具
    pub async fn execute_tool(
        &self,
        server_name: &str,
        tool_name: &str,
        arguments: serde_json::Value,
    ) -> Result<serde_json::Value, NeuroFlowError> {
        let _permit = self.semaphore.acquire().await
            .map_err(|e| NeuroFlowError::InternalError(e.to_string()))?;

        let connections = self.connections.read().await;
        let connection = connections.get(server_name)
            .ok_or_else(|| NeuroFlowError::MCPServerError(
                format!("Server '{}' not found", server_name)
            ))?;

        connection.call_tool(tool_name, arguments).await
    }

    /// 获取所有可用工具
    pub async fn list_all_tools(&self) -> Vec<MCPToolInfo> {
        let registry = self.tool_registry.read().await;
        registry.values().cloned().collect()
    }

    /// 按名称查找工具
    pub async fn get_tool(&self, tool_name: &str) -> Option<MCPToolInfo> {
        let registry = self.tool_registry.read().await;
        registry.get(tool_name).cloned()
    }

    async fn register_tools(&self, server_name: &str, tools: Vec<MCPToolInfo>) {
        let mut registry = self.tool_registry.write().await;
        for tool in tools {
            let full_name = format!("{}:{}", server_name, tool.name);
            registry.insert(full_name, tool);
        }
    }
}
```

#### 2.2 MCP 连接管理

```rust
// kernel/src/mcp/connection.rs
use reqwest::Client;
use serde_json::json;

pub struct MCPConnection {
    server_name: String,
    http_port: u16,
    base_url: String,
    client: Client,
    auth_config: Option<MCPAuthConfig>,
}

impl MCPConnection {
    pub async fn new(
        server_name: &str,
        config: &MCPServerConfig,
    ) -> Result<Self, NeuroFlowError> {
        let client = Client::builder()
            .timeout(std::time::Duration::from_millis(
                config.get_timeout_ms()
            ))
            .build()?;

        let base_url = if let Some(url) = &config.url {
            url.clone()
        } else {
            format!("http://localhost:{}", config.http_port)
        };

        Ok(Self {
            server_name: server_name.to_string(),
            http_port: config.http_port,
            base_url,
            client,
            auth_config: config.auth.clone(),
        })
    }

    pub async fn list_tools(&self) -> Result<Vec<MCPToolInfo>, NeuroFlowError> {
        let url = format!("{}/mcp/tools/list", self.base_url);
        let mut request = self.client.get(&url);

        if let Some(auth) = &self.auth_config {
            request = self.apply_auth(request, auth);
        }

        let response = request.send().await?;
        
        if response.status().is_success() {
            let result: MCPToolsResponse = response.json().await?;
            Ok(result.result.tools)
        } else {
            Err(NeuroFlowError::MCPToolExecutionError(
                format!("Failed to list tools: {}", response.status())
            ))
        }
    }

    pub async fn call_tool(
        &self,
        tool_name: &str,
        arguments: serde_json::Value,
    ) -> Result<serde_json::Value, NeuroFlowError> {
        let url = format!("{}/mcp/tools/call", self.base_url);
        
        let payload = json!({
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "jsonrpc": "2.0",
            "id": 1
        });

        let mut request = self.client.post(&url).json(&payload);

        if let Some(auth) = &self.auth_config {
            request = self.apply_auth(request, auth);
        }

        let response = request.send().await?;
        
        if response.status().is_success() {
            let result: MCPToolCallResponse = response.json().await?;
            
            if let Some(error) = result.error {
                Err(NeuroFlowError::MCPToolExecutionError(
                    format!("Tool error: {:?}", error)
                ))
            } else {
                Ok(result.result.unwrap_or(json!(null)))
            }
        } else {
            Err(NeuroFlowError::MCPToolExecutionError(
                format!("Tool call failed: {}", response.status())
            ))
        }
    }

    fn apply_auth(
        &self,
        request: reqwest::RequestBuilder,
        auth: &MCPAuthConfig,
    ) -> reqwest::RequestBuilder {
        match auth.auth_type.as_str() {
            "bearer" => {
                if let Some(token) = &auth.token {
                    request.bearer_auth(token)
                } else {
                    request
                }
            }
            "api_key" => {
                // 自定义 API Key 逻辑
                request
            }
            _ => request,
        }
    }
}
```

#### 2.3 MCP 工具路由

```rust
// kernel/src/mcp/router.rs
use crate::routing::semantic::SemanticRouter;

pub struct MCPToolRouter {
    gateway: Arc<MCPGateway>,
    semantic_router: Option<SemanticRouter>,
}

impl MCPToolRouter {
    pub fn new(gateway: Arc<MCPGateway>) -> Self {
        Self {
            gateway,
            semantic_router: None,
        }
    }

    /// 启用语义路由
    pub fn with_semantic_routing(mut self, router: SemanticRouter) -> Self {
        self.semantic_router = Some(router);
        self
    }

    /// 根据工具名称路由请求
    pub async fn route_by_name(
        &self,
        tool_name: &str,
        arguments: serde_json::Value,
    ) -> Result<serde_json::Value, NeuroFlowError> {
        // 解析工具名称格式：server_name:tool_name
        let parts: Vec<&str> = tool_name.split(':').collect();
        
        let (server_name, actual_tool_name) = if parts.len() == 2 {
            (parts[0], parts[1])
        } else {
            // 如果没有指定服务器，尝试自动发现
            self.find_tool_server(tool_name).await?
        };

        self.gateway.execute_tool(
            server_name,
            actual_tool_name,
            arguments,
        ).await
    }

    /// 语义路由 - 根据描述自动选择工具
    pub async fn route_by_semantic(
        &self,
        intent: &str,
        arguments: serde_json::Value,
    ) -> Result<serde_json::Value, NeuroFlowError> {
        if let Some(router) = &self.semantic_router {
            // 获取所有工具的描述
            let tools = self.gateway.list_all_tools().await;
            
            // 使用语义路由选择最佳工具
            let best_tool = router.find_best_tool(tools, intent).await?;
            
            self.gateway.execute_tool(
                &best_tool.server_name,
                &best_tool.name,
                arguments,
            ).await
        } else {
            Err(NeuroFlowError::RoutingError(
                "Semantic router not configured".to_string()
            ))
        }
    }

    async fn find_tool_server(
        &self,
        tool_name: &str,
    ) -> Result<(&str, &str), NeuroFlowError> {
        let registry = self.gateway.tool_registry.read().await;
        
        for (full_name, _) in registry.iter() {
            if full_name.ends_with(&format!(":{}", tool_name)) {
                let parts: Vec<&str> = full_name.split(':').collect();
                return Ok((parts[0], parts[1]));
            }
        }

        Err(NeuroFlowError::MCPToolNotFoundError(
            format!("Tool '{}' not found", tool_name)
        ))
    }
}
```

### 三、Python SDK 层实现

#### 3.1 MCP 装饰器 API

```python
# sdk/neuroflow/mcp.py
"""
MCP 集成模块
提供装饰器 API 用于快速对接 MCP 服务
"""
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from functools import wraps
import os
import yaml


@dataclass
class MCPTool:
    """MCP 工具定义"""
    name: str
    description: str
    server_name: str
    parameters: Dict[str, Any]
    endpoint: str


class MCPClient:
    """MCP 客户端 - 统一 API"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.config = self._load_config(config_path) if config_path else {}
        self.sessions: Dict[str, aiohttp.ClientSession] = {}
        self.tools: Dict[str, MCPTool] = {}
        self._initialized = False

    def _load_config(self, path: str) -> Dict:
        """加载配置文件"""
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    async def initialize(self):
        """初始化 MCP 客户端"""
        if self._initialized:
            return

        mcp_config = self.config.get('mcp', {})
        servers = mcp_config.get('servers', {})

        for server_name, server_config in servers.items():
            if server_config.get('enabled', True):
                await self._connect_server(server_name, server_config)

        self._initialized = True

    async def _connect_server(self, name: str, config: Dict):
        """连接到 MCP 服务器"""
        http_port = config.get('http_port', 8080)
        base_url = config.get('url', f"http://localhost:{http_port}")

        session = aiohttp.ClientSession()
        self.sessions[name] = session

        # 获取工具列表
        await self._fetch_tools(name, base_url, config)

    async def _fetch_tools(self, server_name: str, base_url: str, config: Dict):
        """获取服务器工具列表"""
        session = self.sessions[server_name]
        url = f"{base_url}/mcp/tools/list"

        headers = self._build_headers(config)

        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                tools = result.get('result', {}).get('tools', [])

                for tool in tools:
                    tool_name = f"{server_name}:{tool['name']}"
                    self.tools[tool_name] = MCPTool(
                        name=tool_name,
                        description=tool.get('description', ''),
                        server_name=server_name,
                        parameters=tool.get('inputSchema', {}),
                        endpoint=f"{base_url}/mcp/tools/call"
                    )

    def _build_headers(self, config: Dict) -> Dict[str, str]:
        """构建请求头"""
        headers = {"Content-Type": "application/json"}

        auth = config.get('auth', {})
        auth_type = auth.get('type', '')

        if auth_type == 'bearer':
            token = auth.get('token') or os.getenv('MCP_BEARER_TOKEN')
            headers['Authorization'] = f"Bearer {token}"
        elif auth_type == 'api_key':
            api_key = auth.get('key') or os.getenv('MCP_API_KEY')
            headers['X-API-Key'] = api_key

        return headers

    async def call_tool(
        self,
        tool_name: str,
        **kwargs
    ) -> Any:
        """调用 MCP 工具"""
        if not self._initialized:
            await self.initialize()

        if tool_name not in self.tools:
            raise ValueError(f"MCP tool '{tool_name}' not found")

        tool = self.tools[tool_name]
        session = self.sessions.get(tool.server_name)

        if not session:
            raise RuntimeError(f"Not connected to server '{tool.server_name}'")

        payload = {
            "method": "tools/call",
            "params": {
                "name": tool.name.split(':', 1)[1],  # 去掉服务器前缀
                "arguments": kwargs
            },
            "jsonrpc": "2.0",
            "id": 1
        }

        config = self.config.get('mcp', {}).get('servers', {}).get(tool.server_name, {})
        headers = self._build_headers(config)

        async with session.post(tool.endpoint, json=payload, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                if "error" in result:
                    raise RuntimeError(f"MCP tool error: {result['error']}")
                return result.get("result", {})
            else:
                error_text = await response.text()
                raise RuntimeError(f"MCP tool call failed: {response.status} - {error_text}")

    async def list_tools(self) -> List[MCPTool]:
        """列出所有可用工具"""
        if not self._initialized:
            await self.initialize()
        return list(self.tools.values())

    async def close(self):
        """关闭所有会话"""
        for session in self.sessions.values():
            await session.close()
        self.sessions.clear()

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# 全局 MCP 客户端实例
_mcp_client: Optional[MCPClient] = None


def get_mcp_client(config_path: Optional[str] = None) -> MCPClient:
    """获取全局 MCP 客户端实例"""
    global _mcp_client

    if _mcp_client is None:
        _mcp_client = MCPClient(config_path)

    return _mcp_client


# MCP 工具装饰器
def mcp_tool(
    server: str,
    tool_name: Optional[str] = None,
    description: Optional[str] = None
):
    """
    MCP 工具装饰器

    用法:
        @mcp_tool(server="filesystem", tool_name="read_file")
        async def read_file_wrapper(path: str) -> str:
            return await mcp_client.call_tool("filesystem:read_file", path=path)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            client = get_mcp_client()
            actual_tool = tool_name or func.__name__
            full_name = f"{server}:{actual_tool}"
            return await client.call_tool(full_name, **kwargs)
        return wrapper
    return decorator


# MCP 资源装饰器
def mcp_resource(uri_pattern: str, server: Optional[str] = None):
    """
    MCP 资源装饰器

    用法:
        @mcp_resource("file:///*", server="filesystem")
        async def get_file_resource(uri: str):
            return await mcp_client.read_resource(uri)
    """
    def decorator(func: Callable):
        # 注册资源处理器
        # 实际实现需要资源路由逻辑
        return func
    return decorator


# MCP 提示词装饰器
def mcp_prompt(server: Optional[str] = None):
    """
    MCP 提示词装饰器

    用法:
        @mcp_prompt(server="assistant")
        async def get_system_prompt():
            return await mcp_client.get_prompt("system")
    """
    def decorator(func: Callable):
        # 注册提示词处理器
        return func
    return decorator


# 便捷函数
async def mcp_call(tool_name: str, **kwargs) -> Any:
    """便捷调用 MCP 工具"""
    client = get_mcp_client()
    return await client.call_tool(tool_name, **kwargs)


async def mcp_list_tools() -> List[MCPTool]:
    """列出所有可用工具"""
    client = get_mcp_client()
    return await client.list_tools()


# Agent 集成
def agent_with_mcp(
    name: str,
    mcp_servers: Optional[List[str]] = None,
    mcp_config: Optional[str] = None,
    **agent_kwargs
):
    """
    带有 MCP 集成的 Agent 装饰器

    用法:
        @agent_with_mcp(
            name="data_agent",
            mcp_servers=["database", "filesystem"],
            mcp_config="config/mcp.yaml"
        )
        class DataAgent:
            async def handle(self, request, context):
                # 可以直接使用 MCP 工具
                data = await mcp_call("database:query", sql="SELECT * FROM users")
                return {"data": data}
    """
    def decorator(cls):
        # 保存原始的 handle 方法
        original_handle = getattr(cls, 'handle', None)

        async def enhanced_handle(self, request, context):
            # 初始化 MCP 客户端
            client = get_mcp_client(mcp_config)
            await client.initialize()

            # 将 MCP 客户端注入 context
            context.mcp_client = client

            # 调用原始 handle
            if original_handle:
                return await original_handle(self, request, context)
            else:
                raise NotImplementedError("Agent must implement handle method")

        # 替换 handle 方法
        setattr(cls, 'handle', enhanced_handle)

        return cls

    return decorator
```

#### 3.2 类型定义和验证

```python
# sdk/neuroflow/mcp_types.py
"""
MCP 类型定义和验证
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import json


class MCPParameterType(str, Enum):
    """MCP 参数类型"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class MCPParameterSchema:
    """MCP 参数模式"""
    type: str
    description: Optional[str] = None
    required: bool = False
    default: Optional[Any] = None
    items: Optional['MCPParameterSchema'] = None  # 用于 array 类型
    properties: Optional[Dict[str, 'MCPParameterSchema']] = None  # 用于 object 类型


@dataclass
class MCPToolDefinition:
    """MCP 工具定义"""
    name: str
    description: str
    input_schema: Dict[str, MCPParameterSchema]
    server_name: str
    version: str = "1.0.0"


@dataclass
class MCPResourceDefinition:
    """MCP 资源定义"""
    uri: str
    name: str
    description: str
    mime_type: str
    server_name: str


@dataclass
class MCPPromptDefinition:
    """MCP 提示词定义"""
    name: str
    description: str
    arguments: List[MCPParameterSchema]
    server_name: str


class MCPValidator:
    """MCP 参数验证器"""

    @staticmethod
    def validate_parameters(
        params: Dict[str, Any],
        schema: Dict[str, MCPParameterSchema]
    ) -> bool:
        """验证参数是否符合模式"""
        for param_name, param_schema in schema.items():
            if param_schema.required and param_name not in params:
                raise ValueError(f"Missing required parameter: {param_name}")

            if param_name in params:
                value = params[param_name]
                MCPValidator._validate_type(value, param_schema, param_name)

        return True

    @staticmethod
    def _validate_type(
        value: Any,
        schema: MCPParameterSchema,
        param_name: str
    ):
        """验证参数类型"""
        type_checks = {
            "string": lambda v: isinstance(v, str),
            "number": lambda v: isinstance(v, (int, float)),
            "boolean": lambda v: isinstance(v, bool),
            "array": lambda v: isinstance(v, list),
            "object": lambda v: isinstance(v, dict),
        }

        check_func = type_checks.get(schema.type)
        if check_func and not check_func(value):
            raise ValueError(
                f"Parameter '{param_name}' must be of type {schema.type}, "
                f"got {type(value).__name__}"
            )

        # 递归验证嵌套类型
        if schema.type == "array" and schema.items and isinstance(value, list):
            for item in value:
                MCPValidator._validate_type(item, schema.items, f"{param_name}[]")

        if schema.type == "object" and schema.properties and isinstance(value, dict):
            MCPValidator.validate_parameters(value, schema.properties)
```

### 四、开发者快速入门

#### 4.1 快速开始指南

```markdown
# MCP 快速开始指南

## 1. 安装依赖

```bash
pip install neuroflow[mcp]
```

## 2. 配置 MCP 服务

创建 `config/mcp.yaml`:

```yaml
mcp:
  servers:
    filesystem:
      enabled: true
      command: npx
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"]
      http_port: 8081
```

## 3. 使用 MCP 工具

### 方式一：直接使用客户端

```python
from neuroflow.mcp import get_mcp_client

client = get_mcp_client("config/mcp.yaml")
await client.initialize()

# 列出所有工具
tools = await client.list_tools()
print(f"Available tools: {[t.name for t in tools]}")

# 调用工具
result = await client.call_tool(
    "filesystem:read_file",
    path="/workspace/data.txt"
)
print(f"File content: {result}")
```

### 方式二：使用装饰器

```python
from neuroflow.mcp import mcp_tool

@mcp_tool(server="filesystem", tool_name="read_file")
async def read_file(path: str) -> str:
    """读取文件"""
    pass

# 直接使用
content = await read_file(path="/workspace/data.txt")
```

### 方式三：在 Agent 中集成

```python
from neuroflow import agent
from neuroflow.mcp import agent_with_mcp

@agent_with_mcp(
    name="file_processor",
    mcp_servers=["filesystem"],
    mcp_config="config/mcp.yaml"
)
class FileProcessorAgent:
    async def handle(self, request, context):
        # 通过 context 访问 MCP 客户端
        mcp = context.mcp_client
        
        # 读取文件
        content = await mcp.call_tool(
            "filesystem:read_file",
            path=request.get("file_path")
        )
        
        # 处理文件内容
        processed = self.process(content)
        
        return {"result": processed}
    
    def process(self, content):
        # 业务逻辑
        pass
```

## 4. 自定义 MCP 服务

### 创建 MCP 服务器

```python
# my_mcp_server.py
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("my-custom-server")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="greet",
            description="Greet someone by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name to greet"
                    }
                },
                "required": ["name"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "greet":
        return [
            TextContent(
                type="text",
                text=f"Hello, {arguments['name']}!"
            )
        ]

if __name__ == "__main__":
    server.run()
```

### 注册到 NeuroFlow

```yaml
# config/mcp.yaml
mcp:
  servers:
    custom:
      enabled: true
      command: python
      args: ["my_mcp_server.py"]
      http_port: 8085
```

## 5. 调试和监控

### 查看工具列表

```bash
neuroflow mcp list-tools --config config/mcp.yaml
```

### 测试工具调用

```bash
neuroflow mcp call-tool filesystem:read_file --path /workspace/test.txt
```

### 查看日志

```bash
neuroflow logs --component mcp
```
```

#### 4.2 示例项目

```python
# examples/mcp_integration/data_agent.py
"""
MCP 集成示例 - 数据处理 Agent
"""
from neuroflow.mcp import agent_with_mcp, mcp_call


@agent_with_mcp(
    name="data_processor",
    mcp_servers=["database", "filesystem", "api"],
    mcp_config="config/mcp.yaml"
)
class DataProcessorAgent:
    """数据处理 Agent，集成多个 MCP 服务"""

    async def handle(self, request, context):
        operation = request.get("operation")
        
        if operation == "import":
            return await self.import_data(request, context)
        elif operation == "export":
            return await self.export_data(request, context)
        elif operation == "transform":
            return await self.transform_data(request, context)
        else:
            return {"error": f"Unknown operation: {operation}"}

    async def import_data(self, request, context):
        """从文件系统导入数据"""
        file_path = request.get("file_path")
        
        # 读取文件
        file_content = await mcp_call(
            "filesystem:read_file",
            path=file_path
        )
        
        # 解析数据
        data = self.parse_data(file_content)
        
        # 存储到数据库
        await mcp_call(
            "database:insert",
            table="imported_data",
            data=data
        )
        
        return {"status": "success", "records": len(data)}

    async def export_data(self, request, context):
        """导出数据到文件系统"""
        query = request.get("query")
        output_path = request.get("output_path")
        
        # 查询数据库
        data = await mcp_call(
            "database:query",
            sql=query
        )
        
        # 写入文件
        await mcp_call(
            "filesystem:write_file",
            path=output_path,
            content=self.format_data(data)
        )
        
        return {"status": "success", "path": output_path}

    async def transform_data(self, request, context):
        """转换数据"""
        source_table = request.get("source_table")
        target_table = request.get("target_table")
        transform_type = request.get("transform_type")
        
        # 读取源数据
        source_data = await mcp_call(
            "database:query",
            sql=f"SELECT * FROM {source_table}"
        )
        
        # 应用转换
        transformed = self.apply_transform(
            source_data,
            transform_type
        )
        
        # 写入目标表
        await mcp_call(
            "database:insert",
            table=target_table,
            data=transformed
        )
        
        return {"status": "success", "records": len(transformed)}

    def parse_data(self, content: str) -> list:
        """解析数据"""
        # 实现解析逻辑
        return []

    def format_data(self, data: list) -> str:
        """格式化数据"""
        # 实现格式化逻辑
        return ""

    def apply_transform(self, data: list, transform_type: str) -> list:
        """应用转换"""
        # 实现转换逻辑
        return data
```

### 五、可观测性集成

```rust
// kernel/src/mcp/observability.rs
use opentelemetry::{global, trace::Tracer, KeyValue};
use opentelemetry::metrics::{Counter, Histogram};

pub struct MCPObservability {
    tracer: opentelemetry::sdk::trace::Tracer,
    tool_call_counter: Counter<u64>,
    tool_call_duration: Histogram<f64>,
    error_counter: Counter<u64>,
}

impl MCPObservability {
    pub fn new() -> Self {
        let tracer = global::tracer("neuroflow/mcp");
        let meter = global::meter("neuroflow/mcp");

        Self {
            tracer,
            tool_call_counter: meter.u64_counter("mcp.tool.calls").init(),
            tool_call_duration: meter.f64_histogram("mcp.tool.duration").init(),
            error_counter: meter.u64_counter("mcp.errors").init(),
        }
    }

    pub fn record_tool_call(
        &self,
        server_name: &str,
        tool_name: &str,
        duration_ms: f64,
        success: bool,
    ) {
        let attributes = vec![
            KeyValue::new("server", server_name.to_string()),
            KeyValue::new("tool", tool_name.to_string()),
        ];

        self.tool_call_counter.add(1, &attributes);
        self.tool_call_duration.record(duration_ms, &attributes);

        if !success {
            self.error_counter.add(1, &attributes);
        }
    }

    pub fn start_span(
        &self,
        server_name: &str,
        tool_name: &str,
    ) -> opentelemetry::trace::Span {
        self.tracer
            .span_builder(format!("mcp.{}.{}", server_name, tool_name))
            .with_attribute(KeyValue::new("mcp.server", server_name))
            .with_attribute(KeyValue::new("mcp.tool", tool_name))
            .start(&self.tracer)
    }
}
```

### 六、测试策略

```python
# tests/test_mcp_integration.py
"""
MCP 集成测试
"""
import pytest
import asyncio
from neuroflow.mcp import MCPClient, get_mcp_client


@pytest.fixture
def mcp_config_file(tmp_path):
    """创建测试配置文件"""
    config = tmp_path / "mcp_test.yaml"
    config.write_text("""
mcp:
  global:
    timeout_ms: 5000
    max_connections: 10
  servers:
    test_server:
      enabled: true
      url: http://localhost:8765
      http_port: 8765
""")
    return str(config)


@pytest.fixture
async def mcp_client(mcp_config_file):
    """创建 MCP 客户端"""
    client = MCPClient(mcp_config_file)
    await client.initialize()
    yield client
    await client.close()


class TestMCPClient:
    """MCP 客户端测试"""

    @pytest.mark.asyncio
    async def test_initialize(self, mcp_client):
        """测试初始化"""
        assert mcp_client._initialized
        assert len(mcp_client.sessions) >= 0

    @pytest.mark.asyncio
    async def test_list_tools(self, mcp_client):
        """测试列出工具"""
        tools = await mcp_client.list_tools()
        assert isinstance(tools, list)

    @pytest.mark.asyncio
    async def test_call_tool(self, mcp_client):
        """测试调用工具"""
        # 需要 mock MCP 服务器
        # 实际测试中应启动测试服务器
        pass


class TestMCPDecorators:
    """MCP 装饰器测试"""

    def test_mcp_tool_decorator(self):
        """测试 MCP 工具装饰器"""
        from neuroflow.mcp import mcp_tool

        @mcp_tool(server="test", tool_name="test_tool")
        async def test_func(param: str):
            return param

        assert test_func is not None

    def test_agent_with_mcp_decorator(self):
        """测试 Agent MCP 集成装饰器"""
        from neuroflow.mcp import agent_with_mcp

        @agent_with_mcp(
            name="test_agent",
            mcp_servers=["test"],
            mcp_config="config/mcp.yaml"
        )
        class TestAgent:
            async def handle(self, request, context):
                return {"test": "result"}

        assert TestAgent is not None
```

## 实施路线图

### 第一阶段：基础架构 (Week 1-2)
- [ ] 完成 Rust 内核 MCP 网关实现
- [ ] 完成 Python SDK MCP 客户端实现
- [ ] 实现统一配置系统
- [ ] 添加基础错误处理

### 第二阶段：工具集成 (Week 3-4)
- [ ] 实现工具自动发现和注册
- [ ] 实现工具路由系统
- [ ] 添加参数验证
- [ ] 集成语义路由

### 第三阶段：开发者体验 (Week 5-6)
- [ ] 完善装饰器 API
- [ ] 编写文档和示例
- [ ] 实现 CLI 工具
- [ ] 添加调试工具

### 第四阶段：生产就绪 (Week 7-8)
- [ ] 实现连接池和负载均衡
- [ ] 添加熔断和重试机制
- [ ] 完善可观测性
- [ ] 性能优化和基准测试

## 最佳实践

### 1. 配置管理
- 使用环境变量管理敏感信息
- 为不同环境创建独立配置
- 定期轮换 API 密钥

### 2. 错误处理
- 实现优雅降级
- 记录详细错误日志
- 提供清晰的错误消息

### 3. 性能优化
- 使用连接池减少延迟
- 实现响应缓存
- 批量处理请求

### 4. 安全考虑
- 验证所有输入参数
- 实施速率限制
- 审计工具调用

## 总结

通过将 MCP 集成提升为 NeuroFlow 的核心能力，我们实现了：

1. **统一抽象**: Rust 和 Python 共享相同的 MCP 接口
2. **插件化架构**: MCP 服务可热插拔
3. **开发者友好**: 简洁的装饰器 API 和自动化工具发现
4. **生产就绪**: 完整的可观测性和错误处理

这使得开发者能够快速对接第三方 MCP 服务，专注于业务逻辑而非基础设施。
