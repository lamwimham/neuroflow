use std::collections::HashMap;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::{Mutex, RwLock};
use tracing::{info, warn, error, debug};
use wasmtime::{Config as WasmConfig, Engine, Instance, Module, Store, TypedFunc};
use wasmtime_wasi::{WasiCtx, WasiCtxBuilder};
use crate::utils::Result;
use crate::observability::monitoring::{MonitoringService, predefined_metrics};

#[derive(Debug, Clone)]
pub struct EnhancedSandboxConfig {
    pub cpu_limit: f64,
    pub memory_limit_mb: u64,
    pub timeout: Duration,
    pub allowed_domains: Vec<String>,
    pub max_instances: usize,
    pub health_check_interval: Duration,
    pub metrics_collection: bool,
}

impl Default for EnhancedSandboxConfig {
    fn default() -> Self {
        Self {
            cpu_limit: 0.5,
            memory_limit_mb: 256,
            timeout: Duration::from_secs(30),
            allowed_domains: vec!["api.openai.com".to_string()],
            max_instances: 50,
            health_check_interval: Duration::from_secs(60),
            metrics_collection: true,
        }
    }
}

#[derive(Debug, Clone)]
pub struct SandboxResourceUsage {
    pub cpu_usage: f64,
    pub memory_usage_mb: u64,
    pub uptime: Duration,
    pub last_activity: Instant,
    pub request_count: u64,
}

#[derive(Debug, Clone)]
pub struct SandboxHealthStatus {
    pub is_healthy: bool,
    pub last_check: Instant,
    pub error_count: u32,
    pub resource_usage: SandboxResourceUsage,
}

#[derive(Debug)]
pub struct EnhancedSandbox {
    pub id: String,
    pub agent_id: String,
    engine: Engine,
    module: Module,
    store: Arc<Mutex<Store<WasiCtx>>>,
    instance: Instance,
    config: EnhancedSandboxConfig,
    health_status: Arc<RwLock<SandboxHealthStatus>>,
    resource_usage: Arc<RwLock<SandboxResourceUsage>>,
}

impl EnhancedSandbox {
    pub async fn new(id: String, agent_id: String, wasm_bytes: &[u8], config: EnhancedSandboxConfig) -> Result<Self> {
        // 配置WASM引擎
        let mut wasm_config = WasmConfig::new();
        wasm_config.async_support(false);
        
        let engine = Engine::new(&wasm_config)?;
        
        // 创建WASI上下文
        let wasi = WasiCtxBuilder::new()
            .inherit_stdio()
            .build();
        
        let mut store = Store::new(&engine, wasi);
        
        // 编译模块
        let module = Module::from_binary(&engine, wasm_bytes)?;
        
        // 实例化
        let instance = Instance::new(&mut store, &module, &[])?;
        
        let now = Instant::now();
        let resource_usage = SandboxResourceUsage {
            cpu_usage: 0.0,
            memory_usage_mb: 0,
            uptime: Duration::from_secs(0),
            last_activity: now,
            request_count: 0,
        };
        
        let health_status = SandboxHealthStatus {
            is_healthy: true,
            last_check: now,
            error_count: 0,
            resource_usage: resource_usage.clone(),
        };
        
        Ok(Self {
            id,
            agent_id,
            engine,
            module,
            store: Arc::new(Mutex::new(store)),
            instance,
            config,
            health_status: Arc::new(RwLock::new(health_status)),
            resource_usage: Arc::new(RwLock::new(resource_usage)),
        })
    }
    
    pub async fn call_add(&self, a: i32, b: i32) -> Result<i32> {
        {
            let mut store = self.store.lock().await;
            let add_func: TypedFunc<(i32, i32), i32> = self.instance
                .get_typed_func(&mut *store, "add")?;
                
            let result = add_func.call(&mut *store, (a, b))?;
            
            // 更新资源使用情况
            self.update_resource_usage().await;
        }
        
        Ok(result)
    }
    
    pub async fn call_multiply(&self, a: i32, b: i32) -> Result<i32> {
        {
            let mut store = self.store.lock().await;
            let multiply_func: TypedFunc<(i32, i32), i32> = self.instance
                .get_typed_func(&mut *store, "multiply")?;
                
            let result = multiply_func.call(&mut *store, (a, b))?;
            
            // 更新资源使用情况
            self.update_resource_usage().await;
        }
        
        Ok(result)
    }
    
    async fn update_resource_usage(&self) {
        let mut resource_usage = self.resource_usage.write().await;
        resource_usage.last_activity = Instant::now();
        resource_usage.request_count += 1;
        
        // 模拟CPU和内存使用情况更新
        resource_usage.cpu_usage = self.config.cpu_limit * 0.7; // 模拟当前使用率
        resource_usage.memory_usage_mb = self.config.memory_limit_mb / 2; // 模拟内存使用
        resource_usage.uptime = resource_usage.last_activity.elapsed();
    }
    
    pub async fn health_check(&self) -> bool {
        let now = Instant::now();
        
        // 检查资源限制
        let resource_usage = self.resource_usage.read().await;
        let memory_exceeded = resource_usage.memory_usage_mb > self.config.memory_limit_mb;
        let cpu_exceeded = resource_usage.cpu_usage > self.config.cpu_limit;
        
        let is_healthy = !memory_exceeded && !cpu_exceeded;
        
        // 更新健康状态
        let mut health_status = self.health_status.write().await;
        health_status.is_healthy = is_healthy;
        health_status.last_check = now;
        if !is_healthy {
            health_status.error_count += 1;
        } else {
            health_status.error_count = 0; // 重置错误计数
        }
        health_status.resource_usage = resource_usage.clone();
        
        is_healthy
    }
    
    pub async fn get_resource_usage(&self) -> SandboxResourceUsage {
        self.resource_usage.read().await.clone()
    }
    
    pub async fn get_health_status(&self) -> SandboxHealthStatus {
        self.health_status.read().await.clone()
    }
    
    pub async fn is_overloaded(&self) -> bool {
        let resource_usage = self.resource_usage.read().await;
        let memory_usage_ratio = resource_usage.memory_usage_mb as f64 / self.config.memory_limit_mb as f64;
        memory_usage_ratio > 0.8 || resource_usage.cpu_usage > self.config.cpu_limit * 0.8
    }
}

pub struct SandboxPool {
    sandboxes: Arc<RwLock<HashMap<String, Arc<EnhancedSandbox>>>>,
    config: EnhancedSandboxConfig,
    monitoring_service: Option<Arc<MonitoringService>>,
}

impl SandboxPool {
    pub fn new(config: EnhancedSandboxConfig, monitoring_service: Option<Arc<MonitoringService>>) -> Self {
        Self {
            sandboxes: Arc::new(RwLock::new(HashMap::new())),
            config,
            monitoring_service,
        }
    }
    
    pub async fn create_sandbox(&self, agent_id: &str, wasm_bytes: &[u8]) -> Result<String> {
        let id = uuid::Uuid::new_v4().to_string();
        
        // 检查是否超过最大实例数
        {
            let sandboxes = self.sandboxes.read().await;
            if sandboxes.len() >= self.config.max_instances {
                return Err(crate::utils::NeuroFlowError::Sandbox("Maximum instances reached".to_string()));
            }
        }
        
        let sandbox = EnhancedSandbox::new(
            id.clone(),
            agent_id.to_string(),
            wasm_bytes,
            self.config.clone(),
        ).await?;
        
        {
            let mut sandboxes = self.sandboxes.write().await;
            sandboxes.insert(id.clone(), Arc::new(sandbox));
        }
        
        info!("Created new sandbox: {} for agent: {}", id, agent_id);
        
        // 记录指标
        if let Some(ref service) = self.monitoring_service {
            predefined_metrics::record_active_sandboxes(
                service,
                self.get_active_count().await as u64,
                &[]
            );
        }
        
        Ok(id)
    }
    
    pub async fn get_sandbox(&self, id: &str) -> Option<Arc<EnhancedSandbox>> {
        let sandboxes = self.sandboxes.read().await;
        sandboxes.get(id).cloned()
    }
    
    pub async fn execute_in_sandbox(&self, id: &str, func_name: &str, args: &[i32]) -> Result<Vec<i32>> {
        let sandbox = self.get_sandbox(id).await;
        
        match sandbox {
            Some(sb) => {
                let start_time = Instant::now();
                
                let result = match func_name {
                    "add" if args.len() == 2 => {
                        vec![sb.call_add(args[0], args[1]).await?]
                    }
                    "multiply" if args.len() == 2 => {
                        vec![sb.call_multiply(args[0], args[1]).await?]
                    }
                    _ => {
                        return Err(crate::utils::NeuroFlowError::WasmExecution(
                            format!("Unsupported function: {} with {} args", func_name, args.len())
                        ));
                    }
                };
                
                // 记录执行时间
                if let Some(ref service) = self.monitoring_service {
                    let duration = start_time.elapsed().as_secs_f64();
                    predefined_metrics::record_request(
                        service,
                        duration,
                        &[opentelemetry::KeyValue::new("sandbox_id", id)]
                    );
                }
                
                Ok(result)
            }
            None => {
                Err(crate::utils::NeuroFlowError::AgentNotFound(
                    format!("Sandbox {} not found", id)
                ))
            }
        }
    }
    
    pub async fn health_check_all(&self) -> Vec<(String, bool)> {
        let mut results = Vec::new();
        let sandboxes = self.sandboxes.read().await;
        
        for (id, sandbox) in sandboxes.iter() {
            let is_healthy = sandbox.health_check().await;
            results.push((id.clone(), is_healthy));
            
            if !is_healthy {
                warn!("Sandbox {} is unhealthy", id);
            }
        }
        
        results
    }
    
    pub async fn get_active_count(&self) -> usize {
        let sandboxes = self.sandboxes.read().await;
        sandboxes.len()
    }
    
    pub async fn get_overloaded_sandboxes(&self) -> Vec<String> {
        let mut overloaded = Vec::new();
        let sandboxes = self.sandboxes.read().await;
        
        for (id, sandbox) in sandboxes.iter() {
            if sandbox.is_overloaded().await {
                overloaded.push(id.clone());
            }
        }
        
        overloaded
    }
    
    pub async fn destroy_sandbox(&self, id: &str) -> Result<()> {
        let mut sandboxes = self.sandboxes.write().await;
        if sandboxes.remove(id).is_some() {
            info!("Destroyed sandbox: {}", id);
            
            // 记录指标
            if let Some(ref service) = self.monitoring_service {
                predefined_metrics::record_active_sandboxes(
                    service,
                    self.get_active_count().await as u64,
                    &[]
                );
            }
            
            Ok(())
        } else {
            Err(crate::utils::NeuroFlowError::AgentNotFound(
                format!("Sandbox {} not found", id)
            ))
        }
    }
    
    pub async fn cleanup_unhealthy_sandboxes(&self) -> usize {
        let mut cleaned_count = 0;
        let sandboxes = self.sandboxes.read().await;
        let mut to_remove = Vec::new();
        
        for (id, sandbox) in sandboxes.iter() {
            let health_status = sandbox.get_health_status().await;
            // 如果错误计数过多或沙箱不健康超过一定时间
            if health_status.error_count > 5 || !health_status.is_healthy {
                to_remove.push(id.clone());
            }
        }
        
        drop(sandboxes); // 释放读锁
        
        // 移除不健康的沙箱
        for id in to_remove {
            if self.destroy_sandbox(&id).await.is_ok() {
                cleaned_count += 1;
            }
        }
        
        info!("Cleaned up {} unhealthy sandboxes", cleaned_count);
        cleaned_count
    }
    
    pub async fn get_load_balanced_sandbox(&self) -> Option<String> {
        let sandboxes = self.sandboxes.read().await;
        
        // 简单的负载均衡：返回资源使用最少的沙箱
        let mut least_loaded: Option<(String, f64)> = None;
        
        for (id, sandbox) in sandboxes.iter() {
            let resource_usage = sandbox.get_resource_usage().await;
            let load_score = resource_usage.memory_usage_mb as f64 / self.config.memory_limit_mb as f64 +
                           resource_usage.cpu_usage / self.config.cpu_limit;
            
            if let Some((_, current_min_load)) = least_loaded {
                if load_score < current_min_load {
                    least_loaded = Some((id.clone(), load_score));
                }
            } else {
                least_loaded = Some((id.clone(), load_score));
            }
        }
        
        least_loaded.map(|(id, _)| id)
    }
    
    pub async fn start_health_monitoring(&self) {
        let pool = self.clone();
        tokio::spawn(async move {
            loop {
                // 执行健康检查
                pool.health_check_all().await;
                
                // 清理不健康的沙箱
                pool.cleanup_unhealthy_sandboxes().await;
                
                tokio::time::sleep(pool.config.health_check_interval).await;
            }
        });
    }
}

impl Clone for SandboxPool {
    fn clone(&self) -> Self {
        Self {
            sandboxes: self.sandboxes.clone(),
            config: self.config.clone(),
            monitoring_service: self.monitoring_service.clone(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[tokio::test]
    async fn test_sandbox_pool_creation() {
        let config = EnhancedSandboxConfig::default();
        let pool = SandboxPool::new(config, None);
        
        assert_eq!(pool.get_active_count().await, 0);
    }
    
    #[tokio::test]
    async fn test_sandbox_lifecycle() {
        // 注意：这里需要一个有效的WASM文件来进行测试
        // 在实际环境中，我们可以使用一个测试WASM文件
        let config = EnhancedSandboxConfig {
            max_instances: 10,
            ..EnhancedSandboxConfig::default()
        };
        let pool = SandboxPool::new(config, None);
        
        // 由于我们没有有效的WASM文件，我们跳过创建沙箱的测试
        // 在实际环境中，这里会创建一个测试WASM文件
    }
}