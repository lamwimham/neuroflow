//! NeuroFlow Rust Kernel - Performance Benchmarks
//! 
//! 性能基准测试
//! 
//! 运行:
//! cargo bench

use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use kernel::{
    ToolRegistry,
    ToolDefinition,
    ToolParameter,
    ToolSource,
    ToolCall,
    tool_router::executor::LocalExecutor,
};
use serde_json::json;
use std::sync::Arc;

/// 基准测试：工具注册
fn bench_tool_registry(c: &mut Criterion) {
    c.bench_function("tool_registry_create", |b| {
        b.iter(|| {
            let registry = ToolRegistry::new();
            black_box(registry);
        });
    });
    
    c.bench_function("tool_registry_register_tool", |b| {
        let registry = ToolRegistry::new();
        
        let tool = ToolDefinition {
            id: "test_tool".to_string(),
            name: "test_tool".to_string(),
            description: "Test tool".to_string(),
            source: ToolSource::Local,
            parameters: vec![
                ToolParameter {
                    name: "param".to_string(),
                    parameter_type: "string".to_string(),
                    description: "Test parameter".to_string(),
                    required: true,
                    default_value: None,
                    enum_values: None,
                },
            ],
            return_type: Some("string".to_string()),
            schema: json!({}),
            metadata: None,
        };
        
        b.to_async(tokio::runtime::Runtime::new().unwrap()).iter(|| async {
            registry.register_tool(tool.clone()).await.unwrap();
        });
    });
}

/// 基准测试：工具执行
fn bench_tool_execution(c: &mut Criterion) {
    c.bench_function("tool_execution_local", |b| {
        let registry = ToolRegistry::new();
        let executor = Arc::new(LocalExecutor::new());
        
        // 注册工具
        let tool = ToolDefinition {
            id: "add".to_string(),
            name: "add".to_string(),
            description: "Add two numbers".to_string(),
            source: ToolSource::Local,
            parameters: vec![
                ToolParameter {
                    name: "a".to_string(),
                    parameter_type: "number".to_string(),
                    description: "First number".to_string(),
                    required: true,
                    default_value: None,
                    enum_values: None,
                },
                ToolParameter {
                    name: "b".to_string(),
                    parameter_type: "number".to_string(),
                    description: "Second number".to_string(),
                    required: true,
                    default_value: None,
                    enum_values: None,
                },
            ],
            return_type: Some("number".to_string()),
            schema: json!({}),
            metadata: None,
        };
        
        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async {
            registry.register_tool(tool).await.unwrap();
            registry.register_executor(ToolSource::Local, executor.clone()).await.unwrap();
            
            executor.register_tool(
                |args: serde_json::Value| async move {
                    let a = args["a"].as_f64().unwrap_or(0.0);
                    let b = args["b"].as_f64().unwrap_or(0.0);
                    Ok(json!(a + b))
                },
                registry.get_tool("add").await.unwrap(),
            ).await.unwrap();
        });
        
        let call = ToolCall::new(
            "add".to_string(),
            json!({"a": 10, "b": 20}),
        );
        
        b.to_async(tokio::runtime::Runtime::new().unwrap()).iter(|| async {
            let result = registry.execute(call.clone()).await.unwrap();
            black_box(result);
        });
    });
}

/// 基准测试：工具 Schema 生成
fn bench_tool_schema_generation(c: &mut Criterion) {
    let registry = ToolRegistry::new();
    
    // 注册多个工具
    let rt = tokio::runtime::Runtime::new().unwrap();
    rt.block_on(async {
        for i in 0..10 {
            let tool = ToolDefinition {
                id: format!("tool_{}", i),
                name: format!("tool_{}", i),
                description: format!("Tool {}", i),
                source: ToolSource::Local,
                parameters: vec![],
                return_type: Some("object".to_string()),
                schema: json!({}),
                metadata: None,
            };
            registry.register_tool(tool).await.unwrap();
        }
    });
    
    c.bench_function("tool_schema_generation", |b| {
        b.to_async(tokio::runtime::Runtime::new().unwrap()).iter(|| async {
            let schemas = registry.get_all_llm_schemas().await;
            black_box(schemas);
        });
    });
}

/// 基准测试：不同工具数量下的性能
fn bench_tool_registry_scale(c: &mut Criterion) {
    let mut group = c.benchmark_group("tool_registry_scale");
    
    for size in [10, 100, 1000].iter() {
        group.bench_with_input(BenchmarkId::from_parameter(size), size, |b, &size| {
            let registry = ToolRegistry::new();
            
            // 注册工具
            let rt = tokio::runtime::Runtime::new().unwrap();
            rt.block_on(async {
                for i in 0..size {
                    let tool = ToolDefinition {
                        id: format!("tool_{}", i),
                        name: format!("tool_{}", i),
                        description: format!("Tool {}", i),
                        source: ToolSource::Local,
                        parameters: vec![],
                        return_type: Some("object".to_string()),
                        schema: json!({}),
                        metadata: None,
                    };
                    registry.register_tool(tool).await.unwrap();
                }
            });
            
            b.to_async(tokio::runtime::Runtime::new().unwrap()).iter(|| async {
                let tools = registry.list_tools().await;
                black_box(tools);
            });
        });
    }
    
    group.finish();
}

criterion_group!(
    benches,
    bench_tool_registry,
    bench_tool_execution,
    bench_tool_schema_generation,
    bench_tool_registry_scale,
);

criterion_main!(benches);
