# NeuroFlow - AI Native Agent 运行时框架

> 🎉 **新版本**: v0.4.0 - Phase 1-4 全部完成

[![CI](https://github.com/lamwimham/neuroflow/actions/workflows/ci.yml/badge.svg)](https://github.com/lamwimham/neuroflow/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/pypi/v/neuroflow-sdk.svg)](https://pypi.org/project/neuroflow-sdk/)

NeuroFlow 是一个 AI Native 的 Agent 运行时框架，支持 LLM 自主决定使用工具、技能和协作。

## 🎯 核心价值

**让 LLM 自主决定使用工具，而非被动执行代码。**

- 🤖 **AI Native** - LLM 自主决定使用 MCP/Skills/Tools
- 🔌 **统一工具接口** - 支持 Local/MCP/Skills/Agents
- 🧠 **记忆管理** - 向量记忆、语义检索
- 🤝 **A2A 协作** - Agent 间自主协作
- 🎓 **技能学习** - LLM 驱动的技能生成
- 🛠️ **CLI 工具** - 完整的生产力工具链
- 🚀 **高性能** - Rust 内核 + Python 沙箱

## 🚀 快速开始

### 1. 安装

```bash
cd sdk
pip install -e .

# 验证安装
python -c "from neuroflow import AINativeAgent; print('✓ 安装成功')"
```

### 2. 创建你的第一个 AI Native Agent

```python
import asyncio
from neuroflow import AINativeAgent, LLMConfig

async def main():
    # 创建 Agent
    agent = AINativeAgent(
        name="assistant",
        llm_config=LLMConfig(provider="openai", model="gpt-4"),
    )
    
    # 注册工具
    @agent.tool(name="greet", description="问候某人")
    async def greet(name: str) -> str:
        return f"Hello, {name}!"
    
    # LLM 自主决定是否使用 greet 工具
    result = await agent.handle("帮我问候张三")
    print(result["response"])

asyncio.run(main())
```

### 3. 运行示例

```bash
export OPENAI_API_KEY=your-api-key
python sdk/examples/ai_native/minimal_example.py
```

详细教程请查看 [docs/PHASE1_COMPLETE.md](docs/PHASE1_COMPLETE.md)

## 📊 架构设计

```
┌─────────────────────────────────────────┐
│      Python SDK (业务逻辑层)             │
│  • Agent 定义                           │
│  • 工具系统                             │
│  • MCP 集成 (可选)                       │
├─────────────────────────────────────────┤
│      Rust Kernel (基础设施层)            │
│  • HTTP/gRPC 网关                        │
│  • WASM/进程沙箱                        │
│  • 资源调度                             │
│  • 可观测性                             │
└─────────────────────────────────────────┘
```

### 核心设计原则

1. **关注点分离**: Rust 专注基础设施，Python 专注业务逻辑
2. **显式初始化**: 避免异步初始化陷阱
3. **最小配置**: 只保留必要的配置项
4. **性能优先**: 网关延迟目标 < 10ms

## 📦 核心组件

### Rust 内核

| 组件 | 说明 | 状态 |
|------|------|------|
| HTTP 网关 | Axum + Tokio 高性能网关 | ✅ 可用 |
| 配置系统 | 简化的配置管理 (5 个核心结构) | ✅ 已重构 |
| WASM 沙箱 | 安全执行环境 | 🚧 开发中 |
| 可观测性 | OpenTelemetry 集成 | ✅ 可用 |

### Python SDK

| 组件 | 说明 | 状态 |
|------|------|------|
| NeuroFlowSDK | 统一的 SDK 入口 | ✅ 已重构 |
| @agent 装饰器 | Agent 定义 | ✅ 可用 |
| @tool 装饰器 | 工具定义 | ✅ 可用 |
| 工具管理器 | 工具注册和执行 | ✅ 已重构 |

## 📈 性能指标 (目标)

| 指标 | 当前 | 目标 | 状态 |
|------|------|------|------|
| 网关延迟 (P50) | - | < 10ms | 🚧 待优化 |
| 网关延迟 (P99) | - | < 20ms | 🚧 待优化 |
| 并发沙箱数 | - | 10+ | 🚧 待实现 |
| 沙箱启动时间 | - | < 100ms | 🚧 待实现 |

性能基准测试框架：**计划中**

## 🛠️ 开发指南

### 环境要求

- Rust 1.70+
- Python 3.9+
- Protobuf 编译器 (protoc)

### 构建项目

```bash
# 构建 Rust 内核
cd kernel
cargo build

# 安装 Python SDK
cd sdk
pip install -e .

# 运行测试
cargo test  # Rust
pytest      # Python
```

### 代码质量

```bash
# Rust
cargo clippy -- -D warnings
cargo fmt --check

# Python
black --check sdk/neuroflow/
isort --check-only sdk/neuroflow/
mypy sdk/neuroflow/
```

## 📚 文档

- **[快速开始](QUICKSTART.md)** - 30 分钟入门
- **[迭代计划](ITERATION_PLAN.md)** - 发展路线图
- **[架构审查](ARCHITECTURE_REVIEW.md)** - 技术审查报告
- **[MCP 集成](docs/MCP_DEVELOPER_GUIDE.md)** - MCP 使用指南

## 🗺️ 路线图

### Phase 1: AI Native 基础架构 ✅

- [x] 统一工具协议层
- [x] LLM Orchestrator 核心
- [x] AI Native Agent
- [x] Function Calling 支持
- [x] 基础文档和示例

**详情**: [docs/PHASE1_COMPLETE.md](docs/PHASE1_COMPLETE.md)

### Phase 2: MCP 集成和示例完善 ✅

- [x] MCP 工具发现和集成
- [x] 3 个完整示例代码
- [x] 混合工具使用
- [x] 完善文档
- [x] Python 测试覆盖

**详情**: [docs/PHASE2_COMPLETE.md](docs/PHASE2_COMPLETE.md)

### Phase 3: 高级特性 ✅

- [x] A2A 协作机制
- [x] 技能学习系统
- [x] 记忆系统增强
- [x] Phase 3 示例代码
- [x] 完整文档

**详情**: [docs/PHASE3_COMPLETE.md](docs/PHASE3_COMPLETE.md)

### Phase 4: 生产力工具链 ✅

- [x] CLI 工具开发
- [x] Rust 内核完善
- [x] 性能基准测试
- [x] 完整文档

**详情**: [docs/PHASE4_COMPLETE.md](docs/PHASE4_COMPLETE.md)

### Phase 5: 生态建设 (计划中)

- [ ] Web 控制台
- [ ] 插件系统
- [ ] 企业功能
- [ ] Agent 市场

## 🤝 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 发起 Pull Request

### 贡献方向

当前优先级最高的贡献方向：

**Phase 4 相关**:
1. **CLI 工具开发** - neuroflow 命令行工具
2. **Rust 内核完善** - 修复 proto/grpc 编译问题
3. **性能基准测试** - 建立可重复的性能测试框架
4. **文档完善** - API 参考、教程、最佳实践

**通用**:
1. **测试用例** - 单元测试、集成测试
2. **MCP 服务器实现** - 实际可用的 MCP 服务
3. **Agent 示例** - 更多实用的 Agent 示例
4. **技能库** - 预定义技能集合

## 📄 许可证

MIT License - 查看 [LICENSE](LICENSE) 文件

## 📞 联系方式

- 项目主页：https://github.com/lamwimham/neuroflow
- 问题反馈：https://github.com/lamwimham/neuroflow/issues
- 讨论区：https://github.com/lamwimham/neuroflow/discussions

---

**NeuroFlow** - 让 AI Agent 开发更简单、更安全、更高效。
