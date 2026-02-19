# NeuroFlow Memory 集成指南

**状态**: ✅ 代码完成，待集成  
**日期**: 2026-03-20

---

## 🚀 快速集成步骤

### 1. 更新 kernel/src/main.rs

在 `run_server()` 函数中，添加以下代码（在启动 HTTP 服务器之前）：

```rust
// ========== 初始化 Memory 模块 ==========
info!("Initializing Memory module...");
let memory_config = MemoryConfig::default();
let memory_manager = Arc::new(MemoryManager::new(
    Arc::new(InMemoryBackend::new(memory_config.clone())),
    memory_config,
));
info!("Memory module initialized");

// ========== 初始化 MCP 模块 ==========
info!("Initializing MCP module...");
let mcp_service = Arc::new(MCPService::new(crate::mcp::MCPConfig::default()));
info!("MCP module initialized");

// ========== 创建 Memory 服务（带 Knowledge Extractor） ==========
info!("Creating Memory Service with Knowledge Extractor...");
let memory_service = Arc::new(
    MemoryService::new(memory_manager.clone())
        .with_knowledge_extractor(mcp_service.clone())
);
info!("Memory Service created");
```

### 2. 更新 HTTP 服务器启动代码

替换原有的 `start_http_server` 调用：

```rust
// 原代码:
// let http_future = start_http_server(config.server.host.clone(), config.server.port);

// 新代码:
let http_addr = format!("{}:{}", config.server.host, config.server.port);
let memory_service_data = web::Data::new(memory_service);

let http_future = async move {
    HttpServer::new(move || {
        App::new()
            .app_data(memory_service_data.clone())
            .configure(configure_memory_routes)  // ← 添加 Memory 路由
            .configure(kernel::gateway::configure_routes)  // 原有路由
    })
    .bind(&http_addr)?
    .run()
    .await
};
```

### 3. 添加必要的 import

在 `main.rs` 顶部添加：

```rust
use kernel::{
    memory::{MemoryManager, InMemoryBackend, MemoryConfig},
    mcp::MCPService,
    grpc::{MemoryService, configure_memory_routes},
};
use std::sync::Arc;
use actix_web::{App, HttpServer, web};
```

---

## 🧪 测试 Memory 服务

### 启动服务器

```bash
cd kernel
cargo run -- --http-port 8080 --grpc-port 50051
```

### 测试 API

#### 1. 存储记忆

```bash
curl -X POST http://localhost:8080/api/memory/store \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "user-123",
    "key": "preference:theme",
    "value": {"theme": "dark", "lang": "zh"},
    "tags": ["preference", "ui"],
    "importance": 0.8
  }'
```

**响应**:
```json
{
  "success": true,
  "memory_id": "abc-123-def",
  "error": null
}
```

#### 2. 检索记忆

```bash
curl -X POST http://localhost:8080/api/memory/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "user-123",
    "key": "preference:theme"
  }'
```

**响应**:
```json
{
  "found": true,
  "entry": {
    "id": "abc-123-def",
    "agent_id": "user-123",
    "key": "preference:theme",
    "value": {"theme": "dark", "lang": "zh"},
    "importance": 0.8,
    "tags": ["preference", "ui"]
  },
  "error": null
}
```

#### 3. 搜索记忆

```bash
curl -X POST http://localhost:8080/api/memory/search \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "user-123",
    "tags": ["preference"],
    "min_importance": 0.5,
    "limit": 10
  }'
```

#### 4. 提取知识

```bash
curl -X POST http://localhost:8080/api/memory/extract \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "user-123",
    "conversation_id": "conv-001",
    "conversation_text": "User: 我在北京工作，是软件工程师\nAssistant: 很好！您用什么编程语言？\nUser: 主要用 Python，喜欢 Django 和 FastAPI"
  }'
```

**响应**:
```json
{
  "success": true,
  "knowledge_count": 3,
  "memories": [
    {
      "id": "...",
      "key": "knowledge:personal_info:user_location",
      "value": {"city": "北京", "country": "中国"},
      "importance": 0.95,
      "tags": ["personal_info", "knowledge"]
    },
    {
      "id": "...",
      "key": "knowledge:skill:programming_languages",
      "value": {"languages": ["Python"]},
      "importance": 0.9,
      "tags": ["skill", "knowledge"]
    }
  ],
  "error": null
}
```

#### 5. 保存对话

```bash
curl -X POST http://localhost:8080/api/memory/conversation \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "user-123",
    "conversation_id": "conv-001",
    "turns": [
      {"role": "user", "content": "你好"},
      {"role": "assistant", "content": "你好！有什么可以帮助你的？"}
    ]
  }'
```

---

## 🐛 常见问题

### 1. 编译错误：找不到模块

**错误**: `error[E0432]: unresolved import kernel::memory`

**解决**: 确保 `kernel/src/lib.rs` 中导出了模块：

```rust
pub mod memory;
pub mod knowledge;
pub mod mcp;
pub mod grpc;
```

### 2. 运行时错误：端口被占用

**错误**: `error: Address already in use`

**解决**: 更换端口：

```bash
cargo run -- --http-port 8081 --grpc-port 50052
```

### 3. Memory 服务未响应

**检查**:
1. 服务器日志中是否有 "Memory Service created"
2. HTTP 路由是否正确注册
3. 防火墙是否阻止端口

---

## 📝 Python SDK 使用

### 安装依赖

```bash
cd sdk
pip install -e .
pip install grpcio grpcio-tools
```

### 使用示例

```python
from neuroflow.memory import KernelMemoryClient

# 创建客户端
client = KernelMemoryClient(endpoint="localhost:8080")

# 存储记忆
memory_id = await client.store(
    agent_id="user-123",
    key="preference:theme",
    value={"theme": "dark"},
    tags=["preference"],
    importance=0.8,
)

# 检索记忆
pref = await client.retrieve("user-123", "preference:theme")

# 提取知识
knowledge = await client.extract_knowledge(
    agent_id="user-123",
    conversation_id="conv-001",
    conversation_text="User: 我在北京工作...",
)

# 搜索记忆
skills = await client.search(
    agent_id="user-123",
    tags=["skill"],
    min_importance=0.8,
)
```

---

## 📊 性能测试

### 基准测试脚本

```python
import asyncio
import time
from neuroflow.memory import KernelMemoryClient

async def benchmark():
    client = KernelMemoryClient()
    
    # 测试存储延迟
    start = time.time()
    for i in range(100):
        await client.store(
            agent_id="bench",
            key=f"test:{i}",
            value={"index": i},
        )
    elapsed = time.time() - start
    print(f"Store: {100/elapsed:.2f} ops/sec")
    
    # 测试检索延迟
    start = time.time()
    for i in range(100):
        await client.retrieve("bench", f"test:{i}")
    elapsed = time.time() - start
    print(f"Retrieve: {100/elapsed:.2f} ops/sec")

asyncio.run(benchmark())
```

**预期结果**:
- Store: 1000+ ops/sec
- Retrieve: 2000+ ops/sec

---

## 🎯 下一步

1. **启动服务器测试**
   ```bash
   cd kernel
   cargo run
   ```

2. **运行测试脚本**
   ```bash
   curl http://localhost:8080/api/memory/store ...
   ```

3. **Python SDK 测试**
   ```bash
   cd sdk
   python examples/agent_with_memory.py
   ```

---

**集成完成！🎉**

*Last updated: 2026-03-20*
