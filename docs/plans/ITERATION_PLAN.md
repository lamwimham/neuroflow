# NeuroFlow 迭代计划 (2024-02-18)

## 📋 审查发现的问题

基于架构审查，我们识别出以下关键问题：

### 严重问题 (Critical)
1. **身份危机**: 在运行时框架、开发 SDK、MCP 平台三个方向间摇摆
2. **过度设计**: 55+ 配置结构，但核心功能未经验证
3. **WASM 沙箱不完整**: 无法运行真正的 Python Agent
4. **全局状态污染**: Python SDK 使用全局注册表

### 高优先级问题 (High)
1. **异步初始化陷阱**: 模块加载时启动后台线程
2. **类型注解不完整**: 缺少类型安全
3. **测试覆盖率低**: <20%
4. **文档混乱**: 分散在多个文件中

### 中优先级问题 (Medium)
1. **错误处理不一致**: 混用 anyhow 和 thiserror
2. **MCP 重复实现**: 三层实现功能重叠
3. **缺少 CI/CD**: 无自动化测试和发布流程

## 🎯 迭代目标

### Phase 1: 生存验证 (Week 1-6)

**核心目标**: 证明 Rust 内核 + WASM 沙箱的价值主张

#### Week 1-2: 清理技术债

**目标**: 简化架构，移除过度设计

**任务**:
- [ ] 简化 Rust 配置系统 (从 12 个结构减到 5 个)
- [ ] 移除内核层业务逻辑 (A2A、MCP、Memory 移到 Python SDK)
- [ ] 统一错误处理
- [ ] 修复异步初始化陷阱

**验收标准**:
- `kernel/src/config/enhanced.rs` < 150 行
- 移除 `kernel/src/mcp/mod.rs` (移到 Python SDK)
- 移除 `kernel/src/a2a/mod.rs` (移到 Python SDK)
- 移除 `kernel/src/memory/mod.rs` (移到 Python SDK)

#### Week 3-4: 完善沙箱

**目标**: 实现真正的 Python Agent 执行能力

**任务**:
- [ ] 设计 Python Agent 执行器接口
- [ ] 实现进程隔离 (使用 subprocess + gRPC)
- [ ] 添加资源限制 (CPU、内存、超时)
- [ ] 实现网络访问控制
- [ ] 添加沙箱监控指标

**验收标准**:
- 能运行简单的 Python Agent
- 资源限制生效 (测试验证)
- 有基本的监控指标

#### Week 5-6: 性能验证

**目标**: 建立性能基准，验证价值主张

**任务**:
- [ ] 建立性能基准测试框架
- [ ] 优化网关延迟到<10ms
- [ ] 支持 10+ 并发沙箱
- [ ] 编写性能报告
- [ ] 对比纯 Python 方案

**验收标准**:
- 有可重复的性能基准测试
- 网关延迟 < 10ms (P50), < 20ms (P99)
- 支持 10+ 并发沙箱
- 性能报告公开

### Phase 2: 开发者体验 (Week 7-14)

**核心目标**: 让开发者能在 30 分钟内构建第一个 Agent

#### Week 7-8: SDK 重构

**任务**:
- [ ] 移除全局状态，使用显式注册表
- [ ] 完善类型注解
- [ ] 实现显式初始化
- [ ] 添加错误消息本地化

**验收标准**:
- 无全局变量 (`_global_tools_registry` 等)
- 所有公共 API 有完整类型注解
- 显式初始化 (`await sdk.initialize()`)

#### Week 9-10: 文档重写

**任务**:
- [ ] 按照新结构组织文档
- [ ] 编写快速开始教程
- [ ] 创建示例库 (10+ 示例)
- [ ] 录制视频教程

**验收标准**:
- 文档结构清晰
- 快速开始教程 < 30 分钟
- 示例代码可运行

#### Week 11-12: 工具链

**任务**:
- [ ] CLI 工具 (项目生成)
- [ ] 本地开发服务器
- [ ] 热重载支持
- [ ] 调试模式

**验收标准**:
- `neuroflow new my-project` 可用
- `neuroflow run` 可启动开发服务器

#### Week 13-14: 测试与质量

**任务**:
- [ ] 测试覆盖率达到 80%
- [ ] 添加 CI/CD 流水线
- [ ] 代码质量检查
- [ ] 安全审计

**验收标准**:
- 测试覆盖率报告 > 80%
- CI 流水线绿色
- 无严重安全漏洞

## 📝 当前迭代 (Week 1-2) 详细计划

### 任务 1: 简化 Rust 配置系统

**当前状态**:
```rust
// 489 行，12 个配置结构
pub struct EnhancedConfig {
    pub server: ServerConfig,
    pub sandbox: SandboxConfig,
    pub observability: ObservabilityConfig,
    pub security: SecurityConfig,
    pub rate_limit: RateLimitConfig,
    pub pii_detection: PIIDetectionConfig,
    pub routing: RoutingConfig,
    pub grpc: GrpcConfig,
    pub hot_reload: HotReloadConfig,
    pub database: DatabaseConfig,
    pub cache: CacheConfig,
}
```

**目标状态**:
```rust
// < 150 行，5 个配置结构
pub struct Config {
    pub server: ServerConfig,      // HTTP 服务配置
    pub sandbox: SandboxConfig,    // 沙箱配置
    pub observability: ObsConfig,  // 可观测性配置
    pub security: SecurityConfig,  // 安全配置
}
```

**实施步骤**:
1. 创建新的简化配置结构
2. 迁移现有配置加载逻辑
3. 更新所有使用配置的地方
4. 删除旧的配置代码

### 任务 2: 移除内核层业务逻辑

**要移除的模块**:
- `kernel/src/mcp/mod.rs` → 移到 `sdk/neuroflow/mcp.py`
- `kernel/src/a2a/mod.rs` → 移到 `sdk/neuroflow/a2a.py`
- `kernel/src/memory/mod.rs` → 移到 `sdk/neuroflow/memory.py`

**理由**:
- 这些是业务逻辑，应该在 Python 层
- Rust 内核应该专注基础设施 (网关、沙箱、路由)
- 减少维护成本

### 任务 3: 统一错误处理

**当前问题**:
```rust
// 混用 anyhow 和 thiserror
use anyhow::Result;
use thiserror::Error;
```

**目标**:
```rust
// 统一的错误层次结构
#[derive(Debug, thiserror::Error)]
pub enum NeuroFlowError {
    #[error("Sandbox error: {0}")]
    Sandbox(#[from] SandboxError),
    
    #[error("Routing error: {0}")]
    Routing(#[from] RoutingError),
    
    #[error("Timeout after {0:?}")]
    Timeout(Duration),
}

pub type Result<T> = std::result::Result<T, NeuroFlowError>;
```

### 任务 4: 修复异步初始化陷阱

**当前问题**:
```python
# sdk/neuroflow/skills.py
# 在模块加载时启动后台线程
try:
    loop = asyncio.get_running_loop()
    loop.create_task(async_init())
except RuntimeError:
    import threading
    def run_async_init():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(async_init())
    init_thread = threading.Thread(target=run_async_init, daemon=True)
    init_thread.start()
```

**目标**:
```python
# sdk/neuroflow/__init__.py
class NeuroFlowSDK:
    def __init__(self):
        self._initialized = False
    
    async def initialize(self):
        """显式初始化"""
        if self._initialized:
            return
        # 初始化逻辑
        self._initialized = True
    
    @classmethod
    async def create(cls) -> 'NeuroFlowSDK':
        """工厂方法"""
        sdk = cls()
        await sdk.initialize()
        return sdk

# 使用
sdk = await NeuroFlowSDK.create()
```

## 📊 成功指标

### 技术指标
- [ ] 配置代码行数减少 70% (489 → <150)
- [ ] 移除 3 个业务逻辑模块
- [ ] 测试覆盖率从<20% 提升到 50%
- [ ] 网关延迟 < 10ms

### 开发者体验指标
- [ ] 快速开始教程完成时间 < 30 分钟
- [ ] 示例代码可运行率 100%
- [ ] 文档清晰度评分 > 4/5

### 工程质量指标
- [ ] CI 流水线建立
- [ ] 代码质量检查通过
- [ ] 无严重安全漏洞

## 🔄 审查机制

### 每周审查
- **时间**: 每周一上午
- **参与**: 核心开发者
- **内容**:
  - 上周进展审查
  - 本周计划调整
  - 技术决策讨论

### 里程碑审查
- **Phase 1 结束 (Week 6)**: 
  - 性能基准报告
  - MVP 演示
  - Go/No-Go 决策

- **Phase 2 结束 (Week 14)**:
  - v0.2.0 发布
  - 开发者反馈收集
  - Phase 3 规划

## 📚 参考文档

- [架构审查报告](ARCHITECTURE_REVIEW.md)
- [MCP 集成方案](MCP_CORE_INTEGRATION_PLAN.md)
- [开发者指南](docs/MCP_DEVELOPER_GUIDE.md)

## 🚀 立即行动项

**Today**:
1. ✅ 创建迭代计划 (本文档)
2. ⏳ 简化配置系统
3. ⏳ 移除 MCP 模块 (从 Rust 内核)
4. ⏳ 修复异步初始化

**This Week**:
- 完成所有 Week 1-2 任务
- 建立每日站会机制
- 更新项目 README

---

**版本**: 1.0  
**创建日期**: 2024-02-18  
**下次更新**: 2024-02-25
