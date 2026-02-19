use crate::{
    sandbox::{SandboxConfig, WasmSandbox},
    utils::{NeuroFlowError, Result},
};
use std::{
    collections::HashMap,
    sync::{Arc, Mutex},
};
use tracing::{debug, error, info};

#[derive(Debug, Clone)]
pub struct SandboxInstance {
    pub id: String,
    pub agent_id: String,
    pub config: SandboxConfig,
}

pub struct SandboxManager {
    sandboxes: Arc<Mutex<HashMap<String, SandboxInstance>>>,
    wasm_bytes_cache: Arc<Mutex<HashMap<String, Vec<u8>>>>,
}

impl SandboxManager {
    pub fn new() -> Self {
        Self {
            sandboxes: Arc::new(Mutex::new(HashMap::new())),
            wasm_bytes_cache: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    pub fn spawn_sandbox(&self, agent_id: &str, wasm_bytes: &[u8], config: SandboxConfig) -> Result<String> {
        let sandbox_id = uuid::Uuid::new_v4().to_string();
        
        // 缓存WASM字节码
        {
            let mut cache = self.wasm_bytes_cache.lock().map_err(|_| {
                NeuroFlowError::Sandbox("Failed to lock WASM cache".to_string())
            })?;
            cache.insert(sandbox_id.clone(), wasm_bytes.to_vec());
        }

        // 创建沙箱实例
        let instance = SandboxInstance {
            id: sandbox_id.clone(),
            agent_id: agent_id.to_string(),
            config,
        };

        // 存储沙箱实例
        {
            let mut sandboxes = self.sandboxes.lock().map_err(|_| {
                NeuroFlowError::Sandbox("Failed to lock sandboxes".to_string())
            })?;
            sandboxes.insert(sandbox_id.clone(), instance);
        }

        info!(sandbox_id = %sandbox_id, agent_id = %agent_id, "Sandbox spawned");
        Ok(sandbox_id)
    }

    pub fn get_sandbox(&self, sandbox_id: &str) -> Result<SandboxInstance> {
        let sandboxes = self.sandboxes.lock().map_err(|_| {
            NeuroFlowError::Sandbox("Failed to lock sandboxes".to_string())
        })?;
        
        sandboxes.get(sandbox_id).cloned().ok_or_else(|| {
            NeuroFlowError::AgentNotFound(format!("Sandbox {} not found", sandbox_id))
        })
    }

    pub fn execute_in_sandbox(&self, sandbox_id: &str, func_name: &str, args: &[i32]) -> Result<Vec<i32>> {
        // 获取WASM字节码
        let wasm_bytes = {
            let cache = self.wasm_bytes_cache.lock().map_err(|_| {
                NeuroFlowError::Sandbox("Failed to lock WASM cache".to_string())
            })?;
            cache.get(sandbox_id).cloned().ok_or_else(|| {
                NeuroFlowError::AgentNotFound(format!("WASM code for sandbox {} not found", sandbox_id))
            })?
        };

        // 获取沙箱配置
        let config = {
            let sandboxes = self.sandboxes.lock().map_err(|_| {
                NeuroFlowError::Sandbox("Failed to lock sandboxes".to_string())
            })?;
            let instance = sandboxes.get(sandbox_id).ok_or_else(|| {
                NeuroFlowError::AgentNotFound(format!("Sandbox {} not found", sandbox_id))
            })?;
            instance.config.clone()
        };

        // 创建并执行沙箱
        let mut sandbox = WasmSandbox::new(&wasm_bytes, config)
            .map_err(|e| NeuroFlowError::WasmExecution(e.to_string()))?;

        debug!(sandbox_id = %sandbox_id, func_name = %func_name, "Executing function in sandbox");

        let result = match func_name {
            "add" if args.len() == 2 => {
                vec![sandbox.call_add(args[0], args[1])
                    .map_err(|e| NeuroFlowError::WasmExecution(e.to_string()))?]
            }
            "multiply" if args.len() == 2 => {
                vec![sandbox.call_multiply(args[0], args[1])
                    .map_err(|e| NeuroFlowError::WasmExecution(e.to_string()))?]
            }
            _ => {
                return Err(NeuroFlowError::WasmExecution(
                    format!("Unsupported function: {} with {} args", func_name, args.len())
                ));
            }
        };

        Ok(result)
    }

    pub fn destroy_sandbox(&self, sandbox_id: &str) -> Result<()> {
        // 从缓存中移除WASM字节码
        {
            let mut cache = self.wasm_bytes_cache.lock().map_err(|_| {
                NeuroFlowError::Sandbox("Failed to lock WASM cache".to_string())
            })?;
            cache.remove(sandbox_id);
        }

        // 从沙箱列表中移除
        {
            let mut sandboxes = self.sandboxes.lock().map_err(|_| {
                NeuroFlowError::Sandbox("Failed to lock sandboxes".to_string())
            })?;
            sandboxes.remove(sandbox_id);
        }

        info!(sandbox_id = %sandbox_id, "Sandbox destroyed");
        Ok(())
    }

    pub fn list_sandboxes(&self) -> Result<Vec<SandboxInstance>> {
        let sandboxes = self.sandboxes.lock().map_err(|_| {
            NeuroFlowError::Sandbox("Failed to lock sandboxes".to_string())
        })?;
        
        Ok(sandboxes.values().cloned().collect())
    }

    pub fn get_sandbox_count(&self) -> Result<usize> {
        let sandboxes = self.sandboxes.lock().map_err(|_| {
            NeuroFlowError::Sandbox("Failed to lock sandboxes".to_string())
        })?;
        Ok(sandboxes.len())
    }
}

impl Default for SandboxManager {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sandbox_lifecycle() {
        let manager = SandboxManager::new();
        let wasm_bytes = std::fs::read("/Users/lianwenhua/indie/NeuroFlow/test/simple.wasm").unwrap();
        let config = SandboxConfig::default();

        // 创建沙箱
        let sandbox_id = manager.spawn_sandbox("test-agent", &wasm_bytes, config).unwrap();
        assert!(!sandbox_id.is_empty());

        // 获取沙箱信息
        let instance = manager.get_sandbox(&sandbox_id).unwrap();
        assert_eq!(instance.id, sandbox_id);
        assert_eq!(instance.agent_id, "test-agent");

        // 执行函数
        let result = manager.execute_in_sandbox(&sandbox_id, "add", &[1, 2]).unwrap();
        assert_eq!(result, vec![3]);

        let result = manager.execute_in_sandbox(&sandbox_id, "multiply", &[3, 4]).unwrap();
        assert_eq!(result, vec![12]);

        // 列出沙箱
        let sandboxes = manager.list_sandboxes().unwrap();
        assert_eq!(sandboxes.len(), 1);

        // 销毁沙箱
        manager.destroy_sandbox(&sandbox_id).unwrap();
        
        // 确认沙箱已销毁
        assert!(manager.get_sandbox(&sandbox_id).is_err());
    }
}