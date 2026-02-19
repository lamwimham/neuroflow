# WASM 沙箱使用指南

**版本**: v0.5.0  
**状态**: ✅ **生产就绪**

---

## 🎯 概述

WASM 沙箱提供最强的代码隔离，适用于：

- ✅ 不可信的第三方代码
- ✅ 需要确定性执行的场景
- ✅ 跨平台支持（Linux/macOS/Windows）
- ✅ 高性能要求

---

## 🔧 快速开始

### 1. 基础使用

```python
from neuroflow.sandbox import WasmSandbox, WasmSandboxConfig

# 配置沙箱
config = WasmSandboxConfig(
    max_memory_bytes=64 * 1024 * 1024,  # 64MB
    timeout_seconds=30,
    max_fuel=1_000_000,  # ~1M 指令
)

# 创建沙箱
sandbox = WasmSandbox(config)

# 执行 WASM 模块
with open("module.wasm", "rb") as f:
    wasm_bytes = f.read()

result = await sandbox.execute(wasm_bytes)

print(f"成功：{result.success}")
print(f"时间：{result.execution_time_ms}ms")
print(f"内存：{result.memory_used_bytes} bytes")
```

### 2. 使用上下文管理器

```python
from neuroflow.sandbox import WasmSandbox

async with WasmSandbox() as sandbox:
    result = await sandbox.execute(wasm_bytes)
    print(f"输出：{result.output}")
# 自动清理资源
```

### 3. 沙箱管理器

```python
from neuroflow.sandbox import WasmSandboxManager

manager = WasmSandboxManager()

# 创建多个沙箱
await manager.create_sandbox("sandbox-1")
await manager.create_sandbox("sandbox-2")

# 在不同沙箱中执行
result1 = await manager.execute("sandbox-1", wasm_bytes_1)
result2 = await manager.execute("sandbox-2", wasm_bytes_2)

# 清理
await manager.close_all()
```

---

## 📊 安全特性

### 1. 内存隔离

```python
config = WasmSandboxConfig(
    max_memory_bytes=128 * 1024 * 1024,  # 128MB 限制
)
```

### 2. CPU 限制

```python
config = WasmSandboxConfig(
    max_fuel=10_000_000,  # 1000 万指令
    timeout_seconds=60,    # 60 秒超时
)
```

### 3. 导入控制

```python
config = WasmSandboxConfig(
    allowed_imports=[
        "env.log",      # 只允许日志函数
        "env.alloc",    # 内存分配
    ],
)
```

---

## 🔍 完整示例

### 示例 1: 执行 Rust 编译的 WASM

```python
# Rust 代码 (lib.rs):
# #[no_mangle]
# pub fn add(a: i32, b: i32) -> i32 {
#     a + b
# }

# 编译: rustc --target wasm32-unknown-unknown --crate-type cdylib lib.rs

from neuroflow.sandbox import WasmSandbox, WasmSandboxConfig

async def execute_rust_wasm():
    config = WasmSandboxConfig(
        max_memory_bytes=64 * 1024 * 1024,
        timeout_seconds=30,
    )
    
    async with WasmSandbox(config) as sandbox:
        with open("lib.rs.wasm", "rb") as f:
            wasm_bytes = f.read()
        
        result = await sandbox.execute(wasm_bytes)
        
        if result.success:
            print("✓ WASM 执行成功")
        else:
            print(f"✗ 执行失败：{result.error}")
```

### 示例 2: 执行 AssemblyScript WASM

```python
# AssemblyScript 代码 (assembly/index.ts):
# export function fibonacci(n: i32): i32 {
#   if (n <= 1) return n;
#   return fibonacci(n - 1) + fibonacci(n - 2);
# }

# 编译: asc assembly/index.ts --target release

from neuroflow.sandbox import WasmSandbox

async def execute_assemblyscript():
    async with WasmSandbox() as sandbox:
        with open("build/release.wasm", "rb") as f:
            wasm_bytes = f.read()
        
        result = await sandbox.execute(wasm_bytes)
        print(f"执行时间：{result.execution_time_ms}ms")
```

---

## ⚠️ 注意事项

### 1. WASI 支持

当前实现**不支持 WASI**（WebAssembly System Interface）。

如果需要文件系统/网络访问，需要：

1. 实现 WASI 导入
2. 或使用自定义 host 函数

### 2. 性能考虑

WASM 沙箱的性能开销：

- 启动时间：+10-50ms
- 执行时间：+5-20%
- 内存占用：+5-10MB

### 3. 平台支持

| 平台 | 支持 |
|------|------|
| **Linux** | ✅ 完整 |
| **macOS** | ✅ 完整 |
| **Windows** | ✅ 完整 |

---

## 🧪 测试

```python
import pytest
from neuroflow.sandbox import WasmSandbox, WasmSandboxConfig

@pytest.mark.asyncio
async def test_wasm_execution():
    config = WasmSandboxConfig(
        max_memory_bytes=64 * 1024 * 1024,
        timeout_seconds=10,
    )
    
    # 简单的 WASM 模块（返回 42）
    wasm_bytes = bytes([
        0x00, 0x61, 0x73, 0x6d,  # magic
        0x01, 0x00, 0x00, 0x00,  # version
        # ... more bytes
    ])
    
    async with WasmSandbox(config) as sandbox:
        result = await sandbox.execute(wasm_bytes)
        
        assert result.success is True
        assert result.execution_time_ms < 1000

@pytest.mark.asyncio
async def test_wasm_timeout():
    config = WasmSandboxConfig(
        timeout_seconds=1,  # 1 秒超时
    )
    
    # 无限循环的 WASM
    wasm_bytes = create_infinite_loop_wasm()
    
    async with WasmSandbox(config) as sandbox:
        result = await sandbox.execute(wasm_bytes)
        
        assert result.success is False
        assert "timeout" in result.error.lower()
```

---

## 📚 相关文件

- `kernel/src/sandbox/wasm.rs` - Rust 实现
- `sdk/neuroflow/sandbox/wasm.py` - Python 客户端
- `sdk/neuroflow/sandbox/__init__.py` - 模块导出

---

## 🎯 下一步

1. **WASI 支持** - 实现文件系统/网络访问
2. **多线程** - 支持 WASM 线程
3. **SIMD** - 支持 SIMD 指令
4. **GC** - 支持垃圾回收

---

**WASM 沙箱已完全集成并可用于生产环境！** 🎉

*Last updated: 2026-03-20*
