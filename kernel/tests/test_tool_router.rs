//! Tool Router 集成测试

use kernel::{
    ToolRegistry,
    ToolDefinition,
    ToolParameter,
    ToolSource,
    ToolCall,
    tool_router::executor::{LocalExecutor, ToolExecutor},
};
use serde_json::json;

#[tokio::test]
async fn test_tool_registry_integration() {
    // 创建注册表
    let registry = ToolRegistry::new();
    
    // 创建工具定义
    let tool = ToolDefinition {
        id: "test-add".to_string(),
        name: "add".to_string(),
        description: "加法计算器".to_string(),
        source: ToolSource::Local,
        parameters: vec![
            ToolParameter {
                name: "a".to_string(),
                parameter_type: "number".to_string(),
                description: "第一个数".to_string(),
                required: true,
                default_value: None,
                enum_values: None,
            },
            ToolParameter {
                name: "b".to_string(),
                parameter_type: "number".to_string(),
                description: "第二个数".to_string(),
                required: true,
                default_value: None,
                enum_values: None,
            },
        ],
        return_type: Some("number".to_string()),
        schema: json!({}),
        metadata: None,
    };
    
    // 注册工具
    registry.register_tool(tool).await.unwrap();
    
    // 创建执行器
    let executor = std::sync::Arc::new(LocalExecutor::new());
    
    // 注册函数
    executor.register_tool(
        |args: serde_json::Value| async move {
            let a = args["a"].as_f64().unwrap_or(0.0);
            let b = args["b"].as_f64().unwrap_or(0.0);
            Ok(json!(a + b))
        },
        registry.get_tool("add").await.unwrap(),
    ).await.unwrap();
    
    // 注册执行器
    registry.register_executor(ToolSource::Local, executor.clone())
        .await.unwrap();
    
    // 执行工具调用
    let call = ToolCall::new(
        "add".to_string(),
        json!({"a": 100, "b": 200}),
    );
    
    let result = registry.execute(call).await.unwrap();
    
    assert!(result.success);
    assert_eq!(result.result.as_f64().unwrap(), 300.0);
}

#[tokio::test]
async fn test_multiple_tools() {
    let registry = ToolRegistry::new();
    let executor = std::sync::Arc::new(LocalExecutor::new());
    
    // 注册多个工具
    let tools = vec![
        ToolDefinition {
            id: "test-add".to_string(),
            name: "add".to_string(),
            description: "加法".to_string(),
            source: ToolSource::Local,
            parameters: vec![],
            return_type: Some("number".to_string()),
            schema: json!({}),
            metadata: None,
        },
        ToolDefinition {
            id: "test-multiply".to_string(),
            name: "multiply".to_string(),
            description: "乘法".to_string(),
            source: ToolSource::Local,
            parameters: vec![],
            return_type: Some("number".to_string()),
            schema: json!({}),
            metadata: None,
        },
    ];
    
    for tool in tools {
        registry.register_tool(tool).await.unwrap();
    }
    
    // 注册函数
    executor.register_tool(
        |args: serde_json::Value| async move {
            let a = args["a"].as_f64().unwrap_or(0.0);
            let b = args["b"].as_f64().unwrap_or(0.0);
            Ok(json!(a + b))
        },
        registry.get_tool("add").await.unwrap(),
    ).await.unwrap();
    
    executor.register_tool(
        |args: serde_json::Value| async move {
            let a = args["a"].as_f64().unwrap_or(0.0);
            let b = args["b"].as_f64().unwrap_or(0.0);
            Ok(json!(a * b))
        },
        registry.get_tool("multiply").await.unwrap(),
    ).await.unwrap();
    
    // 注册执行器
    registry.register_executor(ToolSource::Local, executor.clone())
        .await.unwrap();
    
    // 测试加法
    let add_call = ToolCall::new(
        "add".to_string(),
        json!({"a": 10, "b": 20}),
    );
    let add_result = registry.execute(add_call).await.unwrap();
    assert!(add_result.success);
    assert_eq!(add_result.result.as_f64().unwrap(), 30.0);
    
    // 测试乘法
    let multiply_call = ToolCall::new(
        "multiply".to_string(),
        json!({"a": 6, "b": 7}),
    );
    let multiply_result = registry.execute(multiply_call).await.unwrap();
    assert!(multiply_result.success);
    assert_eq!(multiply_result.result.as_f64().unwrap(), 42.0);
}

#[tokio::test]
async fn test_tool_schema_generation() {
    let registry = ToolRegistry::new();
    
    let tool = ToolDefinition {
        id: "test-greet".to_string(),
        name: "greet".to_string(),
        description: "问候某人".to_string(),
        source: ToolSource::Local,
        parameters: vec![
            ToolParameter {
                name: "name".to_string(),
                parameter_type: "string".to_string(),
                description: "人名".to_string(),
                required: true,
                default_value: Some(json!("World")),
                enum_values: None,
            },
        ],
        return_type: Some("string".to_string()),
        schema: json!({}),
        metadata: None,
    };
    
    registry.register_tool(tool).await.unwrap();
    
    // 获取 LLM Schema
    let schemas = registry.get_all_llm_schemas().await;
    
    assert_eq!(schemas.len(), 1);
    assert_eq!(schemas[0]["function"]["name"], "greet");
    
    let params = &schemas[0]["function"]["parameters"];
    assert_eq!(params["required"], json!(["name"]));
    assert!(params["properties"]["name"].is_object());
}
