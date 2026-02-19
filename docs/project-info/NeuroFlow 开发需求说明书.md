# 📋 文档二：NeuroFlow 开发需求说明书 (Development Requirements Specification)

| 文档版本 | v1.0 |
| :--- | :--- |
| **阶段** | MVP (Minimum Viable Product) |
| **预计周期** | 8-10 周 |
| **交付物** | 可运行的框架源码、SDK、示例、文档 |

## 1. 项目目标 (Project Goals)

构建一个最小可行的 NeuroFlow 框架，满足以下核心场景：
1.  开发者能用 Python 编写 Agent 代码。
2.  框架能隔离运行这些 Agent。
3.  支持请求的语义路由。
4.  支持代码修改后的热更新。
5.  提供基础的监控和日志。

## 2. 功能需求 (Functional Requirements)

### 2.1 内核层 (Rust)

| ID | 功能点 | 描述 | 优先级 | 验收标准 |
| :--- | :--- | :--- | :--- | :--- |
| **K-01** | HTTP 网关 | 接收外部 HTTP 请求，转换为内部 gRPC 调用 | P0 | `curl` 能触发内部逻辑 |
| **K-02** | 沙箱管理 | 基于 Docker 启动 Python 运行环境 | P0 | 能启动容器，限制 CPU/Mem |
| **K-03** | 通信桥接 | 实现 Rust <-> Python gRPC 通信 | P0 | 双向通信正常，无序列化错误 |
| **K-04** | 热更新引擎 | 监听代码目录文件变化 | P1 | 修改文件后，新请求由新代码处理 |
| **K-05** | 健康检查 | 定期检测沙箱存活状态 | P1 | 僵死沙箱自动重启 |

### 2.2 SDK 层 (Python)

| ID | 功能点 | 描述 | 优先级 | 验收标准 |
| :--- | :--- | :--- | :--- | :--- |
| **S-01** | 装饰器 | 实现 `@agent`, `@tool` | P0 | 函数被正确标记元数据 |
| **S-02** | 上下文对象 | 提供 `ctx` 对象 (含 user_id, trace_id) | P0 | 函数内可访问上下文 |
| **S-03** | 本地调试 | 支持不启动 Docker 的直接运行模式 | P1 | `python agent.py` 可直接测试 |
| **S-04** | 工具调用 | 支持 Agent 内部调用 Tool | P1 | Tool 执行结果返回正确 |

### 2.3 路由与插件 (Plugins)

| ID | 功能点 | 描述 | 优先级 | 验收标准 |
| :--- | :--- | :--- | :--- | :--- |
| **P-01** | 语义路由 | 基于 Embedding 匹配 Agent | P1 | 自然语言能路由到正确 Agent |
| **P-02** | 基础护栏 | 敏感词拦截 | P2 | 触发敏感词返回错误 |

## 3. 非功能需求 (Non-Functional Requirements)

1.  **性能**:
    *   网关内部处理延迟 < 5ms (不含业务逻辑)。
    *   支持至少 50 个并发沙箱。
    *   沙箱冷启动时间 < 2s (Docker 复用优化)。
2.  **可靠性**:
    *   单个 Agent 崩溃不影响内核和其他 Agent。
    *   支持 7x24 小时稳定运行。
3.  **兼容性**:
    *   支持 Python 3.9+。
    *   支持 Linux (Ubuntu/CentOS) 部署。
4.  **安全性**:
    *   沙箱无法逃逸到宿主机。
    *   无高危依赖漏洞。

## 4. 里程碑计划 (Milestones)

### Phase 1: 核心连通 (Week 1-4)
*   **目标**: Rust 网关能调用 Python 函数。
*   **交付**:
    *   [ ] Rust 项目初始化，HTTP 接口通。
    *   [ ] Protobuf 协议定义完成。
    *   [ ] Python SDK 基础装饰器完成。
    *   [ ] **Demo**: `hello_world` 示例跑通。

### Phase 2: 隔离与路由 (Week 5-7)
*   **目标**: 支持多 Agent 隔离运行与语义分发。
*   **交付**:
    *   [ ] Docker 沙箱管理器完成。
    *   [ ] 语义路由插件完成。
    *   [ ] **Demo**: 两个 Agent 根据自然语言自动路由。

### Phase 3: 运维能力 (Week 8-10)
*   **目标**: 可观测、热更新、安全护栏。
*   **交付**:
    *   [ ] OpenTelemetry 链路追踪打通。
    *   [ ] 文件监听热更新完成。
    *   [ ] 基础 Guardrails 集成。
    *   [ ] **Demo**: 修改代码无需重启服务生效。

## 5. 交付物清单 (Deliverables)

1.  **源码仓库**: 包含 `kernel/`, `sdk/`, `proto/`, `examples/`。
2.  **构建脚本**: `Makefile` 或 `scripts/build.sh`，一键编译 Rust 和打包 Python。
3.  **文档**:
    *   `README.md`: 如何从源码构建。
    *   `SDK Reference`: Python 接口文档。
    *   `Architecture.md`: 架构设计文档。
4.  **测试报告**: 单元测试覆盖率报告，压测报告。

## 6. 开发规范 (Development Standards)

1.  **代码风格**:
    *   Rust: 遵循 `rustfmt` 默认配置。
    *   Python: 遵循 `PEP 8`, 使用 `black` 格式化。
2.  **提交规范**:
    *   Commit Message 格式：`type(scope): subject` (e.g., `feat(kernel): add http gateway`)。
3.  **分支管理**:
    *   `main`: 稳定分支。
    *   `dev`: 开发分支。
    *   `feature/*`: 功能分支。
4.  **错误处理**:
    *   Rust: 禁止 `unwrap()`，使用 `Result` 透传。
    *   Python: 捕获异常并转换为标准错误码返回给内核。

---

# 🚀 附录：开发人员快速启动指南 (For Developers)

**请所有开发人员严格执行以下步骤初始化环境：**

### 1. 克隆与初始化
```bash
git clone <repo-url> neuroflow
cd neuroflow

# 安装 Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 安装 Python 依赖
python -m venv .venv
source .venv/bin/activate
pip install -e ./sdk  # 关键：本地 editable 安装
pip install -r requirements-dev.txt
```

### 2. 生成 Protobuf 代码
```bash
# 每次修改 proto 文件后执行
make proto-gen
```

### 3. 运行测试
```bash
# Rust 测试
cd kernel && cargo test

# Python 测试
cd sdk && pytest
```

### 4. 本地联调
```bash
# 终端 1：启动内核
cd kernel && cargo run

# 终端 2：运行示例 Agent
python examples/hello_agent.py
```

---

**批准人签字:**

架构师：____________________ 日期：____________________

项目负责人：________________ 日期：____________________