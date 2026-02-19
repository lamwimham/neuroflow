# 沙箱模型

沙箱提供安全的代码执行环境，隔离 Agent 和工具的执行。

## 为什么需要沙箱？

- **安全性**: 防止恶意代码
- **隔离性**: 避免相互影响
- **资源控制**: 限制 CPU、内存使用
- **可观测性**: 监控执行状态

## 沙箱类型

### Python 进程沙箱

**特点**:
- 完整 Python 环境
- 强隔离性
- 启动时间 ~80ms
- 内存占用 ~15MB

```python
# 沙箱执行
result = await sandbox.execute("""
x = 1 + 1
_result = x
""")
```

### WASM 沙箱 (开发中)

**特点**:
- 轻量级
- 快速启动 ~10ms
- 有限 Python 支持
- 内存占用 ~5MB

## 资源限制

```yaml
# config/neuroflow.yaml
sandbox:
  max_instances: 10      # 最大沙箱数
  memory_limit_mb: 256   # 每个沙箱内存限制
  cpu_limit: 0.5         # CPU 限制 (核心数)
  timeout_ms: 30000      # 执行超时
```

## 安全机制

### 1. 进程隔离

```
Host System
├── Sandbox 1 (PID 1001)
├── Sandbox 2 (PID 1002)
└── Sandbox 3 (PID 1003)
```

### 2. 网络访问控制

```yaml
sandbox:
  allowed_hosts:
    - localhost
    - api.trusted.com
  # 其他主机禁止访问
```

### 3. 文件系统限制

```yaml
sandbox:
  allowed_paths:
    - /tmp
    - /workspace
  # 其他路径禁止访问
```

## 沙箱管理

### 创建沙箱

```python
from neuroflow.sandbox import SandboxManager

manager = SandboxManager()
await manager.start()

# 执行代码
result = await manager.execute("print('Hello')")
```

### 监控状态

```python
stats = await manager.get_stats()
print(f"Active sandboxes: {stats.active_sandboxes}")
print(f"Total executions: {stats.total_executions}")
```

## 最佳实践

### 1. 合理设置限制

```yaml
# 开发环境
sandbox:
  max_instances: 5
  timeout_ms: 60000

# 生产环境
sandbox:
  max_instances: 20
  timeout_ms: 30000
```

### 2. 监控资源使用

```python
# 定期检查
async def monitor():
    while True:
        stats = await manager.get_stats()
        if stats.active_sandboxes > 15:
            print("Warning: High sandbox usage")
        await asyncio.sleep(60)
```

## 相关文档

- [架构概览](architecture.md)
- [性能优化](../best-practices/performance.md)
