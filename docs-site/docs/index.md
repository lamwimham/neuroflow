# NeuroFlow v0.5.0

**让 AI Agent 开发更简单、更安全、更高效**

[![CI](https://github.com/lamwimham/neuroflow/actions/workflows/ci.yml/badge.svg)](https://github.com/lamwimham/neuroflow/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/pypi/v/neuroflow-sdk.svg)](https://pypi.org/project/neuroflow-sdk/)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://neuroflow.ai/)

---

## 🎉 新版本 v0.5.0

**v0.5.0 "Performance & Security"** 已发布！

### 核心特性

- 🛡️ **沙箱安全增强** - Linux namespace 隔离，达到生产级安全标准
- ⚡ **性能优化** - 完整的基准测试套件，性能提升 35%+
- 🔍 **可观测性** - OpenTelemetry 集成，全链路追踪
- 🖥️ **Web 控制台** - 可视化的 Agent 管理和监控
- 📦 **Skill 市场** - 10+ 预置 Skills，Skill 导入/导出

[查看发布说明](guides/release-notes/v0.5.0.md){ .md-button .md-button--primary }
[快速开始](getting-started/installation.md){ .md-button }

---

## 🚀 快速开始

### ⚡ 5 分钟安装

```bash
# 安装 SDK
cd sdk
pip install -e .

# 验证安装
python -c "from neuroflow import AINativeAgent; print('✓ 安装成功')"
```

### 🎯 30 分钟入门

1. [安装 NeuroFlow](getting-started/installation.md)
2. [创建第一个 Agent](getting-started/first-agent.md)
3. [运行示例代码](examples/basic.md)

### 📖 完整文档

- [新手入门](getting-started/quickstart.md) - 快速上手指南
- [核心概念](concepts/architecture.md) - 理解架构设计
- [开发指南](guides/cli.md) - 详细的开发教程
- [API 参考](api-reference/python/index.md) - 完整的 API 文档

### 💻 示例代码

- [基础示例](examples/basic.md) - 简单的 Agent 示例
- [高级示例](examples/advanced.md) - 复杂场景示例
- [生产示例](examples/production.md) - 生产环境示例

---

## 🎯 核心价值

**让 LLM 自主决定使用工具，而非被动执行代码。**

- 🤖 **AI Native** - LLM 自主决定使用 MCP/Skills/Tools
- 🔌 **统一工具接口** - 支持 Local/MCP/Skills/Agents
- 🧠 **记忆管理** - 向量记忆、语义检索
- 🤝 **A2A 协作** - Agent 间自主协作
- 🎓 **技能学习** - LLM 驱动的技能生成
- 🛡️ **沙箱安全** - Linux namespace 隔离，生产级安全
- 📊 **可观测性** - 全链路追踪，性能监控
- 🖥️ **Web 控制台** - 可视化管理界面

---

## ✨ v0.5.0 新特性

### 1. 沙箱安全增强 🛡️

采用 Linux namespace 实现进程、文件系统、网络完全隔离。

```python
from neuroflow.sandbox import SandboxIsolator, SandboxConfig

config = SandboxConfig(
    security_level=SandboxSecurityLevel.STRICT,
    cpu_time_limit=30,
    memory_limit=256 * 1024 * 1024,
)

isolator = SandboxIsolator(config)
result = await isolator.execute("python3", ["script.py"])
```

[查看沙箱安全白皮书](https://github.com/lamwimham/neuroflow/blob/main/docs/SECURITY_WHITEPAPER_v0.5.0.md){ target="_blank" }

### 2. 性能优化 ⚡

完整的基准测试套件，性能提升 35%+。

| 指标 | v0.4.2 | v0.5.0 | 提升 |
|------|--------|--------|------|
| Gateway 延迟 (P50) | 15ms | 10ms | 33% ↓ |
| Gateway 延迟 (P99) | 50ms | 30ms | 40% ↓ |
| 工具调用 | 80ms | 50ms | 37% ↓ |
| A2A 通信 | 150ms | 100ms | 33% ↓ |

[查看性能报告](https://github.com/lamwimham/neuroflow/blob/main/sdk/benchmarks/benchmark_v0.5.0.py){ target="_blank" }

### 3. 可观测性 🔍

OpenTelemetry 集成，全链路追踪。

```python
from neuroflow.observability import TracingService

tracing = TracingService(
    service_name="my-agent",
    exporter_endpoint="http://localhost:4317",
)

with tracing.span("tool_execution") as span:
    await execute_tool()
```

[查看可观测性指南](https://github.com/lamwimham/neuroflow/blob/main/sdk/neuroflow/observability/tracing.py){ target="_blank" }

### 4. Web 控制台 🖥️

可视化的 Agent 管理和监控。

- Dashboard - 实时系统状态
- Agent 管理 - 创建/查看/删除
- 对话调试 - 实时对话测试
- 监控面板 - 性能指标可视化

[查看 Web 控制台文档](https://github.com/lamwimham/neuroflow/blob/main/web-console/README.md){ target="_blank" }

---

## 📊 架构设计

```
┌─────────────────────────────────────────┐
│      Python SDK (业务逻辑层)             │
│  • Agent 定义                           │
│  • 工具系统                             │
│  • MCP 集成                             │
│  • 沙箱隔离                             │
│  • 可观测性                             │
├─────────────────────────────────────────┤
│      Rust Kernel (基础设施层)            │
│  • HTTP/gRPC 网关                        │
│  • WASM/进程沙箱                        │
│  • Namespace 隔离                        │
│  • 资源调度                             │
│  • 可观测性                             │
└─────────────────────────────────────────┘
```

### 核心设计原则

1. **关注点分离**: Rust 专注基础设施，Python 专注业务逻辑
2. **深度防御**: 多层安全隔离机制
3. **数据驱动**: 基于基准测试的性能优化
4. **可观测性**: 全链路追踪和监控

---

## 📦 核心组件

### Rust 内核

| 组件 | 说明 | 状态 |
|------|------|------|
| HTTP 网关 | Axum + Tokio 高性能网关 | ✅ 可用 |
| 沙箱隔离 | Linux namespace 隔离 | ✅ 新增 |
| 资源限制 | cgroups v2 CPU/内存限制 | ✅ 新增 |
| 可观测性 | OpenTelemetry 集成 | ✅ 新增 |

### Python SDK

| 组件 | 说明 | 状态 |
|------|------|------|
| NeuroFlowSDK | 统一的 SDK 入口 | ✅ 可用 |
| @agent 装饰器 | Agent 定义 | ✅ 可用 |
| @tool 装饰器 | 工具定义 | ✅ 可用 |
| 沙箱隔离 | Linux namespace 隔离 | ✅ 新增 |
| 可观测性 | 链路追踪/指标收集 | ✅ 新增 |
| Web 控制台 | 可视化管理界面 | ✅ 新增 |

---

## 📈 性能指标

| 指标 | 当前 | 目标 | 状态 |
|------|------|------|------|
| Gateway 延迟 (P50) | 10ms | < 10ms | ✅ |
| Gateway 延迟 (P99) | 30ms | < 30ms | ✅ |
| 并发沙箱数 | 10+ | 10+ | ✅ |
| 沙箱启动时间 | 100ms | < 100ms | ✅ |
| 并发 Agent 支持 | 100 | 100+ | ✅ |

[查看详细性能基准测试报告](guides/performance/benchmark.md)

---

## 🗺️ 路线图

### Phase 1: AI Native 基础架构 ✅

- [x] 统一工具协议层
- [x] LLM Orchestrator 核心
- [x] AI Native Agent
- [x] Function Calling 支持
- [x] 基础文档和示例

**详情**: [PHASE1_COMPLETE.md](https://github.com/lamwimham/neuroflow/blob/main/docs/PHASE1_COMPLETE.md)

### Phase 2: MCP 集成和示例完善 ✅

- [x] MCP 工具发现和集成
- [x] 3 个完整示例代码
- [x] 混合工具使用
- [x] 完善文档
- [x] Python 测试覆盖

**详情**: [PHASE2_COMPLETE.md](https://github.com/lamwimham/neuroflow/blob/main/docs/PHASE2_COMPLETE.md)

### Phase 3: 高级特性 ✅

- [x] A2A 协作机制
- [x] 技能学习系统
- [x] 记忆系统增强
- [x] Phase 3 示例代码
- [x] 完整文档

**详情**: [PHASE3_COMPLETE.md](https://github.com/lamwimham/neuroflow/blob/main/docs/PHASE3_COMPLETE.md)

### Phase 4: 生产力工具链 ✅

- [x] CLI 工具开发
- [x] Rust 内核完善
- [x] 性能基准测试
- [x] 完整文档

**详情**: [PHASE4_COMPLETE.md](https://github.com/lamwimham/neuroflow/blob/main/docs/PHASE4_COMPLETE.md)

### Phase 5: 性能与安全 ✅ (NEW!)

- [x] 沙箱安全增强 (Linux namespace)
- [x] 性能优化 (提升 35%+)
- [x] 可观测性 (OpenTelemetry)
- [x] Web 控制台 MVP
- [x] Skill 市场

**详情**: [RELEASE_NOTES_v0.5.0.md](guides/release-notes/v0.5.0.md)

### Phase 6: 生态建设 (计划中)

- [ ] Web 控制台增强
- [ ] 插件系统
- [ ] Skill 云平台
- [ ] 企业功能
- [ ] Agent 市场

---

## 🤝 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 发起 Pull Request

### 当前优先贡献方向

**v0.5.0 相关**:
1. **Web 控制台功能增强** - 更多可视化功能
2. **Skill 市场扩展** - 贡献你的 Skills
3. **性能优化** - 发现并优化性能瓶颈
4. **文档完善** - 教程、示例、最佳实践

**通用**:
1. **测试用例** - 单元测试、集成测试
2. **MCP 服务器实现** - 实际可用的 MCP 服务
3. **Agent 示例** - 更多实用的 Agent 示例
4. **安全审计** - 发现和修复安全问题

---

## 📞 社区

- **项目主页**: https://github.com/lamwimham/neuroflow
- **问题反馈**: https://github.com/lamwimham/neuroflow/issues
- **讨论区**: https://github.com/lamwimham/neuroflow/discussions
- **文档**: https://neuroflow.ai/

---

## 📄 许可证

MIT License - 查看 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

感谢所有为 NeuroFlow 做出贡献的开发者和社区成员！

---

**NeuroFlow** - 让 AI Agent 开发更简单、更安全、更高效。

*Last updated: 2026-03-20*
