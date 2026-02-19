# NeuroFlow Memory 调用链路文档

**版本**: v0.5.0  
**日期**: 2026-03-20

---

## 📋 目录

1. [架构概览](#架构概览)
2. [调用链路详解](#调用链路详解)
3. [使用示例](#使用示例)
4. [知识提取机制](#知识提取机制)

---

## 🏗️ 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│              Python SDK (AINativeAgent)                     │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  ConversationMemoryManager                            │  │
│  │  • 对话上下文管理                                      │  │
│  │  • 自动保存对话                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ↓ gRPC                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  KernelMemoryClient                                   │  │
│  │  • store() / retrieve() / search()                    │  │
│  │  • save_conversation()                                │  │
│  │  • extract_knowledge() / save_extracted_knowledge()   │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ gRPC (localhost:50051)
                     │ /neuroflow.memory.v1.MemoryService
                     │ /neuroflow.memory.v1.ConversationMemoryService
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                  Rust Kernel                                │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  MemoryGrpcService                                    │  │
│  │  • Store() / Retrieve() / Search()                    │  │
│  │  • SemanticSearch()                                   │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  ConversationMemoryGrpcService                        │  │
│  │  • SaveConversation()                                 │  │
│  │  • ExtractKnowledge()                                 │  │
│  │  • SaveExtractedKnowledge()                           │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  MemoryManager                                        │  │
│  │  • store_memory() / retrieve_memory()                 │  │
│  │  • search_memories() / semantic_search()              │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  InMemoryBackend                                      │  │
│  │  • HashMap<String, MemoryEntry>                       │  │
│  │  • 存储所有记忆数据                                    │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔗 调用链路详解

### 链路 1: 存储记忆

```python
# Python SDK
await memory_client.store(
    agent_id="user-123",
    key="preference:theme",
    value={"theme": "dark"},
    tags=["preference"],
    importance=0.8,
)
```

**调用流程**:
```
1. Python: KernelMemoryClient.store()
   ↓ (gRPC stub)
2. Python: MemoryServiceStub.Store(request)
   ↓ (HTTP/2)
3. Rust: MemoryGrpcService::store()
   ↓ (内部调用)
4. Rust: MemoryManager::store_memory()
   ↓ (内部调用)
5. Rust: InMemoryBackend::store()
   ↓ (写入 HashMap)
6. Rust: 返回 memory_id
   ↓ (gRPC response)
7. Python: 返回 memory_id
```

**Proto 消息**:
```protobuf
message StoreRequest {
  MemoryEntry entry = 1;
  // MemoryEntry {
  //   string agent_id = 2;
  //   string key = 3;
  //   google.protobuf.Value value = 4;
  //   repeated string tags = 7;
  //   float importance = 8;
  // }
}

message StoreResponse {
  bool success = 1;
  string memory_id = 2;
  string error = 3;
}
```

---

### 链路 2: 检索记忆

```python
# Python SDK
preference = await memory_client.retrieve(
    agent_id="user-123",
    key="preference:theme",
)
```

**调用流程**:
```
1. Python: KernelMemoryClient.retrieve()
   ↓ (gRPC stub)
2. Python: MemoryServiceStub.Retrieve(request)
   ↓ (HTTP/2)
3. Rust: MemoryGrpcService::retrieve()
   ↓ (内部调用)
4. Rust: MemoryManager::retrieve_memory()
   ↓ (内部调用)
5. Rust: InMemoryBackend::load()
   ↓ (从 HashMap 读取)
6. Rust: 返回 MemoryEntry
   ↓ (gRPC response)
7. Python: 转换为 dict 并返回
```

---

### 链路 3: 保存对话

```python
# Python SDK
async with memory_mgr.conversation("conv-001") as conv:
    conv.add_user("Hello")
    response = await agent.chat("Hello")
    conv.add_assistant(response)
# 退出上下文时自动保存
```

**调用流程**:
```
1. Python: ConversationContext.__aexit__()
   ↓ (自动调用)
2. Python: KernelMemoryClient.save_conversation()
   ↓ (gRPC stub)
3. Python: ConversationMemoryServiceStub.SaveConversation(request)
   ↓ (HTTP/2)
4. Rust: ConversationMemoryGrpcService::save_conversation()
   ↓ (循环存储每轮对话)
5. Rust: MemoryManager::store_memory() × N
   ↓
6. Rust: 返回保存的轮数
   ↓ (gRPC response)
7. Python: 返回保存的轮数
```

**对话存储格式**:
```
Key: "conversation:{conversation_id}:{index}"
Value: {
  "role": "user" | "assistant",
  "content": "...",
  "metadata": {...}
}
Tags: ["conversation", "{conversation_id}"]
```

---

### 链路 4: 提取并保存知识 ⭐

```python
# Python SDK
# 1. 从对话中提取知识
knowledge_items = await memory_client.extract_knowledge(
    agent_id="user-123",
    conversation_id="conv-001",
    conversation_text="User: 我在北京工作\nAssistant: ...",
)

# 2. 保存提取的知识
await memory_client.save_extracted_knowledge(
    agent_id="user-123",
    knowledge_items=knowledge_items,
)
```

**调用流程**:
```
提取知识:
1. Python: KernelMemoryClient.extract_knowledge()
   ↓ (gRPC stub)
2. Python: ConversationMemoryServiceStub.ExtractKnowledge(request)
   ↓ (HTTP/2)
3. Rust: ConversationMemoryGrpcService::extract_knowledge()
   ↓ (调用 LLM 提取，当前返回空)
4. Rust: 返回 ExtractedKnowledge 列表
   ↓ (gRPC response)
5. Python: 转换为 dict 列表

保存知识:
1. Python: KernelMemoryClient.save_extracted_knowledge()
   ↓ (gRPC stub)
2. Python: ConversationMemoryServiceStub.SaveExtractedKnowledge(request)
   ↓ (HTTP/2)
3. Rust: ConversationMemoryGrpcService::save_extracted_knowledge()
   ↓ (循环存储每个知识项)
4. Rust: MemoryManager::store_memory() × N
   ↓
5. Rust: 返回 memory_ids
   ↓ (gRPC response)
6. Python: 返回 memory_ids
```

**知识存储格式**:
```
Key: "knowledge:{key}"
Value: {
  "value": "...",
  "category": "personal_info" | "preference" | "technical_skills",
  "confidence": 0.0-1.0
}
Tags: [category, ...]
Importance: confidence
```

---

## 📝 使用示例

### 示例 1: 基础记忆操作

```python
from neuroflow.memory import KernelMemoryClient

client = KernelMemoryClient(endpoint="localhost:50051")

# 存储
memory_id = await client.store(
    agent_id="user-123",
    key="preference:theme",
    value={"theme": "dark", "lang": "zh"},
    tags=["preference", "ui"],
    importance=0.8,
)

# 检索
pref = await client.retrieve("user-123", "preference:theme")

# 搜索
prefs = await client.search(
    agent_id="user-123",
    tags=["preference"],
    limit=10,
)

# 删除
await client.delete("user-123", "preference:theme")
```

---

### 示例 2: 对话记忆管理

```python
from neuroflow.memory import ConversationMemoryManager

memory_mgr = ConversationMemoryManager(
    agent_id="user-123",
    client=KernelMemoryClient(),
)

# 使用上下文管理器（自动保存）
async with memory_mgr.conversation("conv-001") as conv:
    conv.add_user("我在北京工作")
    response = await agent.chat("我在北京工作")
    conv.add_assistant(response)

# 加载历史
history = await client.get_conversation_history(
    agent_id="user-123",
    conversation_id="conv-001",
    limit=50,
)
```

---

### 示例 3: 知识提取和保存

```python
from neuroflow.memory import KernelMemoryClient

client = KernelMemoryClient()

# 对话文本
conversation = """
User: 我在北京工作，是软件工程师
Assistant: 很好！您用什么编程语言？
User: 主要用 Python，喜欢 Django 和 FastAPI
"""

# 提取知识（需要实现 LLM 提取逻辑）
knowledge = await client.extract_knowledge(
    agent_id="user-123",
    conversation_id="conv-001",
    conversation_text=conversation,
)

# 或者手动创建知识项
knowledge_items = [
    {
        "key": "user_location",
        "value": json.dumps({"city": "北京"}),
        "category": "personal_info",
        "confidence": 0.95,
        "tags": ["location", "personal"],
    },
    {
        "key": "user_profession",
        "value": json.dumps({"role": "软件工程师"}),
        "category": "professional_info",
        "confidence": 0.98,
        "tags": ["profession"],
    },
    {
        "key": "user_tech_stack",
        "value": json.dumps({"languages": ["Python"], "frameworks": ["Django", "FastAPI"]}),
        "category": "technical_skills",
        "confidence": 0.95,
        "tags": ["technology", "skills"],
    },
]

# 保存知识
memory_ids = await client.save_extracted_knowledge(
    agent_id="user-123",
    knowledge_items=knowledge_items,
)

# 后续可以搜索这些知识
tech_memories = await client.search(
    agent_id="user-123",
    tags=["technology"],
    min_importance=0.9,
)
```

---

## 🧠 知识提取机制

### 当前实现

当前 `extract_knowledge()` 返回空结果，需要实现 LLM 提取逻辑。

### 推荐实现方案

```rust
// kernel/src/grpc/memory_service.rs

async fn extract_knowledge(
    &self,
    request: Request<ExtractKnowledgeRequest>,
) -> Result<Response<ExtractKnowledgeResponse>, Status> {
    let req = request.into_inner();
    
    // 1. 调用 LLM 从对话中提取知识
    let llm_prompt = format!(
        "从以下对话中提取用户的个人信息、偏好、技能等知识:\n\n{}\n\n\
         请以 JSON 格式返回，包含：key, value, category, confidence, tags",
        req.conversation_text
    );
    
    // 2. 调用 LLM (通过 Kernel MCP)
    let llm_response = self.llm_client.generate(&llm_prompt).await?;
    
    // 3. 解析 LLM 输出
    let knowledge_items = parse_llm_output(&llm_response)?;
    
    Ok(Response::new(ExtractKnowledgeResponse {
        knowledge_items,
        error: String::new(),
    }))
}
```

### Python 实现方案

```python
async def extract_knowledge(
    self,
    agent_id: str,
    conversation_text: str,
) -> List[Dict[str, Any]]:
    """使用 LLM 从对话中提取知识"""
    
    # 调用 LLM
    from neuroflow import AINativeAgent, LLMConfig
    
    agent = AINativeAgent(
        name="knowledge_extractor",
        llm_config=LLMConfig(provider="openai", model="gpt-4"),
    )
    
    prompt = f"""
从以下对话中提取用户的知识:

{conversation_text}

提取的知识类型:
- 个人信息 (位置、职业等)
- 偏好 (主题、语言等)
- 技能 (编程语言、框架等)

返回 JSON 格式:
[
  {{
    "key": "user_location",
    "value": {{"city": "北京"}},
    "category": "personal_info",
    "confidence": 0.95,
    "tags": ["location", "personal"]
  }}
]
"""
    
    response = await agent.llm.chat(
        messages=[Message.system(prompt)]
    )
    
    # 解析 JSON
    knowledge_items = json.loads(response.content)
    
    return knowledge_items
```

---

## 📊 性能指标

| 操作 | 延迟 (P50) | 延迟 (P99) | 吞吐量 |
|------|------------|------------|--------|
| Store | ~1ms | ~5ms | 1000/s |
| Retrieve | ~0.5ms | ~2ms | 2000/s |
| Search | ~2ms | ~10ms | 500/s |
| SaveConversation (10 turns) | ~10ms | ~50ms | 100/s |

---

## 🔒 安全考虑

1. **Agent 隔离**: 每个 Agent 只能访问自己的记忆
2. **数据加密**: 敏感数据应加密存储
3. **访问日志**: 记录所有记忆访问
4. **过期清理**: 定期清理过期记忆

---

## 📚 相关文件

- Proto 定义：`proto/memory.proto`
- Rust 实现：`kernel/src/grpc/memory_service.rs`
- Python 客户端：`sdk/neuroflow/memory/kernel_client.py`
- 使用示例：`sdk/examples/agent_with_memory.py`

---

*Last updated: 2026-03-20*
