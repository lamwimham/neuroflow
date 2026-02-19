# NeuroFlow v0.4.2 - Quick Start Guide

**Version**: v0.4.2  
**Release Date**: 2026-03-05  
**Status**: ✅ Production Ready

---

## 🚀 What's New in v0.4.2

v0.4.2 "Real Connection" brings **production-ready MCP integration** and **real A2A communication** to NeuroFlow.

### Key Features

1. **Real MCP Integration** - Connect to official MCP servers
2. **A2A HTTP Communication** - Real agent-to-agent collaboration
3. **Agent Registry** - Memory and Redis-backed registries
4. **Health Monitoring** - Automatic health checks and circuit breakers
5. **Depth Limiting** - Prevent infinite recursion in collaboration

---

## 📦 Installation

### Prerequisites

- Python 3.9+
- Node.js 16+ (for MCP servers)
- Redis 6+ (optional, for distributed registry)

### Install SDK

```bash
cd sdk
pip install -e .
```

### Install Optional Dependencies

```bash
# For Redis support
pip install redis

# For MCP servers (optional - SDK will work without)
npm install -g @modelcontextprotocol/server-filesystem
npm install -g @modelcontextprotocol/server-memory
```

---

## 🎯 Quick Start Examples

### 1. Real MCP Integration

```python
import asyncio
from neuroflow.mcp import MCPServerManager

async def main():
    # Create manager
    manager = MCPServerManager()
    
    # Start from config (see config example below)
    await manager.start_from_config(config)
    
    # Execute tools
    result = await manager.execute_tool(
        server_name="filesystem",
        tool_name="read_file",
        arguments={"path": "/tmp/test.txt"},
    )
    
    print(result["result"])

asyncio.run(main())
```

### 2. A2A Agent Registry

```python
import asyncio
from neuroflow.a2a import AgentRegistryService, AgentRegistration

async def main():
    # Create registry
    registry = AgentRegistryService(backend="memory")
    await registry.start()
    
    # Register an agent
    agent = AgentRegistration(
        id="researcher",
        name="Research Agent",
        description="Web research specialist",
        endpoint="http://localhost:8081",
        capabilities=["web_search", "research"],
    )
    await registry.register(agent)
    
    # Discover agents
    researchers = await registry.discover_by_capability("web_search")
    print(f"Found {len(researchers)} researchers")
    
    await registry.stop()

asyncio.run(main())
```

### 3. Multi-Agent Collaboration

```python
import asyncio
from neuroflow.a2a import (
    AgentRegistryService,
    CollaborativeOrchestratorV2,
)
from neuroflow.orchestrator import LLMOrchestrator, LLMConfig

async def main():
    # Setup registry
    registry = AgentRegistryService(backend="memory")
    await registry.start()
    
    # Register agents
    # ... (see example 2)
    
    # Create orchestrator
    llm_config = LLMConfig(provider="openai", model="gpt-4")
    llm_orchestrator = LLMOrchestrator(llm_config=llm_config)
    
    orchestrator = CollaborativeOrchestratorV2(
        llm_orchestrator=llm_orchestrator,
        agent_registry_service=registry,
        max_depth=5,  # Prevent infinite recursion
        timeout_ms=30000,  # 30 second timeout
    )
    
    # Execute with collaboration
    result = await orchestrator.execute_with_collaboration(
        user_message="Research AI agents and write a summary",
    )
    
    print(result.response)
    
    await registry.stop()

asyncio.run(main())
```

---

## 📚 Complete Examples

Run the complete feature demonstration:

```bash
cd sdk
python examples/v042_complete_example.py
```

This example demonstrates:
- ✅ Real MCP filesystem and memory servers
- ✅ A2A agent registration and discovery
- ✅ Collaboration depth limiting
- ✅ Health monitoring and circuit breakers

---

## 🧪 Running Tests

### MCP Integration Tests

```bash
cd sdk
python tests/mcp/test_simple.py
```

### A2A Communication Tests

```bash
python tests/a2a/test_simple.py
```

### All Tests

```bash
pytest tests/ -v
```

---

## 📖 Configuration

### MCP Configuration (config.yaml)

```yaml
mcp:
  enabled: true
  servers:
    - name: filesystem
      enabled: true
      config:
        allowed_paths:
          - /tmp
          - ./data
    
    - name: memory
      enabled: true
      config:
        db_path: ./memory.db
    
    - name: terminal
      enabled: true
      config:
        mode: restricted
        allowed_commands:
          - ls
          - cat
          - pwd
```

### Load Configuration

```python
from neuroflow.mcp import MCPConfigParser

parser = MCPConfigParser()
config = parser.parse_from_file("config.yaml")

manager = MCPServerManager()
await manager.start_from_config(config)
```

---

## 🔧 API Reference

### MCP Module

```python
from neuroflow.mcp import (
    # Core
    RealMCPExecutor,
    MCPServerManager,
    
    # Health & Reliability
    MCPHealthMonitor,
    RetryConfig,
    HealthStatus,
)
```

### A2A Module

```python
from neuroflow.a2a import (
    # Registry
    AgentRegistryService,
    AgentRegistration,
    MemoryRegistry,
    RedisRegistry,
    
    # Protocol
    A2AHTTPClient,
    A2AProtocol,
    A2AMessage,
    AssistRequest,
    AssistResponse,
    
    # Collaboration
    CollaborativeOrchestratorV2,
    CollaborationContext,
)
```

---

## 🎯 Key Concepts

### 1. Real MCP Integration

v0.4.2 replaces all mock MCP implementations with real connections using the official [Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk).

**Benefits:**
- Production-ready file operations
- Real memory persistence
- Automatic tool discovery
- Standard protocol compliance

### 2. Agent Registry Service

Centralized registry for agent discovery and communication.

**Backends:**
- **Memory**: Lightweight, single-machine
- **Redis**: Distributed, production-ready

**Features:**
- Capability-based discovery
- Health monitoring
- Automatic deregistration

### 3. Collaboration Context

Tracks collaboration depth and prevents infinite recursion.

```python
context = CollaborationContext(
    request_id="unique-id",
    current_depth=0,
    max_depth=5,  # Prevent infinite loops
    timeout_ms=30000,  # Timeout control
)

# Check if collaboration is allowed
if context.can_collaborate("agent2"):
    # Create child context for nested collaboration
    child_context = context.create_child("agent2")
```

### 4. Circuit Breaker Pattern

Automatic fault isolation for failing agents.

**Behavior:**
- Opens after 5 consecutive failures
- Auto-recovery after 60 seconds
- Prevents cascade failures

---

## ⚠️ Migration from v0.4.1

### MCP Changes

**Good news**: No code changes required! The MCP module is backward compatible.

```python
# v0.4.1 code still works
from neuroflow.mcp import MCPServerManager

manager = MCPServerManager()
# Now uses real MCP SDK automatically
```

### A2A Changes

For new projects, use the enhanced v2 orchestrator:

```python
# Old (still works)
from neuroflow.a2a import CollaborativeOrchestrator

# New (recommended)
from neuroflow.a2a import CollaborativeOrchestratorV2

orchestrator = CollaborativeOrchestratorV2(
    llm_orchestrator=llm_orchestrator,
    agent_registry_service=registry,
    max_depth=5,
    timeout_ms=30000,
)
```

---

## 🐛 Troubleshooting

### MCP Server Won't Start

**Issue**: `Failed to start MCP server`

**Solutions:**
1. Ensure Node.js 16+ is installed
2. Check npx is available: `npx --version`
3. Verify allowed paths exist

### Redis Connection Failed

**Issue**: `Failed to connect to Redis`

**Solutions:**
1. Install redis package: `pip install redis`
2. Ensure Redis server is running
3. Check Redis URL format: `redis://localhost:6379`

### Collaboration Timeout

**Issue**: `Collaboration timeout (30000ms)`

**Solutions:**
1. Increase timeout: `timeout_ms=60000`
2. Check agent endpoints are accessible
3. Verify network connectivity

---

## 📞 Support

- **Documentation**: `docs/RELEASE_NOTES_v0.4.2.md`
- **Examples**: `sdk/examples/v042_complete_example.py`
- **Tests**: `sdk/tests/mcp/`, `sdk/tests/a2a/`
- **Issues**: https://github.com/lamwimham/neuroflow/issues
- **Discussions**: https://github.com/lamwimham/neuroflow/discussions

---

## 🎉 Next Steps

Now that you have v0.4.2 running:

1. **Try the complete example**: `python examples/v042_complete_example.py`
2. **Read the release notes**: `docs/RELEASE_NOTES_v0.4.2.md`
3. **Explore the API**: Check out the module docstrings
4. **Build your own agents**: Start creating multi-agent systems!

---

**Happy Coding! 🚀**

*NeuroFlow v0.4.2 - Real Connection*
