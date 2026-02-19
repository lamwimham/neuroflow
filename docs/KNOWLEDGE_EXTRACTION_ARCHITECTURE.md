# NeuroFlow Knowledge Extraction 架构文档

**版本**: v0.5.0  
**日期**: 2026-03-20  
**状态**: ✅ 架构设计完成

---

## 📋 目录

1. [架构设计](#架构设计)
2. [模块职责](#模块职责)
3. [调用链路](#调用链路)
4. [使用示例](#使用示例)

---

## 🏗️ 架构设计

### 核心设计原则

1. **单一职责** - 每个模块做好一件事
2. **依赖倒置** - 高层模块不依赖低层模块
3. **接口隔离** - 使用 trait 解耦
4. **无循环依赖** - 依赖关系单向

### 架构图

```
┌─────────────────────────────────────────────────────────┐
│              Knowledge Extraction Layer                 │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │  KnowledgeExtractor                               │  │
│  │  • extract_from_conversation()                    │  │
│  │  • extract_from_document()                        │  │
│  │  • call_llm() → MCP Service                       │  │
│  └───────────────────────────────────────────────────┘  │
│                          ↓ depends on                   │
│  ┌───────────────────────────────────────────────────┐  │
│  │  ConversationAnalyzer                             │  │
│  │  • analyze_and_extract()                          │  │
│  │  • auto_extract (configurable)                    │  │
│  └───────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ uses
                     ↓
┌─────────────────────────────────────────────────────────┐
│                  Memory Layer                           │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │  MemoryManager                                    │  │
│  │  • store_memory()                                 │  │
│  │  • retrieve_memory()                              │  │
│  │  • search_memories()                              │  │
│  └───────────────────────────────────────────────────┘  │
│                          ↓ uses                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │  MemoryBackend (trait)                            │  │
│  │  • InMemoryBackend (implementation)               │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                     ↑
                     │ uses
┌────────────────────┴─────────────────────────────────────┐
│                  MCP Layer (LLM)                         │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │  MCPService                                       │  │
│  │  • execute() → LLM providers                      │  │
│  │  • route to GPT-4/Claude/etc.                     │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 依赖关系

```
knowledge → memory (存储提取的知识)
knowledge → mcp (调用 LLM 提取)
memory → 无外部依赖 (纯存储)
mcp → 外部 LLM API

✅ 无循环依赖
✅ 职责清晰
✅ 易于测试
```

---

## 📦 模块职责

### KnowledgeExtractor

**职责**: 从文本中提取知识并存储

**核心方法**:
```rust
pub struct KnowledgeExtractor {
    memory_manager: Arc<MemoryManager>,  // 用于存储
    mcp_service: Arc<MCPService>,        // 用于调用 LLM
}

impl KnowledgeExtractor {
    // 从对话中提取
    pub async fn extract_from_conversation(
        &self,
        agent_id: &str,
        conversation_id: &str,
        conversation_text: &str,
    ) -> Result<Vec<MemoryEntry>>
    
    // 从文档中提取
    pub async fn extract_from_document(
        &self,
        agent_id: &str,
        document_text: &str,
        document_type: &str,
    ) -> Result<Vec<MemoryEntry>>
}
```

**工作流程**:
1. 构建提取 prompt
2. 调用 LLM (通过 MCP)
3. 解析 LLM 输出 (JSON)
4. 转换为 MemoryEntry
5. 存储到 Memory

---

### ConversationAnalyzer

**职责**: 自动分析对话并触发知识提取

**核心方法**:
```rust
pub struct ConversationAnalyzer {
    extractor: Arc<KnowledgeExtractor>,
    auto_extract: bool,
    min_turns: usize,
}

impl ConversationAnalyzer {
    pub async fn analyze_and_extract(
        &self,
        agent_id: &str,
        conversation_id: &str,
        turns: &[ConversationTurn],
    ) -> Result<usize>
}
```

**配置选项**:
- `auto_extract`: 是否自动提取
- `min_turns`: 最小对话轮数触发提取

---

### MemoryManager

**职责**: 纯粹的存储管理，不关心内容来源

**核心方法**:
```rust
pub struct MemoryManager {
    backend: Arc<dyn MemoryBackend>,
}

impl MemoryManager {
    pub async fn store_memory(&self, entry: MemoryEntry) -> Result<()>
    pub async fn retrieve_memory(&self, agent_id: &str, key: &str) -> Result<Option<MemoryEntry>>
    pub async fn search_memories(&self, query: MemoryQuery) -> Result<Vec<MemoryEntry>>
}
```

---

## 🔗 调用链路

### 完整调用链路

```
Python Agent (via gRPC)
    ↓
ConversationMemoryGrpcService::extract_knowledge()
    ↓
KnowledgeExtractor::extract_from_conversation()
    ├─→ 1. build_extraction_prompt()
    ├─→ 2. call_llm()
    │       ↓
    │   MCPService::execute()
    │       ↓
    │   LLM Provider (GPT-4/Claude)
    │       ↓
    │   JSON response
    │
    ├─→ 3. parse_llm_response()
    └─→ 4. For each knowledge item:
            ↓
        MemoryManager::store_memory()
            ↓
        InMemoryBackend::store()
            ↓
        HashMap<String, MemoryEntry>
```

### 代码示例

```rust
// 1. gRPC 服务接收请求
async fn extract_knowledge(
    &self,
    request: Request<ExtractKnowledgeRequest>,
) -> Result<Response<ExtractKnowledgeResponse>, Status> {
    let req = request.into_inner();
    
    // 2. 调用 KnowledgeExtractor
    let memories = self.knowledge_extractor
        .extract_from_conversation(
            &req.agent_id,
            &req.conversation_id,
            &req.conversation_text,
        )
        .await?;
    
    // 3. 返回结果
    Ok(Response::new(ExtractKnowledgeResponse {
        knowledge_items: memories.iter().map(...).collect(),
        error: String::new(),
    }))
}
```

---

## 📝 使用示例

### 示例 1: Python SDK 调用

```python
from neuroflow import AINativeAgent
from neuroflow.memory import KernelMemoryClient

# 创建 Agent 和 Memory 客户端
agent = AINativeAgent(name="assistant")
memory = KernelMemoryClient(endpoint="localhost:50051")

# 对话
conversation_text = """
User: 我在北京工作，是软件工程师
Assistant: 很好！您用什么编程语言？
User: 主要用 Python，喜欢 Django 和 FastAPI
"""

# 提取知识
knowledge = await memory.extract_knowledge(
    agent_id="user-123",
    conversation_id="conv-001",
    conversation_text=conversation_text,
)

print(f"提取了 {len(knowledge)} 条知识:")
for item in knowledge:
    print(f"  - {item['key']}: {item['value']}")

# 知识已自动保存到 Memory
# 可以搜索这些知识
tech_memories = await memory.search(
    agent_id="user-123",
    tags=["skill"],
    min_importance=0.8,
)
```

### 示例 2: 自动对话分析

```python
from neuroflow.memory import ConversationMemoryManager

memory_mgr = ConversationMemoryManager(
    agent_id="user-123",
    client=KernelMemoryClient(),
)

# 使用上下文管理器
async with memory_mgr.conversation("conv-002") as conv:
    # 对话 1
    conv.add_user("我在上海工作")
    response1 = await agent.chat("我在上海工作")
    conv.add_assistant(response1)
    
    # 对话 2
    conv.add_user("我喜欢用 Python 编程")
    response2 = await agent.chat("我喜欢用 Python 编程")
    conv.add_assistant(response2)
    
    # 对话 3
    conv.add_user("平时喜欢打篮球")
    response3 = await agent.chat("平时喜欢打篮球")
    conv.add_assistant(response3)

# 退出上下文时:
# 1. 自动保存对话
# 2. 自动提取知识（如果达到最小轮数）
# 3. 知识存储到 Memory
```

### 示例 3: Rust 内部调用

```rust
use crate::knowledge::{KnowledgeExtractor, ConversationAnalyzer};
use crate::memory::MemoryManager;
use crate::mcp::MCPService;

// 初始化
let memory_manager = Arc::new(MemoryManager::new(...));
let mcp_service = Arc::new(MCPService::new(...));

// 创建提取器
let extractor = Arc::new(KnowledgeExtractor::new(
    memory_manager.clone(),
    mcp_service.clone(),
));

// 创建分析器
let analyzer = Arc::new(ConversationAnalyzer::new(extractor.clone()));

// 从对话中提取
let turns = vec![
    ConversationTurn {
        role: "user".to_string(),
        content: "我在北京工作".to_string(),
        timestamp: Some(Utc::now()),
        metadata: None,
    },
    // ... more turns
];

let count = analyzer.analyze_and_extract(
    "user-123",
    "conv-001",
    &turns,
).await?;

println!("Extracted {} knowledge items", count);
```

---

## 🧠 知识提取 Prompt

### 对话提取 Prompt

```
从以下对话中提取用户的知识。

对话内容:
{conversation_text}

请提取以下类型的知识:
1. 个人信息（位置、职业、公司、教育背景等）
2. 偏好（主题、语言、工具、框架等）
3. 技能（编程语言、框架、工具、技术等）
4. 兴趣（爱好、活动、关注领域等）
5. 事实知识（用户提到的客观事实）

请以 JSON 数组格式返回，每个知识项包含:
{
  "key": "简短的键名（英文，下划线分隔）",
  "value": { "具体数据对象，结构化" },
  "category": "personal_info|preference|skill|interest|fact",
  "confidence": 0.0-1.0（置信度）,
  "tags": ["标签 1", "标签 2"]
}

注意事项:
- 只提取明确的信息，不要推测
- confidence 表示你对提取内容的确信程度
- value 应该是结构化的 JSON 对象
- key 应该简洁且有描述性

只返回 JSON 数组，不要其他内容。
```

### 输出示例

```json
[
  {
    "key": "user_location",
    "value": {"city": "北京", "country": "中国"},
    "category": "personal_info",
    "confidence": 0.95,
    "tags": ["location", "personal"]
  },
  {
    "key": "programming_languages",
    "value": {"languages": ["Python", "Rust"], "proficiency": "advanced"},
    "category": "skill",
    "confidence": 0.9,
    "tags": ["programming", "skills"]
  },
  {
    "key": "preferred_frameworks",
    "value": {"frameworks": ["Django", "FastAPI", "Axum"]},
    "category": "preference",
    "confidence": 0.85,
    "tags": ["frameworks", "preferences"]
  }
]
```

---

## 📊 性能指标

| 操作 | 延迟 (P50) | 延迟 (P99) | 说明 |
|------|------------|------------|------|
| extract_knowledge (10 turns) | ~2s | ~5s | 包含 LLM 调用 |
| save_extracted_knowledge (5 items) | ~10ms | ~50ms | 纯存储 |
| search_knowledge | ~2ms | ~10ms | 内存搜索 |

---

## 🔒 安全考虑

1. **Prompt 注入防护**
   - 过滤用户输入中的特殊字符
   - 限制 prompt 长度
   - 验证 LLM 输出格式

2. **数据隐私**
   - 敏感信息加密存储
   - 访问日志记录
   - 支持数据删除

3. **置信度阈值**
   - 低置信度知识需要人工审核
   - 可配置最小置信度

---

## 📚 相关文件

- Rust 实现：`kernel/src/knowledge/mod.rs`
- gRPC 服务：`kernel/src/grpc/memory_service.rs`
- Proto 定义：`proto/memory.proto`
- Python 客户端：`sdk/neuroflow/memory/kernel_client.py`
- 使用示例：`sdk/examples/agent_with_memory.py`

---

*Last updated: 2026-03-20*
