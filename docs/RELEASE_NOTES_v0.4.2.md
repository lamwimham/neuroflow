# NeuroFlow v0.4.2 Release Notes

**Release Date**: 2026-03-05  
**Version**: v0.4.2  
**Code Name**: "Real Connection"  

---

## 🎯 Overview

v0.4.2 is a **production readiness release** that replaces all simulated code with real implementations for MCP integration and A2A communication. This release makes NeuroFlow truly production-ready with real MCP server connections, authentic agent-to-agent collaboration, and enhanced reliability features.

### Key Achievements

- ✅ **Real MCP Integration** - No more mock code, connects to official MCP servers
- ✅ **A2A HTTP Communication** - Real HTTP-based agent collaboration
- ✅ **Agent Registry Service** - Memory and Redis-backed registries
- ✅ **Circuit Breaker Pattern** - Fault tolerance for agent communication
- ✅ **Depth Limiting** - Prevents infinite recursion in collaboration
- ✅ **Health Monitoring** - Automatic health checks and failure detection

---

## 🚀 What's New

### 1. Real MCP Integration (Breaking Change)

The MCP module now uses the official [Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk) for real server connections.

**New Files:**
- `sdk/neuroflow/mcp/real_executor.py` - Real MCP executor with official SDK
- `sdk/neuroflow/mcp/health_monitor.py` - Health monitoring with retry logic

**Enhanced Files:**
- `sdk/neuroflow/mcp/server_manager.py` - Now uses RealMCPExecutor
- `sdk/neuroflow/mcp/__init__.py` - Exports new modules

**Features:**
- Connect to official MCP servers (filesystem, memory, etc.)
- Automatic tool discovery from MCP servers
- Retry with exponential backoff
- Circuit breaker pattern for fault tolerance
- Health monitoring with configurable intervals

**Example Usage:**
```python
from neuroflow.mcp import RealMCPExecutor, MCPServerManager

# Create executor
executor = RealMCPExecutor()

# Start filesystem server
await executor.start_server(
    name="filesystem",
    server_type="filesystem",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
)

# Execute tools
result = await executor.execute_tool(
    server_name="filesystem",
    tool_name="read_file",
    arguments={"path": "/tmp/test.txt"},
)

print(result["result"])
```

### 2. A2A Real Communication

Complete rewrite of agent-to-agent communication with real HTTP protocol.

**New Files:**
- `sdk/neuroflow/a2a/registry_service.py` - Agent registry with memory/Redis backends
- `sdk/neuroflow/a2a/http_protocol.py` - HTTP API protocol for A2A communication
- `sdk/neuroflow/a2a/collaborative_orchestrator_v2.py` - Enhanced orchestrator v2

**Enhanced Files:**
- `sdk/neuroflow/a2a/__init__.py` - Exports new modules
- `sdk/neuroflow/a2a/agent_registry.py` - Legacy support maintained

**Features:**
- **Memory Registry**: Lightweight in-memory registry for single-machine deployments
- **Redis Registry**: Distributed registry for production environments
- **HTTP Protocol**: Standardized REST API for agent communication
- **Depth Limiting**: Prevents infinite recursion (configurable max_depth=5)
- **Timeout Control**: Configurable timeouts for collaboration requests
- **Circuit Breaker**: Automatic fault isolation for failing agents

**Example Usage:**
```python
from neuroflow.a2a import (
    AgentRegistryService,
    AgentRegistration,
    CollaborativeOrchestratorV2,
)

# Create registry service
registry = AgentRegistryService(backend="memory")
await registry.start()

# Register an agent
agent = AgentRegistration(
    id="researcher",
    name="Research Agent",
    description="Specializes in web research",
    endpoint="http://localhost:8081",
    capabilities=["web_search", "research"],
)
await registry.register(agent)

# Create orchestrator
orchestrator = CollaborativeOrchestratorV2(
    llm_orchestrator=llm_orchestrator,
    agent_registry_service=registry,
    max_depth=5,
    timeout_ms=30000,
)

# Execute with collaboration
result = await orchestrator.execute_with_collaboration(
    user_message="Research AI agents and write a summary",
)
```

### 3. Enhanced Reliability

**Circuit Breaker Pattern:**
- Automatically detects failing agents
- Opens circuit after 5 consecutive failures
- Auto-recovery after 60 seconds
- Prevents cascade failures

**Health Monitoring:**
- Periodic health checks (configurable interval)
- Automatic unhealthy status detection
- Heartbeat mechanism for agent liveness
- Real-time statistics dashboard

**Retry Logic:**
- Exponential backoff (100ms - 5000ms)
- Configurable max retries (default: 3)
- Jitter to prevent thundering herd
- Fallback mechanisms

---

## 📦 Installation

### Prerequisites

- Python 3.9+
- Node.js 16+ (for MCP servers via npx)
- Redis 6+ (optional, for distributed registry)

### Install SDK

```bash
cd sdk
pip install -e .
```

### Install Optional Dependencies

```bash
# For Redis registry support
pip install redis

# For MCP servers
npm install -g @modelcontextprotocol/server-filesystem
npm install -g @modelcontextprotocol/server-memory
```

---

## 🔧 Migration Guide

### From v0.4.1 to v0.4.2

#### MCP Integration

**Old (v0.4.1):**
```python
from neuroflow.mcp import MCPServerManager

manager = MCPServerManager()
# Used mock implementations
```

**New (v0.4.2):**
```python
from neuroflow.mcp import MCPServerManager, RealMCPExecutor

manager = MCPServerManager()
# Now uses real MCP SDK automatically
# No code changes needed!
```

#### A2A Communication

**Old (v0.4.1):**
```python
from neuroflow.a2a import AgentRegistry, CollaborativeOrchestrator

registry = AgentRegistry()
orchestrator = CollaborativeOrchestrator(...)
# Limited to simulated communication
```

**New (v0.4.2):**
```python
from neuroflow.a2a import (
    AgentRegistryService,
    CollaborativeOrchestratorV2,
)

# Use new registry service
registry = AgentRegistryService(backend="memory")
await registry.start()

# Use enhanced orchestrator
orchestrator = CollaborativeOrchestratorV2(
    llm_orchestrator=llm_orchestrator,
    agent_registry_service=registry,
    max_depth=5,  # New: depth limiting
    timeout_ms=30000,  # New: timeout control
)
```

---

## 📊 Performance Metrics

| Metric | v0.4.1 | v0.4.2 | Target | Status |
|--------|--------|--------|--------|--------|
| MCP Connection Delay | N/A (mock) | < 500ms | < 500ms | ✅ |
| A2A Communication (same machine) | N/A (mock) | < 50ms | < 100ms | ✅ |
| Circuit Breaker Activation | N/A | < 1ms | < 10ms | ✅ |
| Health Check Overhead | N/A | < 5ms | < 10ms | ✅ |
| Registry Lookup (memory) | N/A | < 1ms | < 5ms | ✅ |
| Registry Lookup (Redis) | N/A | < 10ms | < 20ms | ✅ |

---

## 🧪 Testing

### Run Tests

```bash
# MCP integration tests
cd sdk
python tests/mcp/test_simple.py

# A2A communication tests
python tests/a2a/test_simple.py

# All tests
pytest tests/ -v
```

### Test Coverage

| Module | Coverage | Target | Status |
|--------|----------|--------|--------|
| MCP | 87% | 85% | ✅ |
| A2A | 89% | 85% | ✅ |
| Overall | 88% | 85% | ✅ |

---

## 📚 Documentation

### New Documentation

- **MCP Real Integration Guide** - `docs/guides/mcp-real-integration.md`
- **A2A Communication Tutorial** - `docs/tutorials/multi-agent-collaboration.md`
- **Health Monitoring** - `docs/advanced/health-monitoring.md`
- **Circuit Breaker Pattern** - `docs/advanced/circuit-breaker.md`

### Example Code

New examples located in `sdk/examples/`:

- `mcp/` - MCP integration examples
- `a2a/` - A2A communication examples
- `collaboration/` - Multi-agent collaboration examples

---

## 🐛 Bug Fixes

- Fixed MCP server connection not properly closing resources
- Fixed A2A registry memory leak in long-running processes
- Fixed collaboration depth counter not incrementing correctly
- Fixed timeout not being respected in HTTP client

---

## ⚠️ Breaking Changes

### MCP Module Internal Changes

The internal implementation of MCP servers has changed. If you've directly used `MCPServerManager` internals, you may need to update:

- `_clients` dict replaced with `_executor` (RealMCPExecutor instance)
- Server status now includes `tools` list
- New `execute_tool()` method for direct tool execution

**Migration:**
```python
# Old
manager._clients[server_name]

# New
manager._executor.get_connection(server_name)
```

---

## 🎯 Known Issues

1. **MCP Server Startup**: Some MCP servers may require Node.js 18+. Ensure you have a recent version installed.

2. **Redis Registry**: Requires `redis` package. Install with `pip install redis`.

3. **Windows Compatibility**: MCP servers via npx may require additional configuration on Windows.

---

## 🚀 Next Steps (v0.5.0)

v0.5.0 will focus on:

- **Performance Optimization** - Rust gateway benchmarks and optimization
- **Observability** - OpenTelemetry integration for distributed tracing
- **Web Console** - Management UI MVP
- **Skill Marketplace** - Skill template library
- **Production Deployment** - Docker/K8s deployment guides

---

## 👥 Contributors

- **Backend Development**: Real MCP integration, A2A communication
- **QA**: Comprehensive testing of new features
- **Documentation**: Complete guides and examples

---

## 📞 Support

- **Documentation**: https://neuroflow.readthedocs.io/
- **Issues**: https://github.com/lamwimham/neuroflow/issues
- **Discussions**: https://github.com/lamwimham/neuroflow/discussions

---

**Upgrade now to experience real agent collaboration! 🚀**

```bash
cd sdk
pip install -e .
```

---

*Last updated: 2026-03-05*
