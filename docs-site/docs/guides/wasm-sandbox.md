# WASM 沙箱使用指南

**版本**: v0.5.0  
**状态**: ✅ 生产就绪

本指南介绍如何在 NeuroFlow 中使用 WASM 沙箱进行安全代码执行。

---

## 🎯 概述

WASM（WebAssembly）沙箱提供最强的代码隔离：

- ✅ 完全系统隔离（无直接访问）
- ✅ 跨平台支持（Linux/macOS/Windows）
- ✅ 快速启动（~10ms）
- ✅ 确定性执行
- ✅ 资源限制（内存/CPU/指令）

---

## 🔧 安装和配置

### 系统要求

- **Rust**: 1.70+
- **WASM 运行时**: Wasmtime 15 或 Wasmer 4
- **Python**: 3.9+ (用于 Python SDK)

### 安装依赖

```bash
# Rust 项目会自动安装
# kernel/Cargo.toml 已包含：
# wasmtime = "15"
# wasmer = "4"
# wasmer-compiler-singlepass = "4"
```

---

## 💻 使用方式

### Rust 内核集成

```rust
use kernel::sandbox::{WasmSandbox, WasmSandboxConfig, WasmModule};

// 1. 配置沙箱
let config = WasmSandboxConfig {
    max_memory_bytes: 64 * 1024 * 1024,  // 64MB
    timeout: Duration::from_secs(30),
    max_fuel: Some(1_000_000),  // 100 万指令
    allowed_imports: vec![],  // 不允许任何导入
    runtime: WasmRuntime::Wasmtime,
    enable_logging: false,
};

// 2. 创建沙箱
let mut sandbox = WasmSandbox::new(config)?;

// 3. 加载 WASM 模块
let wasm_bytes = std::fs::read("module.wasm")?;
let module = WasmModule::new(wasm_bytes);

// 4. 执行
let result = sandbox.execute(&module, &[])?;

println!("成功：{}", result.success);
println!("时间：{}ms", result.execution_time_ms);
println!("燃料：{:?}", result.fuel_consumed);
```

### Python SDK 调用

```python
from neuroflow.sandbox import WasmSandbox, WasmSandboxConfig

# 配置
config = WasmSandboxConfig(
    max_memory_bytes=64 * 1024 * 1024,  # 64MB
    timeout_seconds=30,
    max_fuel=1_000_000,  # 100 万指令
)

# 创建沙箱并执行
async with WasmSandbox(config) as sandbox:
    with open("module.wasm", "rb") as f:
        wasm_bytes = f.read()
    
    result = await sandbox.execute(wasm_bytes)
    
    print(f"成功：{result.success}")
    print(f"时间：{result.execution_time_ms}ms")
    print(f"内存：{result.memory_used_bytes} bytes")
```

---

## 🔒 安全配置

### 1. 内存限制

```python
config = WasmSandboxConfig(
    max_memory_bytes=128 * 1024 * 1024,  # 128MB
)
```

### 2. CPU 限制

```python
config = WasmSandboxConfig(
    max_fuel=10_000_000,  # 1000 万指令
    timeout_seconds=60,
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

## 🧪 编译 WASM 模块

### Rust 编译

```bash
# 添加 WASM 目标
rustup target add wasm32-unknown-unknown

# 创建 WASM 项目
cargo new --lib my-wasm-module
cd my-wasm-module

# 编辑 Cargo.toml
cat >> Cargo.toml << EOF

[lib]
crate-type = ["cdylib"]

[profile.release]
opt-level = "z"
lto = true
EOF

# 编译
cargo build --target wasm32-unknown-unknown --release

# 输出文件
# target/wasm32-unknown-unknown/release/my_wasm_module.wasm
```

### Rust 示例代码

```rust
// lib.rs
#![no_std]

#[no_mangle]
pub extern "C" fn add(a: i32, b: i32) -> i32 {
    a + b
}

#[no_mangle]
pub extern "C" fn fibonacci(n: i32) -> i32 {
    if n <= 1 {
        n
    } else {
        fibonacci(n - 1) + fibonacci(n - 2)
    }
}

#[no_mangle]
pub extern "C" fn _start() {
    // 入口点
}
```

### AssemblyScript 编译

```bash
# 安装 AssemblyScript
npm install -g assemblyscript

# 创建项目
asc --init

# 编辑 assembly/index.ts
cat > assembly/index.ts << EOF
export function add(a: i32, b: i32): i32 {
  return a + b;
}

export function fibonacci(n: i32): i32 {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}
EOF

# 编译
npm run asbuild

# 输出文件
# build/release.wasm
```

---

## 🧪 测试

### 单元测试

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_wasm_execution() {
        let config = WasmSandboxConfig::default();
        let mut sandbox = WasmSandbox::new(config).unwrap();
        
        // 简单的 WASM 模块（返回 42）
        let wasm_bytes = vec![
            0x00, 0x61, 0x73, 0x6d,  // magic
            0x01, 0x00, 0x00, 0x00,  // version
            // ... more bytes for a valid module
        ];
        
        let module = WasmModule::new(wasm_bytes);
        let result = sandbox.execute(&module, &[]).unwrap();
        
        assert!(result.success);
        assert!(result.execution_time_ms < 1000);
    }

    #[test]
    fn test_wasm_timeout() {
        let config = WasmSandboxConfig {
            timeout: Duration::from_secs(1),
            ..Default::default()
        };
        
        let mut sandbox = WasmSandbox::new(config).unwrap();
        
        // 无限循环的 WASM
        let infinite_loop_wasm = create_infinite_loop_wasm();
        let module = WasmModule::new(infinite_loop_wasm);
        
        let result = sandbox.execute(&module, &[]).unwrap();
        
        assert!(!result.success);
        assert!(result.error.unwrap().contains("timeout"));
    }

    #[test]
    fn test_wasm_validation() {
        // 无效的 WASM
        let invalid = vec![0x00, 0x01, 0x02, 0x03];
        assert!(WasmModule::validate(&invalid).is_err());
        
        // 有效的 WASM
        let valid = get_valid_wasm_module();
        assert!(WasmModule::validate(&valid).is_ok());
    }
}
```

### 集成测试

```bash
# 运行测试
cd kernel
cargo test --package kernel --lib sandbox::wasm
```

---

## ⚠️ 故障排除

### 问题 1: WASM 编译失败

**错误**: `WASM compilation failed: invalid magic number`

**解决**:

```bash
# 验证 WASM 文件
wasm-validate module.wasm

# 检查 magic number
xxd module.wasm | head -1
# 应该是：00 61 73 6d (magic number)
```

### 问题 2: 导入错误

**错误**: `Import not allowed: env.system`

**解决**:

```python
# 添加允许的导入
config = WasmSandboxConfig(
    allowed_imports=[
        "env.system",  # 添加此导入
        "env.log",
    ],
)
```

### 问题 3: 内存不足

**错误**: `Resource limit exceeded: memory`

**解决**:

```python
# 增加内存限制
config = WasmSandboxConfig(
    max_memory_bytes=256 * 1024 * 1024,  # 256MB
)
```

---

## 📊 性能基准

### 启动时间

```
WASM:          ~10ms  ████████
Python 进程：   ~80ms  ████████████████████████████████████████
Namespace:    ~100ms  ████████████████████████████████████████████
```

### 内存占用

```
WASM:        ~5MB   ████
Python 进程：~15MB  ████████████
Namespace:  ~20MB  ████████████████
```

### 执行开销

```
原生执行：100ms  ████████████████████████████████████████████
WASM:    105ms  ██████████████████████████████████████████████ (+5%)
```

---

## 📚 相关文档

- [沙箱概念](../concepts/sandbox.md)
- [沙箱使用指南](sandbox-usage.md)
- [Namespace 沙箱](namespace-sandbox.md)
- [安全最佳实践](../best-practices/security.md)

---

**最后更新**: 2026-03-20  
**版本**: v0.5.0
