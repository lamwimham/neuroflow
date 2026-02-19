# 沙箱使用指南

**版本**: v0.5.0  
**状态**: ✅ 生产就绪

本指南介绍如何在 NeuroFlow 中使用三种沙箱隔离方案。

---

## 🚀 快速开始

### 安装依赖

```bash
# Python SDK 已包含沙箱支持
pip install neuroflow-sdk

# Linux Namespace 需要额外依赖（仅 Linux）
pip install nix  # 或通过系统包管理器
```

### 选择沙箱类型

```python
from neuroflow.sandbox import (
    SandboxIsolator,      # Python 进程沙箱
    NamespaceIsolator,    # Linux Namespace 沙箱
    WasmSandbox,          # WASM 沙箱
)

# 根据需求选择
if platform == "linux" and need_strong_isolation:
    sandbox = NamespaceIsolator(config)
elif need_cross_platform or untrusted_code:
    sandbox = WasmSandbox(config)
else:
    sandbox = SandboxIsolator(config)
```

---

## 📦 Python 进程沙箱

### 基础使用

```python
from neuroflow.sandbox import SandboxIsolator, SandboxConfig

# 1. 配置
config = SandboxConfig(
    work_dir="/tmp/sandbox",
    cpu_time_limit=30,
    memory_limit=256 * 1024 * 1024,
)

# 2. 创建沙箱
isolator = SandboxIsolator(config)

# 3. 执行代码
result = await isolator.execute(
    "python3",
    ["-c", "print('Hello from sandbox!')"]
)

# 4. 检查结果
if result.success:
    print(f"输出：{result.stdout.decode()}")
    print(f"时间：{result.execution_time_ms}ms")
else:
    print(f"错误：{result.error}")
```

### 安全级别配置

```python
from neuroflow.sandbox import SandboxSecurityLevel

# 级别 1: 最小隔离（可信代码）
config = SandboxConfig(
    security_level=SandboxSecurityLevel.MINIMAL,
)

# 级别 2: 标准隔离（默认）
config = SandboxConfig(
    security_level=SandboxSecurityLevel.STANDARD,
)

# 级别 3: 严格隔离（半可信代码）
config = SandboxConfig(
    security_level=SandboxSecurityLevel.STRICT,
    enable_seccomp=True,
)

# 级别 4: 极端隔离（不可信代码）
config = SandboxConfig(
    security_level=SandboxSecurityLevel.PARANOID,
    enable_network=False,
    allowed_commands=["python3"],
)
```

### 命令白名单

```python
config = SandboxConfig(
    security_level=SandboxSecurityLevel.STRICT,
    allowed_commands=[
        "python3",
        "pip",
        "ls",
        "cat",
    ],
)

# 尝试执行未授权的命令会失败
result = await isolator.execute("rm", ["-rf", "/"])
# 返回错误：Command 'rm' not in allowed list
```

---

## 🔒 Linux Namespace 沙箱

### 基础使用

```python
from neuroflow.sandbox import NamespaceIsolator, SandboxConfig

# 1. 配置
config = SandboxConfig(
    work_dir="/tmp/sandbox",
    cpu_time_limit=30,
    memory_limit=256 * 1024 * 1024,
    file_size_limit=10 * 1024 * 1024,
    enable_network=False,  # 禁用网络
    enable_seccomp=True,   # 启用系统调用过滤
)

# 2. 创建沙箱
isolator = NamespaceIsolator(config)

# 3. 执行
result = isolator.execute("python3", ["script.py"])

print(f"退出码：{result.exit_code}")
print(f"时间：{result.execution_time_ms}ms")
```

### 网络访问控制

```python
# 完全禁用网络
config = SandboxConfig(
    enable_network=False,
)

# 或允许特定主机
config = SandboxConfig(
    enable_network=True,
    allowed_hosts=[
        "api.trusted.com",
        "localhost",
    ],
)
```

### 系统调用过滤

```python
# 自定义 seccomp 配置
config = SandboxConfig(
    enable_seccomp=True,
    seccomp_profile={
        "defaultAction": "SCMP_ACT_ERRNO",
        "syscalls": [
            {
                "names": ["read", "write", "open", "close"],
                "action": "SCMP_ACT_ALLOW",
            },
            {
                "names": ["ptrace", "mount", "reboot"],
                "action": "SCMP_ACT_ERRNO",  # 禁止
            },
        ],
    },
)
```

### 权限要求

Linux Namespace 需要特殊权限：

```bash
# 方式 1: 使用 sudo
sudo python script.py

# 方式 2: 设置 capability
sudo setcap cap_sys_admin+ep /usr/bin/python3

# 方式 3: 启用 user namespace（推荐）
echo 0 | sudo tee /proc/sys/kernel/unprivileged_userns_clone
```

---

## 🧩 WASM 沙箱

### 基础使用

```python
from neuroflow.sandbox import WasmSandbox, WasmSandboxConfig

# 1. 配置
config = WasmSandboxConfig(
    max_memory_bytes=64 * 1024 * 1024,  # 64MB
    timeout_seconds=30,
    max_fuel=1_000_000,  # 100 万指令
)

# 2. 创建沙箱
async with WasmSandbox(config) as sandbox:
    # 3. 加载 WASM 模块
    with open("module.wasm", "rb") as f:
        wasm_bytes = f.read()
    
    # 4. 执行
    result = await sandbox.execute(wasm_bytes)
    
    print(f"成功：{result.success}")
    print(f"时间：{result.execution_time_ms}ms")
    print(f"燃料：{result.fuel_consumed}")
```

### 编译 Rust 为 WASM

```bash
# 安装目标
rustup target add wasm32-unknown-unknown

# 编译
cargo build --target wasm32-unknown-unknown --release

# 输出文件
# target/wasm32-unknown-unknown/release/your_project.wasm
```

### 编译 AssemblyScript 为 WASM

```bash
# 安装 AssemblyScript
npm install -g assemblyscript

# 编译
asc assembly/index.ts --target release --outFile build/release.wasm
```

### 导入控制

```python
# 只允许特定导入
config = WasmSandboxConfig(
    allowed_imports=[
        "env.log",      # 日志函数
        "env.alloc",    # 内存分配
    ],
)

# 尝试使用未授权的导入会失败
# Error: Import not allowed: env.system
```

---

## 🎯 场景示例

### 场景 1: 执行第三方插件

```python
from neuroflow.sandbox import SandboxExecutor, WasmSandboxConfig

# 不可信代码 → WASM 沙箱
config = WasmSandboxConfig(
    max_memory_bytes=128 * 1024 * 1024,
    timeout_seconds=10,
    max_fuel=5_000_000,
)

executor = await SandboxExecutor.new_wasm(config)

# 执行插件
with open("plugin.wasm", "rb") as f:
    result = await executor.execute_wasm(f.read())

if result.success:
    print("插件执行成功")
else:
    print(f"插件执行失败：{result.error}")
```

### 场景 2: 运行用户代码

```python
from neuroflow.sandbox import NamespaceIsolator, SandboxConfig

# 半可信代码 → Namespace 沙箱
config = SandboxConfig(
    work_dir="/tmp/user-code",
    cpu_time_limit=30,
    memory_limit=256 * 1024 * 1024,
    enable_network=False,  # 禁用网络
    enable_seccomp=True,   # 过滤系统调用
)

isolator = NamespaceIsolator(config)

# 执行用户代码
result = isolator.execute("python3", ["user_script.py"])

if result.exit_code == 0:
    print("代码执行成功")
else:
    print(f"代码执行失败：退出码 {result.exit_code}")
```

### 场景 3: 沙箱管理器

```python
from neuroflow.sandbox import SandboxManager

manager = SandboxManager()

# 批量执行
tasks = [
    ("task1", "python3 -c 'print(1)'"),
    ("task2", "python3 -c 'print(2)'"),
    ("task3", "python3 -c 'print(3)'"),
]

# 并发执行
results = await asyncio.gather(*[
    manager.execute(cmd) for _, cmd in tasks
])

# 检查结果
for (task_name, _), result in zip(tasks, results):
    print(f"{task_name}: {'✓' if result.success else '✗'}")

# 清理
await manager.cleanup()
```

---

## ⚠️ 故障排除

### 问题 1: Namespace 权限不足

**错误**: `Namespace creation failed: Operation not permitted`

**解决**:

```bash
# 检查权限
cat /proc/sys/kernel/unprivileged_userns_clone

# 启用 user namespace
echo 0 | sudo tee /proc/sys/kernel/unprivileged_userns_clone
```

### 问题 2: WASM 编译失败

**错误**: `WASM compilation failed`

**解决**:

```bash
# 验证 WASM 文件
wasm-validate module.wasm

# 检查 WASM 版本
wasm2wat module.wasm | head -5
```

### 问题 3: 超时执行

**错误**: `Execution timeout after 30s`

**解决**:

```python
# 增加超时时间
config = SandboxConfig(
    cpu_time_limit=60,  # 增加到 60 秒
)

# 或优化代码性能
```

---

## 📚 相关文档

- [沙箱概念](../concepts/sandbox.md)
- [Namespace 集成](namespace-sandbox.md)
- [WASM 指南](wasm-sandbox.md)
- [安全最佳实践](../best-practices/security.md)

---

**最后更新**: 2026-03-20  
**版本**: v0.5.0
