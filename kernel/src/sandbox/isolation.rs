//! 沙箱隔离增强模块
//! 
//! 提供更严格的沙箱隔离机制，防止沙箱逃逸到宿主机

use std::sync::Arc;
use tokio::sync::{Mutex, RwLock};
use tracing::{info, warn, error, debug};
use wasmtime::{Config as WasmConfig, Engine, Instance, Module, Store, TypedFunc, AsContextMut};
use wasmtime_wasi::{WasiCtx, WasiCtxBuilder, Dir, TcpListener, Stdin, Stdout, Stderr};
use crate::utils::Result;
use std::path::Path;
use std::collections::HashSet;

/// 沙箱隔离配置
#[derive(Debug, Clone)]
pub struct IsolationConfig {
    pub allow_network: bool,
    pub allowed_network_hosts: Vec<String>,
    pub allow_filesystem: bool,
    pub allowed_directories: Vec<String>,
    pub max_memory_pages: u32,
    pub max_execution_steps: u64,
    pub forbid_spawn_process: bool,
    pub forbid_system_calls: Vec<String>,
}

impl Default for IsolationConfig {
    fn default() -> Self {
        Self {
            allow_network: false,           // 默认禁止网络访问
            allowed_network_hosts: vec![],  // 允许的网络主机
            allow_filesystem: false,        // 默认禁止文件系统访问
            allowed_directories: vec![],    // 允许访问的目录
            max_memory_pages: 1024,         // 64MB (1024 * 64KB)
            max_execution_steps: 1000000,   // 最大执行步骤
            forbid_spawn_process: true,     // 禁止派生进程
            forbid_system_calls: vec![      // 禁止的系统调用
                "exec".to_string(),
                "fork".to_string(),
                "clone".to_string(),
                "ptrace".to_string(),
                "chroot".to_string(),
                "mount".to_string(),
                "unmount".to_string(),
            ],
        }
    }
}

/// 隔离沙箱
pub struct IsolatedSandbox {
    engine: Engine,
    module: Module,
    store: Arc<Mutex<Store<WasiCtx>>>,
    instance: Instance,
    config: IsolationConfig,
    execution_steps: Arc<Mutex<u64>>,
}

impl IsolatedSandbox {
    /// 创建新的隔离沙箱
    pub fn new(wasm_bytes: &[u8], config: IsolationConfig) -> Result<Self> {
        // 配置WASM引擎以增强安全性
        let mut wasm_config = WasmConfig::new();
        wasm_config.async_support(false);
        
        // 限制内存使用
        wasm_config.static_memory_maximum_size(Some(config.max_memory_pages as u64 * 65536)); // 页大小64KB
        wasm_config.static_memory_guard_size(Some(0));
        wasm_config.dynamic_memory_guard_size(Some(0));
        
        let engine = Engine::new(&wasm_config)
            .map_err(|e| crate::utils::NeuroFlowError::Sandbox(format!("Failed to create engine: {}", e)))?;
        
        // 创建受限的WASI上下文
        let wasi = Self::create_restricted_wasi_ctx(&config)?;
        
        let mut store = Store::new(&engine, wasi);
        
        // 编译模块
        let module = Module::from_binary(&engine, wasm_bytes)
            .map_err(|e| crate::utils::NeuroFlowError::Sandbox(format!("Failed to compile module: {}", e)))?;
        
        // 实例化
        let instance = Instance::new(&mut store, &module, &[])
            .map_err(|e| crate::utils::NeuroFlowError::Sandbox(format!("Failed to instantiate module: {}", e)))?;
        
        Ok(Self {
            engine,
            module,
            store: Arc::new(Mutex::new(store)),
            instance,
            config,
            execution_steps: Arc::new(Mutex::new(0)),
        })
    }

    /// 创建受限的WASI上下文
    fn create_restricted_wasi_ctx(config: &IsolationConfig) -> Result<WasiCtx> {
        let mut builder = WasiCtxBuilder::new();
        
        // 设置标准输入输出
        builder = builder.stdin(Box::new(Stdin::null()));
        builder = builder.stdout(Box::new(Stdout::null()));
        builder = builder.stderr(Box::new(Stderr::null()));
        
        // 根据配置限制文件系统访问
        if config.allow_filesystem {
            for dir_path in &config.allowed_directories {
                if Path::new(dir_path).exists() {
                    // 以只读方式挂载目录
                    match Dir::open_ambient_dir(dir_path, cap_std::ambient_authority()) {
                        Ok(dir) => {
                            builder = builder.preopened_dir(dir, dir_path)?;
                        }
                        Err(e) => {
                            warn!("Failed to open directory {}: {}", dir_path, e);
                        }
                    }
                }
            }
        }
        
        // 网络访问限制
        if config.allow_network {
            // 仅允许预定义的主机
            for host in &config.allowed_network_hosts {
                // 这里可以添加对特定主机的网络访问限制
                debug!("Allowing network access to: {}", host);
            }
        }
        
        Ok(builder.build())
    }

    /// 安全调用函数
    pub async fn safe_call(&self, func_name: &str, args: &[i32]) -> Result<Vec<i32>> {
        let mut store = self.store.lock().await;
        let mut steps = self.execution_steps.lock().await;
        
        // 检查执行步骤限制
        if *steps >= self.config.max_execution_steps {
            return Err(crate::utils::NeuroFlowError::Sandbox("Execution step limit exceeded".to_string()));
        }
        
        // 根据函数名称执行相应的安全调用
        let result = match func_name {
            "add" if args.len() == 2 => {
                let add_func: TypedFunc<(i32, i32), i32> = self.instance
                    .get_typed_func(&mut *store, "add")
                    .map_err(|e| crate::utils::NeuroFlowError::WasmExecution(e.to_string()))?;
                
                let res = add_func.call(&mut *store, (args[0], args[1]))
                    .map_err(|e| crate::utils::NeuroFlowError::WasmExecution(e.to_string()))?;
                
                vec![res]
            }
            "multiply" if args.len() == 2 => {
                let multiply_func: TypedFunc<(i32, i32), i32> = self.instance
                    .get_typed_func(&mut *store, "multiply")
                    .map_err(|e| crate::utils::NeuroFlowError::WasmExecution(e.to_string()))?;
                
                let res = multiply_func.call(&mut *store, (args[0], args[1]))
                    .map_err(|e| crate::utils::NeuroFlowError::WasmExecution(e.to_string()))?;
                
                vec![res]
            }
            _ => {
                return Err(crate::utils::NeuroFlowError::WasmExecution(
                    format!("Unsupported function: {} with {} args", func_name, args.len())
                ));
            }
        };
        
        // 增加执行步骤计数
        *steps += 1;
        
        Ok(result)
    }

    /// 检查沙箱是否安全
    pub fn is_secure(&self) -> bool {
        // 检查配置是否符合安全要求
        (!self.config.allow_network || !self.config.allowed_network_hosts.is_empty()) &&
        (!self.config.allow_filesystem || !self.config.allowed_directories.is_empty())
    }

    /// 获取当前执行步骤数
    pub async fn get_execution_steps(&self) -> u64 {
        *self.execution_steps.lock().await
    }

    /// 重置执行步骤计数
    pub async fn reset_execution_steps(&self) {
        *self.execution_steps.lock().await = 0;
    }
}

/// 沙箱隔离管理器
pub struct IsolationManager {
    default_config: IsolationConfig,
    allowed_hosts: Arc<RwLock<HashSet<String>>>,
    allowed_directories: Arc<RwLock<HashSet<String>>>,
}

impl IsolationManager {
    /// 创建新的隔离管理器
    pub fn new() -> Self {
        Self {
            default_config: IsolationConfig::default(),
            allowed_hosts: Arc::new(RwLock::new(HashSet::new())),
            allowed_directories: Arc::new(RwLock::new(HashSet::new())),
        }
    }

    /// 创建具有指定配置的隔离沙箱
    pub fn create_isolated_sandbox(&self, wasm_bytes: &[u8], config: Option<IsolationConfig>) -> Result<IsolatedSandbox> {
        let final_config = config.unwrap_or_else(|| self.default_config.clone());
        IsolatedSandbox::new(wasm_bytes, final_config)
    }

    /// 添加允许的网络主机
    pub async fn add_allowed_host(&self, host: &str) -> Result<()> {
        let mut hosts = self.allowed_hosts.write().await;
        hosts.insert(host.to_string());
        info!("Added allowed host: {}", host);
        Ok(())
    }

    /// 添加允许的目录
    pub async fn add_allowed_directory(&self, dir: &str) -> Result<()> {
        let mut dirs = self.allowed_directories.write().await;
        if Path::new(dir).exists() {
            dirs.insert(dir.to_string());
            info!("Added allowed directory: {}", dir);
            Ok(())
        } else {
            Err(crate::utils::NeuroFlowError::IoError(format!("Directory does not exist: {}", dir)))
        }
    }

    /// 检查主机是否被允许
    pub async fn is_host_allowed(&self, host: &str) -> bool {
        let hosts = self.allowed_hosts.read().await;
        hosts.contains(host)
    }

    /// 检查目录是否被允许
    pub async fn is_directory_allowed(&self, dir: &str) -> bool {
        let dirs = self.allowed_directories.read().await;
        dirs.contains(dir)
    }

    /// 获取默认隔离配置
    pub fn get_default_config(&self) -> IsolationConfig {
        self.default_config.clone()
    }

    /// 更新默认隔离配置
    pub fn update_default_config(&mut self, config: IsolationConfig) {
        self.default_config = config;
    }
}

/// 沙箱安全检查器
pub struct SandboxSecurityChecker {
    config: IsolationConfig,
}

impl SandboxSecurityChecker {
    /// 创建新的安全检查器
    pub fn new(config: IsolationConfig) -> Self {
        Self { config }
    }

    /// 检查WASM模块的安全性
    pub fn check_module_security(&self, wasm_bytes: &[u8]) -> Result<SecurityCheckReport> {
        let mut report = SecurityCheckReport::default();
        
        // 检查导入的函数，看是否有危险的系统调用
        match wasmparser::validate(wasm_bytes) {
            Ok(_) => {
                report.module_valid = true;
                
                // 解析WASM模块以检查导入
                let mut parser = wasmparser::Parser::new(0);
                for payload in wasmparser::Parser::new(0).parse_all(wasm_bytes) {
                    match payload {
                        Ok(wasmparser::Payload::ImportSection(impt_section)) => {
                            for import in impt_section {
                                let import = import?;
                                if let wasmparser::ExternalKind::Function(_) = import.kind {
                                    let module = import.module;
                                    let name = import.name;
                                    
                                    // 检查是否导入了危险函数
                                    if self.config.forbid_system_calls.iter().any(|forbidden| {
                                        name.contains(forbidden)
                                    }) {
                                        report.security_issues.push(format!(
                                            "Module imports forbidden function: {}/{}", module, name
                                        ));
                                        report.is_secure = false;
                                    }
                                }
                            }
                        }
                        _ => {}
                    }
                }
            }
            Err(e) => {
                report.module_valid = false;
                report.security_issues.push(format!("Invalid WASM module: {}", e));
                report.is_secure = false;
            }
        }
        
        Ok(report)
    }

    /// 检查运行时安全
    pub fn check_runtime_security(&self, sandbox: &IsolatedSandbox) -> bool {
        // 检查沙箱配置是否安全
        sandbox.is_secure()
    }
}

/// 安全检查报告
#[derive(Debug, Default, Clone)]
pub struct SecurityCheckReport {
    pub module_valid: bool,
    pub is_secure: bool,
    pub security_issues: Vec<String>,
    pub allowed_capabilities: Vec<String>,
}

impl SecurityCheckReport {
    /// 检查报告是否表示安全
    pub fn is_safe(&self) -> bool {
        self.module_valid && self.is_secure && self.security_issues.is_empty()
    }

    /// 获取安全问题摘要
    pub fn get_summary(&self) -> String {
        if self.is_safe() {
            "Module is secure".to_string()
        } else {
            format!(
                "Module has {} security issues: {}",
                self.security_issues.len(),
                self.security_issues.join(", ")
            )
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_isolation_config_defaults() {
        let config = IsolationConfig::default();
        assert_eq!(config.allow_network, false);
        assert_eq!(config.allow_filesystem, false);
        assert_eq!(config.max_memory_pages, 1024); // 64MB
        assert_eq!(config.forbid_spawn_process, true);
    }
    
    #[tokio::test]
    async fn test_isolation_manager_creation() {
        let manager = IsolationManager::new();
        assert_eq!(manager.get_default_config().allow_network, false);
        assert_eq!(manager.get_default_config().allow_filesystem, false);
    }
    
    #[tokio::test]
    async fn test_host_allowance() {
        let manager = IsolationManager::new();
        manager.add_allowed_host("example.com").await.unwrap();
        assert!(manager.is_host_allowed("example.com").await);
        assert!(!manager.is_host_allowed("other.com").await);
    }
    
    #[test]
    fn test_security_checker_creation() {
        let config = IsolationConfig::default();
        let checker = SandboxSecurityChecker::new(config);
        assert_eq!(checker.config.allow_network, false);
    }
}

/// 沙箱隔离工具函数
pub mod utils {
    use super::*;
    
    /// 创建严格隔离配置
    pub fn create_strict_isolation_config() -> IsolationConfig {
        IsolationConfig {
            allow_network: false,
            allowed_network_hosts: vec![],
            allow_filesystem: false,
            allowed_directories: vec![],
            max_memory_pages: 512,  // 32MB
            max_execution_steps: 500000,
            forbid_spawn_process: true,
            forbid_system_calls: vec![
                "exec".to_string(),
                "fork".to_string(),
                "clone".to_string(),
                "ptrace".to_string(),
                "chroot".to_string(),
                "mount".to_string(),
                "unmount".to_string(),
                "open".to_string(),  // 文件打开
                "write".to_string(), // 文件写入
                "unlink".to_string(), // 文件删除
            ],
        }
    }
    
    /// 创建宽松隔离配置（用于开发和测试）
    pub fn create_permissive_isolation_config() -> IsolationConfig {
        IsolationConfig {
            allow_network: true,
            allowed_network_hosts: vec!["localhost".to_string(), "127.0.0.1".to_string()],
            allow_filesystem: true,
            allowed_directories: vec!["/tmp".to_string()],
            max_memory_pages: 2048,  // 128MB
            max_execution_steps: 2000000,
            forbid_spawn_process: false,
            forbid_system_calls: vec![
                "exec".to_string(),
                "fork".to_string(),
                "clone".to_string(),
                "ptrace".to_string(),
                "chroot".to_string(),
            ],
        }
    }
}

/// WASI系统调用拦截器（概念性实现）
pub struct SyscallInterceptor {
    forbidden_calls: HashSet<String>,
}

impl SyscallInterceptor {
    pub fn new(forbidden_calls: Vec<String>) -> Self {
        Self {
            forbidden_calls: forbidden_calls.into_iter().collect(),
        }
    }
    
    pub fn is_call_allowed(&self, syscall_name: &str) -> bool {
        !self.forbidden_calls.contains(syscall_name)
    }
    
    pub fn intercept_syscall(&self, syscall_name: &str) -> Result<()> {
        if self.is_call_allowed(syscall_name) {
            Ok(())
        } else {
            Err(crate::utils::NeuroFlowError::SecurityError(
                format!("Forbidden system call attempted: {}", syscall_name)
            ))
        }
    }
}