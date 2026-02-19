# 沙箱隔离系统

**版本**: v0.5.0  
**状态**: ✅ 生产就绪

NeuroFlow 提供三种生产级沙箱隔离方案，满足不同安全级别和平台需求。

---

## 🎯 概述

### 为什么需要沙箱？

- 🔒 **安全性** - 防止恶意代码执行
- 📦 **隔离性** - 避免代码相互影响
- 🎛️ **资源控制** - 限制 CPU、内存、时间
- 🔍 **可观测性** - 监控执行状态和性能

### 三种沙箱方案对比

| 特性 | Python 进程 | Linux Namespace | WASM |
|------|------------|-----------------|------|
| **隔离级别** | 中 | 高 | 最高 |
| **启动时间** | ~80ms | ~100ms | ~10ms |
| **内存占用** | ~15MB | ~20MB | ~5MB |
| **性能开销** | 低 | 中 | 中 |
| **安全性** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **跨平台** | ✅ | ❌ | ✅ |
| **系统访问** | 受限 | 完全隔离 | 无访问 |
| **适用场景** | 可信代码 | 半可信代码 | 不可信代码 |

---

## 📦 沙箱类型详解

### 1. Python 进程沙箱

**实现位置**: `sdk/neuroflow/sandbox/isolation.py`

**特点**:
- ✅ 完整 Python 环境
- ✅ 跨平台支持
- ✅ 简单易用
- ⚠️ 隔离级别中等

**使用示例**:

```python
from neuroflow.sandbox import SandboxIsolator, SandboxConfig, SandboxSecurityLevel

# 配置
config = SandboxConfig(
    work_dir="/tmp/sandbox",
    cpu_time_limit=30,
    memory_limit=256 * 1024 * 1024,
    security_level=SandboxSecurityLevel.STANDARD,
    allowed_commands=["python3", "pip"],
)

# 创建沙箱
isolator = SandboxIsolator(config)

# 执行代码
result = await isolator.execute("python3", ["-c", "print('Hello from sandbox!')"])

print(f"Exit code: {result.exit_code}")
print(f"Time: {result.execution_time_ms}ms")
```

**适用场景**:
- 内部可信代码
- 快速原型开发
- 教育/学习场景

---

### 2. Linux Namespace 沙箱 ⭐ 推荐

**实现位置**: `kernel/src/sandbox/namespace.rs`

**特点**:
- ✅ 完整系统隔离（PID/Mount/Network）
- ✅ cgroups v2 资源限制
- ✅ seccomp 系统调用过滤
- ⚠️ 仅支持 Linux

**安全特性**:

```rust
use kernel::sandbox::{NamespaceIsolator, SandboxConfig};

let config = SandboxConfig {
    work_dir: "/tmp/sandbox".to_string(),
    cpu_time_limit: Some(30),
    memory_limit: Some(256 * 1024 * 1024),
    file_size_limit: Some(10 * 1024 * 1024),
    enable_network: false,  // 禁用网络
    enable_seccomp: true,   // 启用系统调用过滤
};

let mut isolator = NamespaceIsolator::new(config);
let result = isolator.execute("python3", &["script.py"])?;
```

**隔离层级**:

```
Host System
└── Namespace Sandbox
    ├── PID Namespace    - 进程隔离（只能看到自身进程）
    ├── Mount Namespace  - 文件系统隔离
    ├── Network Namespace- 网络隔离（可选）
    ├── UTS Namespace    - 主机名隔离
    ├── IPC Namespace    - IPC 隔离
    └── cgroups v2       - CPU/内存限制
```

**适用场景**:
- 半可信第三方代码
- 生产环境部署
- 需要完整 Python 环境的场景

**文档**: [Namespace 集成指南](../guides/namespace-sandbox.md)

---

### 3. WASM 沙箱 ⭐ 最强隔离

**实现位置**: `kernel/src/sandbox/wasm.rs`

**特点**:
- ✅ 最强隔离（无系统访问）
- ✅ 跨平台（Linux/macOS/Windows）
- ✅ 快速启动（~10ms）
- ✅ 确定性执行
- ⚠️ 需要编译为 WASM

**安全特性**:

```python
from neuroflow.sandbox import WasmSandbox, WasmSandboxConfig

# 配置
config = WasmSandboxConfig(
    max_memory_bytes=64 * 1024 * 1024,  # 64MB 限制
    timeout_seconds=30,
    max_fuel=1_000_000,  # 100 万指令限制
    allowed_imports=[],  # 不允许任何导入
)

# 执行
async with WasmSandbox(config) as sandbox:
    with open("module.wasm", "rb") as f:
        wasm_bytes = f.read()
    
    result = await sandbox.execute(wasm_bytes)
    
    print(f"成功：{result.success}")
    print(f"时间：{result.execution_time_ms}ms")
    print(f"燃料消耗：{result.fuel_consumed}")
```

**安全模型**:

```
WASM Module
    ↓
WASM Runtime (Wasmtime/Wasmer)
    ↓
Controlled Imports (白名单)
    ↓
Resource Limits (内存/CPU/时间)
    ↓
No Direct System Access ✅
```

**适用场景**:
- 不可信第三方代码
- 需要确定性执行的场景
- 跨平台部署
- 高性能要求

**文档**: [WASM 沙箱指南](../guides/wasm-sandbox.md)

---

## 🛡️ 安全机制

### 1. 资源限制

所有沙箱都支持：

```yaml
# config/neuroflow.yaml
sandbox:
  # CPU 限制
  cpu_time_limit: 30  # 秒
  
  # 内存限制
  memory_limit: 268435456  # 256MB
  
  # 时间超时
  timeout: 30  # 秒
  
  # 文件大小
  file_size_limit: 10485760  # 10MB
  
  # 进程数
  max_processes: 10
```

### 2. 网络访问控制

```yaml
sandbox:
  # 方式 1: 完全禁用
  enable_network: false
  
  # 方式 2: 白名单
  enable_network: true
  allowed_hosts:
    - localhost
    - api.trusted.com
```

### 3. 文件系统限制

```yaml
sandbox:
  work_dir: /tmp/sandbox
  allowed_paths:
    - /tmp
    - /workspace
  # 其他路径禁止访问
```

### 4. 系统调用过滤 (Linux Namespace)

```rust
// seccomp 配置文件
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "syscalls": [
    {
      "names": ["read", "write", "open", "close"],
      "action": "SCMP_ACT_ALLOW"
    },
    {
      "names": ["ptrace", "mount", "reboot"],
      "action": "SCMP_ACT_ERRNO"  // 禁止
    }
  ]
}
```

---

## 🔧 使用指南

### 选择合适的沙箱

```python
from neuroflow.sandbox import SandboxExecutor, SandboxConfig, WasmSandboxConfig

# 场景 1: 内部可信代码 → Python 进程沙箱
executor = SandboxExecutor.new_python()

# 场景 2: 第三方插件（Linux）→ Namespace 沙箱
config = SandboxConfig.default()
executor = SandboxExecutor.new_namespace(config)

# 场景 3: 不可信代码/跨平台 → WASM 沙箱
config = WasmSandboxConfig.default()
executor = SandboxExecutor.new_wasm(config)?
```

### 统一接口

```python
# 执行代码
result = await executor.execute("python3", ["script.py"])

# 或执行 WASM
result = await executor.execute_wasm(wasm_module, input_data)
```

### 监控和管理

```python
from neuroflow.sandbox import SandboxManager

manager = SandboxManager()

# 启动
await manager.start()

# 监控
stats = await manager.get_stats()
print(f"活跃沙箱：{stats.active_sandboxes}")
print(f"总执行次数：{stats.total_executions}")
print(f"平均执行时间：{stats.avg_execution_time}ms")

# 清理
await manager.cleanup()
```

---

## 📊 性能基准

### 启动时间对比

```
WASM:          ~10ms  ████████
Python 进程：   ~80ms  ████████████████████████████████████████
Namespace:    ~100ms  ████████████████████████████████████████████
```

### 内存占用对比

```
WASM:          ~5MB   ████
Python 进程：  ~15MB  ████████████
Namespace:    ~20MB  ████████████████
```

### 执行开销对比

```
原生执行：     100ms  ████████████████████████████████████████████
WASM:         105ms  ██████████████████████████████████████████████ (+5%)
Namespace:    110ms  ████████████████████████████████████████████████ (+10%)
Python 进程：  120ms  ████████████████████████████████████████████████████ (+20%)
```

---

## ⚠️ 注意事项

### 平台支持

| 沙箱类型 | Linux | macOS | Windows |
|---------|-------|-------|---------|
| **Python 进程** | ✅ | ✅ | ✅ |
| **Namespace** | ✅ | ❌ | ❌ |
| **WASM** | ✅ | ✅ | ✅ |

### 权限要求

**Linux Namespace** 需要：
- `CAP_SYS_ADMIN` capability
- 或启用 user namespace

**WASM** 无需特殊权限。

### 限制

| 沙箱类型 | 限制 |
|---------|------|
| **Python 进程** | 隔离级别有限 |
| **Namespace** | 仅 Linux，需要权限 |
| **WASM** | 不支持 WASI（当前） |

---

## 🎯 最佳实践

### 1. 根据安全需求选择

```
可信代码     → Python 进程沙箱
半可信代码   → Namespace 沙箱
不可信代码   → WASM 沙箱
```

### 2. 合理设置限制

```yaml
# 开发环境
sandbox:
  cpu_time_limit: 60
  memory_limit: 512MB
  timeout: 60

# 生产环境
sandbox:
  cpu_time_limit: 30
  memory_limit: 256MB
  timeout: 30
```

### 3. 监控资源使用

```python
async def monitor_sandboxes():
    while True:
        stats = await manager.get_stats()
        
        if stats.active_sandboxes > 15:
            logger.warning("高沙箱使用率")
        
        if stats.avg_memory_mb > 200:
            logger.warning("高内存使用率")
        
        await asyncio.sleep(60)
```

### 4. 定期清理

```python
# 清理超时沙箱
await manager.cleanup(timeout=300)

# 清理空闲沙箱
await manager.cleanup(idle_timeout=60)
```

---

## 📚 相关文档

- [架构概览](architecture.md)
- [Namespace 集成指南](../guides/namespace-sandbox.md)
- [WASM 沙箱指南](../guides/wasm-sandbox.md)
- [性能优化](../best-practices/performance.md)
- [安全最佳实践](../best-practices/security.md)

---

**最后更新**: 2026-03-20  
**版本**: v0.5.0
