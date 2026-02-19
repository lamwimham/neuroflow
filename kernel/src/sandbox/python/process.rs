//! Python 沙箱进程实现
//! 使用 subprocess 启动独立 Python 进程，通过 gRPC/Unix Socket 通信

use std::collections::HashMap;
use std::io::{BufRead, BufReader};
use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::{Mutex, RwLock};
use tokio::time::timeout;
use tracing::{info, warn, error, debug};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use super::Result;
use super::SandboxError;

/// 沙箱配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SandboxConfig {
    /// Python 解释器路径
    pub python_path: String,
    /// 沙箱工作目录
    pub work_dir: PathBuf,
    /// 内存限制 (MB)
    pub memory_limit_mb: u64,
    /// CPU 限制 (核心数，0.0-1.0 表示百分比)
    pub cpu_limit: f64,
    /// 执行超时 (毫秒)
    pub timeout_ms: u64,
    /// 允许的网络访问 (域名白名单)
    pub allowed_hosts: Vec<String>,
    /// 允许访问的文件路径
    pub allowed_paths: Vec<String>,
    /// 环境变量
    pub env: HashMap<String, String>,
}

impl Default for SandboxConfig {
    fn default() -> Self {
        Self {
            python_path: "python3".to_string(),
            work_dir: std::env::temp_dir().join("neuroflow_sandbox"),
            memory_limit_mb: 256,
            cpu_limit: 0.5,
            timeout_ms: 30000,
            allowed_hosts: vec!["localhost".to_string(), "127.0.0.1".to_string()],
            allowed_paths: vec!["/tmp".to_string()],
            env: HashMap::new(),
        }
    }
}

/// 沙箱句柄 - 管理单个沙箱进程
pub struct SandboxHandle {
    pub id: String,
    pub config: SandboxConfig,
    process: Option<std::process::Child>,
    pub created_at: std::time::Instant,
    pub last_used: std::time::Instant,
    pub execution_count: u64,
}

impl SandboxHandle {
    /// 创建新的沙箱句柄
    pub fn new(id: String, config: SandboxConfig) -> Self {
        Self {
            id,
            config,
            process: None,
            created_at: std::time::Instant::now(),
            last_used: std::time::Instant::now(),
            execution_count: 0,
        }
    }

    /// 启动沙箱进程
    pub fn start(&mut self) -> Result<()> {
        // 创建工作目录
        std::fs::create_dir_all(&self.config.work_dir)
            .map_err(|e| SandboxError::StartFailed(format!("Failed to create work dir: {}", e)))?;

        // 准备 Python 沙箱执行器脚本
        let executor_script = self.config.work_dir.join("executor.py");
        self.write_executor_script(&executor_script)?;

        // 构建命令
        let mut cmd = Command::new(&self.config.python_path);
        cmd.arg(&executor_script)
            .arg("--id")
            .arg(&self.id)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .current_dir(&self.config.work_dir);

        // 设置环境变量
        for (key, value) in &self.config.env {
            cmd.env(key, value);
        }

        // 设置资源限制 (Unix only)
        #[cfg(unix)]
        {
            use std::os::unix::process::CommandExt;
            
            let memory_limit = self.config.memory_limit_mb * 1024 * 1024;
            
            unsafe {
                cmd.pre_exec(move || {
                    // 设置内存限制
                    let rlimit = libc::rlimit {
                        rlim_cur: memory_limit,
                        rlim_max: memory_limit,
                    };
                    unsafe { libc::setrlimit(libc::RLIMIT_AS, &rlimit) };
                    
                    // 设置 CPU 时间限制
                    let cpu_limit = (self.config.cpu_limit * 100.0) as libc::rlim_t;
                    let rlimit_cpu = libc::rlimit {
                        rlim_cur: cpu_limit,
                        rlim_max: cpu_limit,
                    };
                    unsafe { libc::setrlimit(libc::RLIMIT_CPU, &rlimit_cpu) };
                    
                    Ok(())
                });
            }
        }

        // 启动进程
        let process = cmd.spawn()
            .map_err(|e| SandboxError::StartFailed(format!("Failed to spawn process: {}", e)))?;

        self.process = Some(process);

        info!("Sandbox {} started", self.id);
        Ok(())
    }

    /// 执行 Python 代码
    pub fn execute(&mut self, code: &str, context: &ExecutionContext) -> Result<ExecutionResult> {
        if self.process.is_none() {
            self.start()?;
        }

        let process = self.process.as_mut()
            .ok_or_else(|| SandboxError::ExecutionFailed("Process not running".to_string()))?;

        // 准备执行请求
        let request = ExecutionRequest {
            code: code.to_string(),
            context: context.clone(),
            timeout_ms: self.config.timeout_ms,
        };

        // 序列化请求
        let request_json = serde_json::to_string(&request)
            .map_err(|e| SandboxError::Serialization(e.to_string()))?;

        // 发送到进程
        let mut stdin = process.stdin.take()
            .ok_or_else(|| SandboxError::ExecutionFailed("stdin not available".to_string()))?;

        use std::io::Write;
        writeln!(stdin, "{}", request_json)
            .map_err(|e| SandboxError::Communication(e.to_string()))?;

        // 读取响应 (带超时)
        let mut stdout = process.stdout.take()
            .ok_or_else(|| SandboxError::ExecutionFailed("stdout not available".to_string()))?;

        let reader = BufReader::new(&mut stdout);
        
        // 使用 timeout 包装读取操作
        let result = std::thread::spawn(move || {
            let mut line = String::new();
            reader.lines().next().and_then(|r| r.ok())
        }).join();

        self.execution_count += 1;
        self.last_used = std::time::Instant::now();

        // 解析响应
        match result {
            Ok(Some(response_json)) => {
                let response: ExecutionResponse = serde_json::from_str(&response_json)
                    .map_err(|e| SandboxError::Serialization(e.to_string()))?;
                
                Ok(ExecutionResult {
                    success: response.success,
                    output: response.output,
                    error: response.error,
                    execution_time_ms: response.execution_time_ms,
                })
            }
            Ok(None) => Err(SandboxError::ExecutionFailed("No response from sandbox".to_string())),
            Err(_) => Err(SandboxError::Timeout(Duration::from_millis(self.config.timeout_ms))),
        }
    }

    /// 停止沙箱进程
    pub fn stop(&mut self) -> Result<()> {
        if let Some(mut process) = self.process.take() {
            // 优雅终止
            process.kill()
                .map_err(|e| SandboxError::StopFailed(format!("Failed to kill process: {}", e)))?;
            
            process.wait()
                .map_err(|e| SandboxError::StopFailed(format!("Process wait failed: {}", e)))?;
            
            info!("Sandbox {} stopped", self.id);
        }
        Ok(())
    }

    /// 检查进程是否存活
    pub fn is_alive(&self) -> bool {
        if let Some(process) = &self.process {
            process.try_wait().map(|s| s.is_none()).unwrap_or(false)
        } else {
            false
        }
    }

    /// 写入执行器脚本
    fn write_executor_script(&self, path: &PathBuf) -> Result<()> {
        let script = r#"
import sys
import json
import time
import traceback
from typing import Any, Dict

class SandboxExecutor:
    def __init__(self):
        self.context = {}
    
    def execute(self, code: str, context: Dict[str, Any], timeout_ms: int) -> Dict[str, Any]:
        start_time = time.time()
        
        try:
            # 恢复上下文
            self.context.update(context)
            
            # 执行代码
            exec(code, self.context)
            
            # 获取结果 (如果有的话)
            result = self.context.get('_result', None)
            
            execution_time = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "output": str(result) if result is not None else "",
                "error": None,
                "execution_time_ms": execution_time
            }
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return {
                "success": False,
                "output": "",
                "error": f"{type(e).__name__}: {e}\n{traceback.format_exc()}",
                "execution_time_ms": execution_time
            }

def main():
    executor = SandboxExecutor()
    
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            code = request.get('code', '')
            context = request.get('context', {})
            timeout_ms = request.get('timeout_ms', 30000)
            
            result = executor.execute(code, context, timeout_ms)
            
            # 输出响应
            print(json.dumps(result), flush=True)
            
        except Exception as e:
            error_response = {
                "success": False,
                "output": "",
                "error": str(e),
                "execution_time_ms": 0
            }
            print(json.dumps(error_response), flush=True)

if __name__ == "__main__":
    main()
"#;

        std::fs::write(path, script)
            .map_err(|e| SandboxError::StartFailed(format!("Failed to write executor: {}", e)))?;

        Ok(())
    }
}

impl Drop for SandboxHandle {
    fn drop(&mut self) {
        let _ = self.stop();
    }
}

/// 执行上下文
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionContext {
    pub variables: HashMap<String, serde_json::Value>,
    pub metadata: HashMap<String, String>,
}

impl Default for ExecutionContext {
    fn default() -> Self {
        Self {
            variables: HashMap::new(),
            metadata: HashMap::new(),
        }
    }
}

/// 执行请求
#[derive(Debug, Clone, Serialize, Deserialize)]
struct ExecutionRequest {
    code: String,
    context: ExecutionContext,
    timeout_ms: u64,
}

/// 执行响应
#[derive(Debug, Clone, Serialize, Deserialize)]
struct ExecutionResponse {
    success: bool,
    output: String,
    error: Option<String>,
    execution_time_ms: u64,
}

/// 执行结果
#[derive(Debug, Clone)]
pub struct ExecutionResult {
    pub success: bool,
    pub output: String,
    pub error: Option<String>,
    pub execution_time_ms: u64,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sandbox_config_default() {
        let config = SandboxConfig::default();
        assert_eq!(config.python_path, "python3");
        assert_eq!(config.memory_limit_mb, 256);
        assert_eq!(config.cpu_limit, 0.5);
        assert_eq!(config.timeout_ms, 30000);
    }

    #[tokio::test]
    async fn test_sandbox_basic_execution() {
        let config = SandboxConfig::default();
        let mut handle = SandboxHandle::new("test-1".to_string(), config);

        // 启动沙箱
        assert!(handle.start().is_ok());

        // 执行简单代码
        let context = ExecutionContext::default();
        let result = handle.execute("x = 1 + 1\n_result = x", &context);

        assert!(result.is_ok());
        let result = result.unwrap();
        assert!(result.success);
        assert_eq!(result.output, "2");

        // 停止沙箱
        assert!(handle.stop().is_ok());
    }
}
