# NeuroFlow MCP 开发者指南

## 目录

1. [概述](#概述)
2. [快速开始](#快速开始)
3. [核心概念](#核心概念)
4. [配置指南](#配置指南)
5. [使用 MCP 工具](#使用-mcp 工具)
6. [创建自定义 MCP 服务](#创建自定义-mcp 服务)
7. [最佳实践](#最佳实践)
8. [故障排除](#故障排除)

## 概述

### 什么是 MCP？

MCP (Model Context Protocol) 是一个开放协议，用于标准化 AI 模型与外部工具、资源和提示词的交互。NeuroFlow 将 MCP 集成作为核心能力，使开发者能够：

- **快速对接**第三方 MCP 服务（文件系统、数据库、API 等）
- **统一管理**多个 MCP 服务器的配置和连接
- **自动发现**工具并生成类型安全的调用接口
- **无缝集成**到 Agent 工作流中

### 架构设计

```
┌─────────────────────────────────────────┐
│         NeuroFlow Application           │
├─────────────────────────────────────────┤
│  Python SDK                             │
│  ┌─────────────────────────────────┐   │
│  │  @mcp_tool  @agent_with_mcp     │   │
│  │  MCPClient (统一 API)            │   │
│  └─────────────────────────────────┘   │
├─────────────────────────────────────────┤
│  Rust Kernel                            │
│  ┌─────────────────────────────────┐   │
│  │  MCP Gateway                    │   │
│  │  - 连接池管理                   │   │
│  │  - 工具路由                     │   │
│  │  - 负载均衡                     │   │
│  └─────────────────────────────────┘   │
├─────────────────────────────────────────┤
│  External MCP Servers                   │
│  ┌───────┐ ┌───────┐ ┌───────┐        │
│  │ File  │ │ DB    │ │ API   │        │
│  └───────┘ └───────┘ └───────┘        │
└─────────────────────────────────────────┘
```

### 核心特性

- ✅ **统一配置**: YAML 配置文件管理所有 MCP 服务
- ✅ **自动发现**: 启动时自动获取并注册可用工具
- ✅ **类型安全**: 自动生成参数验证和类型检查
- ✅ **连接池**: 高效的连接复用和负载均衡
- ✅ **错误处理**: 完善的错误分类和重试机制
- ✅ **可观测性**: 完整的指标收集和链路追踪

## 快速开始

### 1. 安装依赖

```bash
# 安装 NeuroFlow SDK（包含 MCP 支持）
pip install neuroflow[mcp]

# 或者从源码安装
cd /path/to/NeuroFlow/sdk
pip install -e .
```

### 2. 创建配置文件

创建 `config/mcp.yaml`:

```yaml
mcp:
  global:
    timeout_ms: 30000
    max_connections: 100
  
  servers:
    filesystem:
      enabled: true
      command: npx
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"]
      http_port: 8081
      description: "文件系统服务"
```

### 3. 使用 MCP 工具

```python
from neuroflow.mcp import get_mcp_client

# 创建客户端
client = get_mcp_client("config/mcp.yaml")
await client.initialize()

# 列出所有工具
tools = await client.list_tools()
print(f"可用工具：{[t.name for t in tools]}")

# 调用工具
result = await client.call_tool(
    "filesystem:read_file",
    path="/workspace/data.txt"
)
print(f"文件内容：{result}")

# 清理
await client.close()
```

### 4. 在 Agent 中集成

```python
from neuroflow.mcp import agent_with_mcp

@agent_with_mcp(
    name="file_agent",
    mcp_servers=["filesystem"],
    mcp_config="config/mcp.yaml"
)
class FileAgent:
    async def handle(self, request, context):
        mcp = context.mcp_client
        content = await mcp.call_tool(
            "filesystem:read_file",
            path=request.get("path")
        )
        return {"content": content}
```

## 核心概念

### MCP 服务器 (Server)

MCP 服务器是提供工具、资源和提示词的服务端。可以是：

- **官方服务器**: 如 `@modelcontextprotocol/server-filesystem`
- **第三方服务器**: 社区开发的各类服务
- **自定义服务器**: 自己开发的服务

### MCP 工具 (Tool)

工具是 MCP 服务器提供的可调用函数，具有：

- **名称**: 唯一标识符
- **描述**: 功能说明
- **参数模式**: JSON Schema 定义
- **执行逻辑**: 实际的业务实现

### MCP 资源 (Resource)

资源是 MCP 服务器提供的数据源，如：

- 文件内容 (`file:///path/to/file`)
- 数据库记录 (`db://table/id`)
- API 响应 (`https://api.example.com/data`)

### MCP 提示词 (Prompt)

提示词是预定义的模板，用于：

- 标准化常见任务
- 提供上下文信息
- 优化模型输出

## 配置指南

### 配置文件结构

```yaml
mcp:
  # 全局设置
  global:
    timeout_ms: 30000          # 默认超时（毫秒）
    max_connections: 100       # 最大并发连接数
    retry_attempts: 3          # 重试次数
    api_key: ${MCP_API_KEY}    # 支持环境变量
  
  # 服务器配置
  servers:
    <server_name>:
      enabled: true            # 是否启用
      command: npx             # 启动命令
      args: [...]              # 命令参数
      url: https://...         # 或远程 URL
      http_port: 8081          # HTTP 端口
      description: "..."       # 描述信息
      auth:                    # 认证配置（可选）
        type: bearer
        token: ${TOKEN}
      tools:                   # 启用的工具列表（可选）
        - tool1
        - tool2
      resources:               # 资源配置（可选）
        - pattern: "file:///*"
          cache_ttl: 300
```

### 环境变量

使用 `${VAR_NAME}` 语法引用环境变量：

```yaml
mcp:
  global:
    api_key: ${MCP_API_KEY}
    api_secret: ${MCP_API_SECRET}
  
  servers:
    database:
      args: ["--uri", "${DATABASE_URL}"]
```

### 多环境配置

```bash
# 开发环境
config/mcp.dev.yaml

# 生产环境
config/mcp.prod.yaml

# 测试环境
config/mcp.test.yaml
```

在代码中根据环境加载：

```python
import os
env = os.getenv('NEUROFLOW_ENV', 'dev')
client = get_mcp_client(f"config/mcp.{env}.yaml")
```

## 使用 MCP 工具

### 方式一：直接使用客户端

```python
from neuroflow.mcp import get_mcp_client

client = get_mcp_client("config/mcp.yaml")
await client.initialize()

# 调用工具
result = await client.call_tool(
    "database:query",
    sql="SELECT * FROM users"
)

await client.close()
```

### 方式二：使用装饰器

```python
from neuroflow.mcp import mcp_tool

@mcp_tool(
    server="database",
    tool_name="query",
    description="执行 SQL 查询"
)
async def query_database(sql: str) -> list:
    """查询数据库"""
    pass

# 直接使用
results = await query_database(sql="SELECT * FROM users")
```

### 方式三：便捷函数

```python
from neuroflow.mcp import mcp_call

# 快速调用
result = await mcp_call(
    "filesystem:read_file",
    path="/workspace/data.txt"
)
```

### 方式四：Agent 集成

```python
from neuroflow.mcp import agent_with_mcp

@agent_with_mcp(
    name="data_agent",
    mcp_servers=["database", "filesystem"],
    mcp_config="config/mcp.yaml"
)
class DataAgent:
    async def handle(self, request, context):
        mcp = context.mcp_client
        
        # 读取文件
        content = await mcp.call_tool(
            "filesystem:read_file",
            path="data.json"
        )
        
        # 处理数据
        data = self.process(content)
        
        # 存入数据库
        await mcp.call_tool(
            "database:insert",
            table="processed_data",
            data=data
        )
        
        return {"status": "success"}
    
    def process(self, content):
        # 业务逻辑
        pass
```

### 错误处理

```python
from neuroflow.mcp import (
    MCPError,
    MCPTimeoutError,
    MCPNotFoundError,
    MCPConnectionError
)

try:
    result = await client.call_tool("database:query", sql="...")
except MCPNotFoundError as e:
    # 工具不存在
    print(f"工具未找到：{e}")
except MCPTimeoutError as e:
    # 请求超时
    print(f"请求超时：{e}")
except MCPConnectionError as e:
    # 连接失败
    print(f"连接失败：{e}")
except MCPError as e:
    # 其他 MCP 错误
    print(f"MCP 错误：{e}")
except Exception as e:
    # 未知错误
    print(f"未知错误：{e}")
```

### 并发调用

```python
import asyncio
from neuroflow.mcp import get_mcp_client

client = get_mcp_client("config/mcp.yaml")
await client.initialize()

# 并发执行多个调用
tasks = [
    client.call_tool("filesystem:read_file", path="file1.txt"),
    client.call_tool("filesystem:read_file", path="file2.txt"),
    client.call_tool("database:query", sql="SELECT ..."),
]

results = await asyncio.gather(*tasks, return_exceptions=True)

for i, result in enumerate(results):
    if isinstance(result, Exception):
        print(f"任务 {i} 失败：{result}")
    else:
        print(f"任务 {i} 结果：{result}")

await client.close()
```

## 创建自定义 MCP 服务

### 基础示例

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
            description="问候某人",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "被问候的人"
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
                text=f"你好，{arguments['name']}!"
            )
        ]
    raise ValueError(f"未知工具：{name}")

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
      http_port: 8090
      description: "自定义问候服务"
```

### 高级示例：带资源的服务

```python
from mcp.server import Server
from mcp.types import Tool, Resource, TextContent

server = Server("data-server")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="process_data",
            description="处理数据",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {"type": "array"},
                    "operation": {"type": "string"}
                },
                "required": ["data", "operation"]
            }
        )
    ]

@server.list_resources()
async def list_resources():
    return [
        Resource(
            uri="data://config/default",
            name="默认配置",
            description="默认数据处理配置",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def read_resource(uri: str):
    if uri == "data://config/default":
        return '{"version": "1.0", "settings": {}}'
    raise ValueError(f"未知资源：{uri}")

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "process_data":
        data = arguments.get("data", [])
        operation = arguments.get("operation", "")
        
        # 处理逻辑
        result = self.process(data, operation)
        
        return [
            TextContent(
                type="text",
                text=f"处理完成：{result}"
            )
        ]
    raise ValueError(f"未知工具：{name}")
```

## 最佳实践

### 1. 配置管理

```yaml
# ✅ 好的做法：使用环境变量
mcp:
  global:
    api_key: ${MCP_API_KEY}
  servers:
    database:
      args: ["--uri", "${DATABASE_URL}"]

# ❌ 避免：硬编码敏感信息
mcp:
  global:
    api_key: "sk-1234567890"
```

### 2. 错误处理

```python
# ✅ 好的做法：细粒度错误处理
try:
    result = await client.call_tool("db:query", sql=sql)
except MCPNotFoundError:
    logger.error("工具不存在")
except MCPTimeoutError:
    logger.warning("请求超时，将重试")
    result = await retry_call(...)
except Exception as e:
    logger.error(f"未知错误：{e}")
    raise

# ❌ 避免：捕获所有异常但不处理
try:
    result = await client.call_tool(...)
except:
    pass
```

### 3. 连接管理

```python
# ✅ 好的做法：使用上下文管理器
async with get_mcp_client("config/mcp.yaml") as client:
    result = await client.call_tool(...)
# 自动关闭连接

# ✅ 好的做法：显式关闭
client = get_mcp_client(...)
try:
    await client.initialize()
    result = await client.call_tool(...)
finally:
    await client.close()

# ❌ 避免：忘记关闭连接
client = get_mcp_client(...)
await client.initialize()
result = await client.call_tool(...)
# 连接泄漏
```

### 4. 性能优化

```python
# ✅ 好的做法：复用客户端实例
# 在应用启动时创建全局客户端
_mcp_client = None

def get_client():
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = get_mcp_client("config/mcp.yaml")
        asyncio.run(_mcp_client.initialize())
    return _mcp_client

# ❌ 避免：频繁创建和销毁
async def handle_request():
    client = get_mcp_client(...)
    await client.initialize()
    result = await client.call_tool(...)
    await client.close()
```

### 5. 工具命名

```python
# ✅ 好的做法：使用描述性名称
@server.list_tools()
async def list_tools():
    return [
        Tool(name="user:create", ...),
        Tool(name="user:delete", ...),
        Tool(name="report:generate", ...),
    ]

# ❌ 避免：模糊的名称
@server.list_tools()
async def list_tools():
    return [
        Tool(name="tool1", ...),
        Tool(name="tool2", ...),
    ]
```

## 故障排除

### 常见问题

#### 1. 连接失败

**症状**: `MCPConnectionError: Failed to connect to server`

**解决方案**:
```bash
# 检查服务器是否运行
neuroflow mcp health-check

# 查看服务器日志
neuroflow logs --component mcp

# 验证配置
neuroflow mcp list-servers
```

#### 2. 工具未找到

**症状**: `MCPNotFoundError: Tool 'xxx' not found`

**解决方案**:
```bash
# 列出所有可用工具
neuroflow mcp list-tools

# 检查工具名称是否正确
neuroflow mcp info <server_name>
```

#### 3. 超时错误

**症状**: `MCPTimeoutError: Request timed out`

**解决方案**:
```yaml
# 增加超时时间
mcp:
  global:
    timeout_ms: 60000  # 增加到 60 秒
```

#### 4. 认证失败

**症状**: `MCPError: Authentication failed`

**解决方案**:
```bash
# 检查环境变量
echo $MCP_API_KEY

# 验证配置文件
neuroflow mcp info <server_name>
```

### 调试技巧

#### 启用详细日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 或在配置文件中设置
mcp:
  global:
    log_level: DEBUG
```

#### 使用 CLI 工具测试

```bash
# 列出工具
neuroflow mcp list-tools --format table

# 调用工具
neuroflow mcp call-tool \
  --server filesystem \
  --tool read_file \
  --args path=/workspace/test.txt

# 健康检查
neuroflow mcp health-check
```

#### 捕获完整堆栈

```python
import traceback

try:
    result = await client.call_tool(...)
except Exception as e:
    print(f"错误：{e}")
    traceback.print_exc()
```

## 总结

NeuroFlow 的 MCP 集成提供了：

1. **统一配置**: 通过 YAML 文件管理所有 MCP 服务
2. **简洁 API**: 装饰器和客户端两种使用方式
3. **自动发现**: 启动时自动获取并注册工具
4. **生产就绪**: 完善的错误处理和可观测性

通过遵循本指南，您可以快速对接第三方 MCP 服务，构建强大的 AI Agent 应用。

## 更多资源

- [MCP 规范文档](https://modelcontextprotocol.io/)
- [官方 MCP 服务器列表](https://github.com/modelcontextprotocol/servers)
- [NeuroFlow 示例项目](examples/mcp_integration/)
- [API 参考文档](sdk/neuroflow/mcp.py)
