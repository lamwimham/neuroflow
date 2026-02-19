//! 配置管理模块
//! 提供应用配置的加载、验证等功能

mod simple;
mod enhanced;  // 保留向后兼容，新代码使用 simple 模块

// 导出简化后的配置 (推荐使用)
pub use simple::{
    Config, ConfigLoader,
    ServerConfig, SandboxConfig, ObservabilityConfig, SecurityConfig,
};

// 导出完整的配置 (仅供需要高级功能的用户)
pub use enhanced::{
    EnhancedConfig, ConfigManager,
};