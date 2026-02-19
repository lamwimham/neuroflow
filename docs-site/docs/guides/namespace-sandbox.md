# Linux Namespace 沙箱集成指南

**版本**: v0.5.0  
**状态**: ✅ 生产就绪

本指南介绍如何在 NeuroFlow 中集成和使用 Linux Namespace 沙箱隔离。

---

## 🎯 概述

Linux Namespace 提供强大的系统级隔离，包括：

- ✅ PID Namespace - 进程隔离
- ✅ Mount Namespace - 文件系统隔离
- ✅ Network Namespace - 网络隔离
- ✅ UTS Namespace - 主机名隔离
- ✅ IPC Namespace - IPC 隔离
- ✅ cgroups v2 - 资源限制

---

## 🔧 安装和配置

### 系统要求

- **Linux Kernel**: 4.0+ (推荐 5.0+)
- **权限**: 需要 `CAP_SYS_ADMIN` 或启用 user namespace

### 启用 User Namespace

```bash
# 检查是否启用
cat /proc/sys/kernel/unprivileged_userns_clone

# 启用（如果需要）
echo 0 | sudo tee /proc/sys/kernel/unprivileged_userns_clone
```

### 安装依赖

```bash
# Rust 项目会自动安装 nix crate
# kernel/Cargo.toml 已包含：
# nix = { version = "0.27", features = ["sched", "mount", "user"] }
```

---

## 💻 使用方式

### Rust 内核集成

```rust
use kernel::sandbox::{NamespaceIsolator, SandboxConfig};

// 1. 配置沙箱
let config = SandboxConfig {
    work_dir: "/tmp/sandbox".to_string(),
    cpu_time_limit: Some(30),
    memory_limit: Some(256 * 1024 * 1024),
    file_size_limit: Some(10 * 1024 * 1024),
    enable_network: false,  // 禁用网络
    enable_seccomp: true,   // 启用系统调用过滤
};

// 2. 创建隔离器
let mut isolator = NamespaceIsolator::new(config);

// 3. 执行命令
let result = isolator.execute("python3", &["script.py"])?;

println!("退出码：{}", result.exit_code);
println!("执行时间：{}ms", result.execution_time_ms);
```

### Python SDK 调用

```python
from neuroflow.sandbox import NamespaceIsolator, SandboxConfig

# 配置
config = SandboxConfig(
    work_dir="/tmp/sandbox",
    cpu_time_limit=30,
    memory_limit=256 * 1024 * 1024,
    enable_network=False,
    enable_seccomp=True,
)

# 创建沙箱
isolator = NamespaceIsolator(config)

# 执行
result = await isolator.execute("python3", ["script.py"])

if result.success:
    print(f"输出：{result.stdout.decode()}")
else:
    print(f"错误：{result.error}")
```

---

## 🔒 安全配置

### 1. 网络访问控制

```rust
// 完全禁用网络
let config = SandboxConfig {
    enable_network: false,
    ..Default::default()
};

// 或允许特定主机
let config = SandboxConfig {
    enable_network: true,
    allowed_hosts: vec![
        "api.trusted.com".to_string(),
        "localhost".to_string(),
    ],
    ..Default::default()
};
```

### 2. 系统调用过滤

```rust
// 自定义 seccomp 配置
let config = SandboxConfig {
    enable_seccomp: true,
    seccomp_profile: Some(SeccompProfile {
        default_action: ScmpAction::Errno(1),
        rules: vec![
            // 允许的系统调用
            ScmpRule::new(ScmpSyscall::read, ScmpAction::Allow),
            ScmpRule::new(ScmpSyscall::write, ScmpAction::Allow),
            ScmpRule::new(ScmpSyscall::open, ScmpAction::Allow),
            ScmpRule::new(ScmpSyscall::close, ScmpAction::Allow),
            
            // 禁止的系统调用
            ScmpRule::new(ScmpSyscall::ptrace, ScmpAction::Errno(1)),
            ScmpRule::new(ScmpSyscall::mount, ScmpAction::Errno(1)),
            ScmpRule::new(ScmpSyscall::reboot, ScmpAction::Errno(1)),
        ],
    }),
    ..Default::default()
};
```

### 3. 资源限制

```rust
use kernel::sandbox::CgroupConfig;

let cgroup_config = CgroupConfig {
    cpu_quota: Some(0.5),  // 50% CPU
    memory_limit: Some(256 * 1024 * 1024),  // 256MB
    pids_limit: Some(10),  // 最多 10 个进程
};

let config = SandboxConfig {
    cgroup: Some(cgroup_config),
    ..Default::default()
};
```

---

## 🧪 测试

### 单元测试

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_namespace_isolation() {
        let config = SandboxConfig::default();
        let mut isolator = NamespaceIsolator::new(config);
        
        let result = isolator.execute("echo", &["test"]).unwrap();
        
        assert_eq!(result.exit_code, 0);
        assert!(result.execution_time_ms < 1000);
    }

    #[test]
    fn test_resource_limits() {
        let config = SandboxConfig {
            memory_limit: Some(64 * 1024 * 1024),  // 64MB
            ..Default::default()
        };
        
        let mut isolator = NamespaceIsolator::new(config);
        
        // 尝试分配大量内存应该会失败
        let result = isolator.execute("python3", &["-c", "x = b'0' * 100000000"]);
        
        // 应该因为内存限制而失败
        assert!(result.is_err() || result.unwrap().exit_code != 0);
    }
}
```

### 集成测试

```bash
# 运行测试
cd kernel
cargo test --package kernel --lib sandbox::namespace
```

---

## ⚠️ 故障排除

### 问题 1: 权限不足

**错误**: `Namespace creation failed: Operation not permitted`

**解决**:

```bash
# 检查当前权限
capsh --print

# 添加 CAP_SYS_ADMIN 权限
sudo setcap cap_sys_admin+ep /path/to/binary

# 或启用 user namespace
echo 0 | sudo tee /proc/sys/kernel/unprivileged_userns_clone
```

### 问题 2: cgroups 不可用

**错误**: `cgroups setup failed: No such file or directory`

**解决**:

```bash
# 检查 cgroups v2 是否挂载
mount | grep cgroup

# 如果没有，手动挂载
sudo mount -t cgroup2 none /sys/fs/cgroup

# 或在内核启动参数中添加
# systemd.unified_cgroup_hierarchy=1
```

### 问题 3: seccomp 失败

**错误**: `seccomp setup failed: Invalid argument`

**解决**:

```bash
# 检查内核是否支持 seccomp
zgrep CONFIG_SECCOMP /proc/config.gz

# 应该是 y
# CONFIG_SECCOMP=y
```

---

## 📊 性能基准

### 启动时间

```
Namespace 沙箱：~100ms
Python 进程：    ~80ms
WASM:          ~10ms
```

### 内存占用

```
Namespace 沙箱：~20MB 基础
Python 进程：  ~15MB 基础
WASM:        ~5MB 基础
```

### 执行开销

```
原生执行：100ms (基准)
Namespace:  110ms (+10%)
Python:    120ms (+20%)
WASM:      105ms (+5%)
```

---

## 📚 相关文档

- [沙箱概念](../concepts/sandbox.md)
- [沙箱使用指南](sandbox-usage.md)
- [WASM 沙箱](wasm-sandbox.md)
- [安全最佳实践](../best-practices/security.md)

---

**最后更新**: 2026-03-20  
**版本**: v0.5.0
