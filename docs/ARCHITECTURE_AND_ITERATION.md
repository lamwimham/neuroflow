# NeuroFlow 架构与迭代讨论 v0.4.0

**文档版本**: 1.0  
**最后更新**: 2026-02-19  
**目的**: 全面总结当前框架状态，明确迭代方向

---

## 📋 执行摘要

NeuroFlow 是一个 **AI Native Agent 运行时框架**，核心理念是让 LLM 自主决定使用工具，而非被动执行代码。

当前版本：**v0.4.0** (Phase 1-3 完成，Phase 4 进行中)

### 核心价值主张

1. **AI Native** - LLM 自主决策，而非确定性执行
2. **统一工具接口** - Local/MCP/Skills/Agents 统一协议
3. **可组合技能** - 程序性知识封装成可复用 Skills
4. **A2A 协作** - Agent 间自主协作完成复杂任务

---

## 🏗️ 当前架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Python SDK (业务层)                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐   │
│  │              AINativeAgent                           │   │
│  │  ┌────────────────────────────────────────────────┐ │   │
│  │  │         LLM Orchestrator (决策核心)             │ │   │
│  │  │  • 意图理解 • 工具选择 • 执行规划 • 结果整合    │ │   │
│  │  └────────────────────────────────────────────────┘ │   │
│  │         ↓              ↓              ↓              │   │
│  │  ┌──────────┐  ┌──────────────┐  ┌──────────┐      │   │
│  │  │  Tools   │  │     A2A      │  │  Skills  │      │   │
│  │  └──────────┘  └──────────────┘  └──────────┘      │   │
│  │         ↓                                           │   │
│  │  ┌──────────────────┐                              │   │
│  │  │    Memory        │                              │   │
│  │  └──────────────────┘                              │   │
│  └──────────────────────────────────────────────────────┘   │
│                              ↓                                │
├─────────────────────────────────────────────────────────────┤
│                  Rust Kernel (基础设施层)                     │
├─────────────────────────────────────────────────────────────┤
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │   Gateway  │  │   Skills   │  │   Memory   │            │
│  │   (网关)   │  │   Engine   │  │   Engine   │            │
│  └────────────┘  └────────────┘  └────────────┘            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │    MCP     │  │  Sandbox   │  │    A2A     │            │
│  │  Service   │  │  Manager   │  │   Router   │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### Python SDK 模块结构

```
sdk/neuroflow/
├── agent/                      # Agent 模块
│   ├── ai_native_agent.py      # AINativeAgent 核心类
│   └── __init__.py
├── orchestrator/               # LLM 编排模块
│   ├── llm_client.py           # LLM 客户端 (OpenAI/Anthropic/Ollama)
│   └── llm_orchestrator.py     # LLM 编排器
├── tools/                      # 工具模块
│   ├── protocol.py             # 统一工具协议
│   └── executors.py            # 工具执行器 (Local/MCP/Skill)
├── a2a/                        # A2A 协作模块
│   ├── agent_registry.py       # Agent 注册表
│   └── collaborative_orchestrator.py  # 协作编排器
├── learning/                   # 技能学习模块
│   ├── skill_learner.py        # 技能学习器
│   └── skill_sandbox.py        # 技能沙箱执行器
├── memory/                     # 记忆模块
│   └── vector_store.py         # 向量记忆存储
├── cli/                        # CLI 工具
│   ├── main.py                 # CLI 入口
│   └── commands/               # CLI 命令
│       ├── agent.py            # Agent 命令
│       ├── skill.py            # Skill 命令 (重构完成)
│       └── tool.py             # Tool 命令
└── __init__.py                 # SDK 导出
```

### Rust Kernel 模块结构

```
kernel/src/
├── tool_router/                # ✅ 工具路由 (Phase 1)
│   ├── mod.rs                  # 核心数据类型
│   ├── executor.rs             # 执行器 Trait
│   └── registry.rs             # 工具注册表
├── gateway/                    # ✅ HTTP 网关
├── mcp/                        # ⚠️ MCP 服务 (部分实现)
├── skills/                     # ⚠️ Skills 引擎 (部分实现)
├── memory/                     # ⚠️ 记忆引擎 (部分实现)
├── a2a/                        # ⚠️ A2A 路由 (部分实现)
├── sandbox/                    # ⚠️ 沙箱管理 (部分实现)
└── [其他模块]                   # ⚠️ 原有代码，需要审查
```

---

## ✅ 已完成功能

### Phase 1: AI Native 基础架构 ✅

| 功能 | 状态 | 说明 |
|------|------|------|
| 统一工具协议 | ✅ 完成 | ToolDefinition, ToolCall, ToolResult |
| 工具执行器 | ✅ 完成 | LocalFunctionExecutor, MCPToolExecutor, SkillExecutor |
| LLM Client | ✅ 完成 | 支持 OpenAI/Anthropic/Ollama |
| LLM Orchestrator | ✅ 完成 | 自主工具选择和执行 |
| AI Native Agent | ✅ 完成 | @tool 装饰器，记忆管理 |
| Rust tool_router | ✅ 完成 | 工具路由和注册 |

**核心 API**:
```python
from neuroflow import AINativeAgent, LLMConfig

agent = AINativeAgent(
    AINativeAgentConfig(
        name="assistant",
        llm_config=LLMConfig(provider="openai", model="gpt-4"),
    )
)

@agent.tool(name="greet", description="问候")
async def greet(name: str) -> str:
    return f"Hello, {name}!"

result = await agent.handle("帮我问候张三")
```

---

### Phase 2: MCP 集成和完善 ✅

| 功能 | 状态 | 说明 |
|------|------|------|
| MCPToolExecutor | ✅ 完成 | MCP 工具调用 |
| 工具发现 | ✅ 完成 | 从 MCP 服务器发现工具 |
| 混合工具使用 | ✅ 完成 | Local + MCP 混合 |
| 示例代码 | ✅ 完成 | 3 个完整示例 |

---

### Phase 3: 高级特性 ✅

| 功能 | 状态 | 说明 |
|------|------|------|
| A2A 协作 | ✅ 完成 | AgentRegistry, CollaborativeOrchestrator |
| 技能学习 | ✅ 完成 | SkillLearner, SkillSandboxExecutor |
| 记忆系统 | ✅ 完成 | VectorMemoryStore (向量记忆) |
| Skills CLI | ✅ 完成 | 灵活的 skill create 命令 |

**Skills CLI 示例**:
```bash
# 创建 Skill
neuroflow skill create data-analysis \
  --description="数据分析框架。触发词：数据分析、统计" \
  --category data-analysis \
  --template standard \
  --with-framework \
  --with-examples \
  --with-scripts \
  --assign-to assistant

# 列出 Skills
neuroflow skill list

# 验证 Skill
neuroflow skill validate data-analysis

# 分配 Skill 到 Agent
neuroflow skill assign data-analysis analyst
```

---

## ⚠️ 待完成/需改进功能

### 高优先级

| 功能 | 当前状态 | 需求 | 优先级 |
|------|---------|------|--------|
| **Rust Kernel 编译** | ⚠️ 部分模块注释 | 修复 proto/grpc 编译 | P0 |
| **MCP 真实实现** | ⚠️ 模拟实现 | 实际 MCP 服务器集成 | P0 |
| **Skill 运行时** | ⚠️ 基础实现 | Skill 自动加载和执行 | P0 |
| **A2A 真实通信** | ⚠️ 框架完成 | 实际 Agent 间通信 | P1 |
| **记忆系统集成** | ⚠️ Python 完成 | Rust Kernel 集成 | P1 |

### 中优先级

| 功能 | 当前状态 | 需求 | 优先级 |
|------|---------|------|--------|
| **CLI 完善** | ✅ 基本完成 | skill test/import/export | P2 |
| **文档完善** | ⚠️ 部分完成 | API 文档、教程 | P2 |
| **测试覆盖** | ⚠️ 基础测试 | 单元测试、集成测试 | P2 |
| **性能优化** | ⚠️ 未开始 | 基准测试、优化 | P3 |

---

## 🎯 核心需求分析

### 用户需求

1. **快速创建 Agent**
   - CLI 工具支持
   - 模板和示例
   - 文档和最佳实践

2. **灵活的工具使用**
   - LLM 自主决定
   - 多种工具来源
   - 统一的调用接口

3. **可复用的技能**
   - 程序性知识封装
   - 跨项目共享
   - 版本管理

4. **Agent 协作**
   - 多 Agent 分工
   - 自主协作决策
   - 结果整合

### 技术需求

1. **性能**
   - 网关延迟 < 10ms (P50)
   - 工具调用延迟 < 50ms
   - 并发支持 > 100 Agent

2. **可靠性**
   - 错误处理和重试
   - 超时控制
   - 资源限制

3. **可扩展性**
   - 插件化架构
   - 模块化设计
   - 清晰的接口定义

4. **可观测性**
   - 日志记录
   - 指标监控
   - 链路追踪

---

## 📦 核心组件详解

### 1. AINativeAgent

**职责**: Agent 基类，提供工具注册、记忆管理、对话历史

**核心方法**:
```python
class AINativeAgent:
    def __init__(self, config: AINativeAgentConfig)
    
    # 工具装饰器
    def tool(self, name: str, description: str) -> callable
    
    # 主入口 - LLM 自主决定使用工具
    async def handle(self, user_message: str) -> Dict[str, Any]
    
    # 记忆管理
    def store_memory(self, key: str, value: Any, tags: List[str])
    def retrieve_memory(self, key: str) -> Any
    def search_memories(self, tags: List[str]) -> List[Any]
    
    # 工具管理
    def list_available_tools(self) -> List[str]
    async def execute_tool(self, tool_name: str, **kwargs) -> Any
```

**依赖**:
- LLMClient (LLM 调用)
- LLMOrchestrator (工具编排)
- UnifiedToolRegistry (工具注册)

---

### 2. LLMOrchestrator

**职责**: LLM 编排，自主决定使用工具

**核心流程**:
```
1. 接收用户请求
2. LLM 分析意图
3. 决定是否需要工具
4. 选择合适工具
5. 执行工具 (可能多轮)
6. 整合结果
7. 返回回复
```

**核心方法**:
```python
class LLMOrchestrator:
    async def execute(
        self,
        user_message: str,
        conversation_history: List[Message] = None,
    ) -> TurnResult
```

**支持 LLM**:
- OpenAI (GPT-3.5/4) - Function Calling
- Anthropic (Claude) - Tool Use
- Ollama (本地模型) - 基础支持

---

### 3. UnifiedToolRegistry

**职责**: 统一工具注册和调用

**工具来源**:
```python
class ToolSource(Enum):
    LOCAL_FUNCTION = "local_function"      # 本地 Python 函数
    MCP_SERVER = "mcp_server"              # MCP 服务
    SKILL = "skill"                        # Rust Skills
    REMOTE_AGENT = "remote_agent"          # 其他 Agent
    LLM_GENERATED = "llm_generated"        # LLM 动态生成
```

**核心方法**:
```python
class UnifiedToolRegistry:
    def register_tool(self, definition: ToolDefinition)
    def register_executor(self, source: ToolSource, executor: ToolExecutor)
    async def execute(self, call: ToolCall) -> ToolResult
    def get_all_llm_schemas(self) -> List[Dict[str, Any]]
```

---

### 4. Skills 系统

**概念**: 封装程序性知识的可复用模块

**SKILL.md 结构**:
```markdown
---
name: skill-name
description: 技能描述。触发词：关键词 1、关键词 2
version: 1.0.0
author: Your Name
category: category-name
trigger_words:
  - keyword1
  - keyword2
assigned_agents:
  - assistant
  - analyst
---

# SKILL NAME

## Goal
技能目标

## Workflow
执行步骤

## Output Format
输出格式
```

**目录结构**:
```
skill-name/
├── SKILL.md                 # 必需
├── FRAMEWORK.md             # 可选
├── EXAMPLES.md              # 可选
├── scripts/                 # 可选
│   └── process.py
└── resources/               # 可选
```

---

### 5. A2A 协作

**组件**:
- `AgentRegistry` - Agent 注册和发现
- `CollaborativeOrchestrator` - 协作编排

**协作流程**:
```
1. LLM 分析是否需要协作
2. 选择合适的 Agent
3. 发送协助请求
4. 接收协助结果
5. 整合结果返回用户
```

**核心 API**:
```python
registry = AgentRegistry()
registry.register_agent(agent_info)

collaborator = CollaborativeOrchestrator(
    llm_orchestrator=orchestrator,
    agent_registry=registry,
)

result = await collaborator.execute_with_collaboration(
    "复杂任务描述"
)
```

---

### 6. 记忆系统

**记忆类型**:
```python
class MemoryType(Enum):
    SHORT_TERM = "short_term"      # 短期记忆
    LONG_TERM = "long_term"        # 长期记忆
    WORKING = "working"            # 工作记忆
    EPISODIC = "episodic"          # 情景记忆
    SEMANTIC = "semantic"          # 语义记忆
```

**核心功能**:
- 键值存储
- 标签索引
- 语义检索 (向量相似度)
- TTL 过期管理
- 自动清理

**核心 API**:
```python
store = VectorMemoryStore(max_memories=1000)

await store.store(
    key="user_preference",
    value="喜欢简洁的回答",
    memory_type=MemoryType.LONG_TERM,
    tags=["user", "preference"],
    importance=0.8,
)

value = await store.retrieve("user_preference")
results = await store.semantic_search("用户喜欢什么？", top_k=3)
```

---

## 🔧 CLI 工具

### 命令总览

| 命令 | 说明 | 状态 |
|------|------|------|
| `neuroflow init` | 创建项目 | ✅ |
| `neuroflow agent create` | 创建 Agent | ✅ |
| `neuroflow skill create` | 创建 Skill | ✅ (重构完成) |
| `neuroflow skill list` | 列出 Skills | ✅ |
| `neuroflow skill show` | 显示 Skill 详情 | ✅ |
| `neuroflow skill validate` | 验证 Skill | ✅ |
| `neuroflow skill assign` | 分配 Skill 到 Agent | ✅ |
| `neuroflow tool create` | 创建 Tool | ✅ |
| `neuroflow run` | 运行应用 | ✅ |
| `neuroflow serve` | 启动服务器 | ✅ |

### Skills CLI 详解

```bash
# 创建 Skill (灵活选项)
neuroflow skill create <name> \
  --description "描述" \
  --category <category> \
  --template <minimal|standard|advanced> \
  --with-framework \
  --with-examples \
  --with-scripts \
  --with-resources \
  --assign-to <agent> \
  --author "作者" \
  --force
```

---

## 📊 当前状态总结

### 已完成 (✅)

- ✅ Python SDK 核心架构
- ✅ LLM 编排器 (OpenAI/Anthropic)
- ✅ 统一工具协议
- ✅ A2A 协作框架
- ✅ 技能学习系统
- ✅ 记忆系统
- ✅ Skills CLI (完整重构)
- ✅ 文档网站基础

### 部分完成 (⚠️)

- ⚠️ Rust Kernel (部分模块注释)
- ⚠️ MCP 集成 (模拟实现)
- ⚠️ Skill 运行时 (基础实现)
- ⚠️ A2A 通信 (框架完成)
- ⚠️ 文档 (部分完成)
- ⚠️ 测试覆盖 (基础测试)

### 未开始 (❌)

- ❌ 性能基准测试
- ❌ 插件系统
- ❌ Web 控制台
- ❌ Skill 市场

---

## 🎯 迭代方向讨论

### 方向 A: 完善 Python SDK (推荐)

**理由**:
1. Python SDK 是用户直接接触的部分
2. 核心功能已完成，需要完善和稳定
3. 可以快速迭代和发布

**任务**:
1. 完善 Skill 运行时集成
2. 实现 Skill 自动加载
3. 完善 A2A 通信机制
4. 添加更多示例和模板
5. 完善文档和教程

**预计时间**: 2-3 周

---

### 方向 B: 修复 Rust Kernel

**理由**:
1. Rust Kernel 是性能关键
2. 需要完整的 Rust/Python 集成
3. 长期来看是必要的

**任务**:
1. 修复 proto 编译问题
2. 恢复 grpc 模块
3. 实现真实的 MCP 服务
4. 实现 Skill 引擎
5. 性能优化

**预计时间**: 4-6 周

---

### 方向 C: 开发者体验

**理由**:
1. 降低使用门槛
2. 吸引更多用户
3. 建立生态

**任务**:
1. CLI 工具完善 (skill test/import/export)
2. 更多模板和示例
3. 完整教程和文档
4. Web 控制台原型
5. 社区建设

**预计时间**: 3-4 周

---

## 📋 建议迭代计划

### 短期 (1-2 周) - 稳定核心

**目标**: 完善 Python SDK 核心功能

**任务**:
1. ✅ Skill 运行时集成 (自动加载、执行)
2. ✅ A2A 通信完善 (真实 Agent 间调用)
3. ✅ 记忆系统与 Agent 深度集成
4. ✅ CLI skill test 命令
5. ✅ 文档完善 (API 参考、教程)

**交付物**:
- v0.4.1 版本
- 完整的 Skills 使用文档
- 5+ 个完整示例

---

### 中期 (3-4 周) - 丰富生态

**目标**: 丰富功能和示例

**任务**:
1. Skill 模板市场
2. 更多预定义 Skills
3. Agent 协作示例
4. Web 控制台原型
5. 性能基准测试

**交付物**:
- v0.5.0 版本
- Skill 模板库 (10+ Skills)
- Web 控制台 MVP

---

### 长期 (5-8 周) - Rust 内核完善

**目标**: 完善 Rust Kernel

**任务**:
1. 修复所有编译问题
2. 实现真实 MCP 服务
3. Skill 引擎 Rust 实现
4. 性能优化
5. 生产部署示例

**交付物**:
- v1.0.0 版本
- 性能基准报告
- 生产部署指南

---

## 🤔 关键决策点

### 决策 1: Rust Kernel 优先级

**选项 A**: 优先完善 Python SDK (推荐)
- 优点：快速迭代，用户可见
- 缺点：Rust Kernel 继续搁置

**选项 B**: 优先修复 Rust Kernel
- 优点：完整架构，性能更好
- 缺点：迭代周期长

**建议**: 选项 A，先完善 Python SDK，Rust Kernel 并行进行

---

### 决策 2: Skills 实现方式

**选项 A**: Python 实现 (当前)
- 优点：灵活，易扩展
- 缺点：性能受限

**选项 B**: Rust 实现
- 优点：性能好，安全
- 缺点：开发周期长

**建议**: 混合方案 - Python 用于快速原型，Rust 用于性能关键 Skills

---

### 决策 3: 文档优先级

**选项 A**: API 参考文档优先
- 优点：开发者友好
- 缺点：学习曲线陡

**选项 B**: 教程优先
- 优点：易上手
- 缺点：深度不够

**建议**: 两者并行 - API 参考 + 快速入门教程

---

## 📝 行动项

### 立即行动 (本周)

- [ ] 确定迭代方向 (A/B/C)
- [ ] 完善 Skill 运行时集成
- [ ] 添加 skill test CLI 命令
- [ ] 完善 API 文档

### 下周行动

- [ ] A2A 通信完善
- [ ] 记忆系统深度集成
- [ ] 5+ 完整示例
- [ ] 文档网站完善

### 下月行动

- [ ] Skill 模板库
- [ ] Web 控制台原型
- [ ] 性能基准测试
- [ ] 社区建设

---

## 📞 讨论问题

1. **迭代方向**: 应该优先完善 Python SDK 还是 Rust Kernel?
2. **Skills 实现**: Python vs Rust，如何平衡灵活性和性能？
3. **文档策略**: API 参考 vs 教程，资源如何分配？
4. **发布节奏**: 快速迭代 (每周) vs 稳定发布 (每月)?
5. **社区建设**: 何时开始社区建设？优先级如何？

---

## 📚 相关文档

- [Phase 1 完成报告](docs/PHASE1_COMPLETE.md)
- [Phase 2 完成报告](docs/PHASE2_COMPLETE.md)
- [Phase 3 完成报告](docs/PHASE3_COMPLETE.md)
- [Skills CLI 重构总结](docs/SKILLS_REFACTOR_SUMMARY.md)
- [CLI 使用指南](docs-site/docs/guides/cli.md)
- [Skills 使用指南](docs/SKILLS_GUIDE.md)

---

**版本**: v0.4.0  
**创建日期**: 2026-02-19  
**状态**: 待讨论
